import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn

from models import (
    RoastRequest, RoastResponse, JobStatus, GenerationResult,
    ProfileData, AnalysisResult, LyricsData, HealthCheck
)
from config import settings, validate_api_keys, setup_logging
from scraper import ProfileScraper, create_manual_profile
from analyzer import LLMAnalyzer
from generator import LyricsGenerator
from audio import AudioPipeline, create_audio_config
from video import VideoGenerator, VideoConfig
from cache import cache
from utils import (
    generate_job_id, ProgressTracker, log_performance, 
    metrics, format_error_response, check_rate_limit
)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Job storage (in production, use Redis/database)
active_jobs: Dict[str, JobStatus] = {}
job_results: Dict[str, GenerationResult] = {}
websocket_connections: Dict[str, WebSocket] = {}

# Initialize components
scraper = ProfileScraper()
analyzer = LLMAnalyzer()
lyrics_generator = LyricsGenerator()
audio_pipeline = AudioPipeline()
video_generator = VideoGenerator()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    logger.info("Starting Roastify backend...")
    
    # Validate API keys
    try:
        validate_api_keys()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        # In development, continue without some keys
        if not settings.debug:
            raise
    
    # Initialize audio pipeline (create sample beats)
    try:
        audio_pipeline.create_sample_beats()
    except Exception as e:
        logger.warning(f"Could not create sample beats: {e}")
    
    logger.info("Roastify backend started successfully!")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Roastify backend...")
    await scraper.cleanup()
    logger.info("Shutdown complete")


app = FastAPI(
    title="Roastify API",
    description="Transform social media profiles into personalized rap diss tracks",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    return response


@app.get("/", response_model=HealthCheck)
async def root():
    """Health check endpoint"""
    return HealthCheck(
        status="healthy",
        services={
            "scraper": "available",
            "analyzer": "available" if analyzer.openai_client else "limited",
            "generator": "available" if lyrics_generator.openai_client else "limited",
            "audio": "available" if audio_pipeline.openai_client else "unavailable",
            "video": "available",
            "cache": "available" if cache.enabled else "disabled"
        }
    )


@app.post("/api/roast", response_model=RoastResponse)
@log_performance("create_roast")
async def create_roast(
    request: RoastRequest, 
    background_tasks: BackgroundTasks
):
    """Create a new roast generation job"""
    
    # Rate limiting (10 requests per hour per IP in production)
    # For demo, skip rate limiting
    
    # Validate input
    if not request.url and not request.manual_text:
        raise HTTPException(
            status_code=400,
            detail="Either 'url' or 'manual_text' must be provided"
        )
    
    # Generate job ID
    job_id = generate_job_id()
    
    # Initialize job status
    job_status = JobStatus(
        job_id=job_id,
        status="pending",
        current_step="Initializing..."
    )
    
    active_jobs[job_id] = job_status
    
    # Start background processing
    background_tasks.add_task(
        process_roast_generation,
        job_id,
        request
    )
    
    return RoastResponse(
        job_id=job_id,
        status="processing",
        message="Your roast is being generated! Check status for updates."
    )


@app.get("/api/status/{job_id}")
async def get_job_status(job_id: str):
    """Get job status"""
    
    # Check active jobs first
    if job_id in active_jobs:
        status = active_jobs[job_id]
        return {
            "job_id": job_id,
            "status": status.status,
            "progress": status.progress,
            "current_step": status.current_step,
            "steps_completed": status.steps_completed,
            "error_message": status.error_message,
            "created_at": status.created_at,
            "estimated_completion": status.estimated_completion
        }
    
    # Check cache
    cached_status = await cache.get_job_status(job_id)
    if cached_status:
        return cached_status
    
    raise HTTPException(status_code=404, detail="Job not found")


@app.get("/api/result/{job_id}")
async def get_result(job_id: str):
    """Get generation result"""
    
    # Check completed results
    if job_id in job_results:
        result = job_results[job_id]
        return {
            "job_id": job_id,
            "status": "completed",
            "result": result.model_dump()
        }
    
    # Check cache
    cached_result = await cache.get_result(job_id)
    if cached_result:
        return {
            "job_id": job_id,
            "status": "completed", 
            "result": cached_result
        }
    
    # Check if still processing
    if job_id in active_jobs:
        status = active_jobs[job_id]
        if status.status == "failed":
            raise HTTPException(
                status_code=500,
                detail=status.error_message or "Generation failed"
            )
        else:
            raise HTTPException(
                status_code=202,
                detail="Job still processing"
            )
    
    raise HTTPException(status_code=404, detail="Job not found")


@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket for real-time progress updates"""
    await websocket.accept()
    websocket_connections[job_id] = websocket
    
    try:
        while True:
            # Send current status
            if job_id in active_jobs:
                status = active_jobs[job_id]
                await websocket.send_json({
                    "type": "status_update",
                    "job_id": job_id,
                    "status": status.status,
                    "progress": status.progress,
                    "current_step": status.current_step
                })
                
                # If completed or failed, send final message
                if status.status in ["completed", "failed"]:
                    break
            
            await asyncio.sleep(1)  # Update every second
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for job {job_id}")
    finally:
        websocket_connections.pop(job_id, None)


@app.get("/api/metrics")
async def get_metrics():
    """Get performance metrics (admin endpoint)"""
    return {
        "active_jobs": len(active_jobs),
        "completed_jobs": len(job_results),
        "performance": metrics.get_all_stats()
    }


async def process_roast_generation(job_id: str, request: RoastRequest):
    """Background task to generate roast"""
    
    progress = ProgressTracker(6)  # 6 main steps
    progress.add_step(1, "Scraping profile data...")
    progress.add_step(2, "Analyzing personality...")
    progress.add_step(3, "Generating rap lyrics...")
    progress.add_step(4, "Creating audio...")
    progress.add_step(5, "Generating video...")
    progress.add_step(6, "Finalizing results...")
    
    job_status = active_jobs[job_id]
    
    try:
        start_time = datetime.now()
        
        # Step 1: Get profile data
        await update_job_progress(job_id, progress, 1, "Scraping profile data...")
        
        search_result = None
        if request.url:
            profile = await scraper.scrape_profile(request.url)
            # Also get search result for dynamic image generation
            search_result = await scraper.scrape_profile_simple(request.url)
        else:
            profile = create_manual_profile(request.manual_text, "Manual User")
        
        # Step 2: Analyze profile
        await update_job_progress(job_id, progress, 2, "Analyzing personality...")
        
        analysis = await analyzer.analyze_profile(profile)
        
        # Step 3: Generate lyrics
        await update_job_progress(job_id, progress, 3, "Writing rap lyrics...")
        
        lyrics = await lyrics_generator.generate_lyrics(
            profile, analysis, request.style
        )
        
        # Step 4: Generate audio
        await update_job_progress(job_id, progress, 4, "Creating audio track...")
        
        audio_config = await create_audio_config(
            voice_model=request.voice_preference,
            beat_type=request.beat_type,
            style=request.style
        )
        
        audio_bytes = await audio_pipeline.generate_audio(lyrics, audio_config)
        
        # Step 5: Generate video (if requested)
        video_bytes = None
        if request.include_video:
            await update_job_progress(job_id, progress, 5, "Creating music video...")
            
            video_config = VideoConfig()
            video_bytes = await video_generator.generate_video(
                audio_bytes, lyrics, profile, video_config, search_result
            )
        
        # Step 6: Finalize
        await update_job_progress(job_id, progress, 6, "Finalizing results...")
        
        # Create result
        generation_time = (datetime.now() - start_time).total_seconds()
        
        result = GenerationResult(
            job_id=job_id,
            profile=profile,
            analysis=analysis,
            lyrics=lyrics,
            audio_url=f"/api/download/audio/{job_id}",  # In production, use cloud storage
            video_url=f"/api/download/video/{job_id}" if video_bytes else None,
            audio_duration=30.0,  # Placeholder
            generation_time=generation_time
        )
        
        # Store result
        job_results[job_id] = result
        
        # Cache result
        await cache.cache_result(job_id, result.model_dump())
        
        # Update job status
        job_status.status = "completed"
        job_status.progress = 1.0
        job_status.current_step = "Complete!"
        job_status.completed_at = datetime.now()
        
        # Store audio/video files (in production, upload to cloud storage)
        # For now, store in memory or temp files
        
        logger.info(f"Roast generation completed for job {job_id} in {generation_time:.2f}s")
        
    except Exception as e:
        logger.error(f"Roast generation failed for job {job_id}: {e}")
        
        job_status.status = "failed"
        job_status.error_message = str(e)
        
        # Send error via WebSocket
        if job_id in websocket_connections:
            try:
                await websocket_connections[job_id].send_json({
                    "type": "error",
                    "job_id": job_id,
                    "message": str(e)
                })
            except:
                pass


async def update_job_progress(
    job_id: str, 
    progress: ProgressTracker, 
    step: int, 
    message: str
):
    """Update job progress and notify via WebSocket"""
    
    progress.complete_step(step)
    progress_data = progress.get_progress()
    
    job_status = active_jobs[job_id]
    job_status.progress = progress_data["progress"] / 100
    job_status.current_step = message
    job_status.steps_completed = progress_data["current_step"]
    
    # Update cache
    await cache.update_job_status(job_id, {
        "status": job_status.status,
        "progress": job_status.progress,
        "current_step": job_status.current_step,
        "steps_completed": job_status.steps_completed
    })
    
    # Send WebSocket update
    if job_id in websocket_connections:
        try:
            await websocket_connections[job_id].send_json({
                "type": "progress_update",
                "job_id": job_id,
                "progress": job_status.progress,
                "current_step": job_status.current_step,
                "estimated_remaining": progress_data.get("estimated_remaining")
            })
        except Exception as e:
            logger.warning(f"Failed to send WebSocket update: {e}")


# Download endpoints (in production, serve from cloud storage)
@app.get("/api/download/audio/{job_id}")
async def download_audio(job_id: str):
    """Download audio file"""
    # In production, redirect to cloud storage URL
    # For now, return placeholder
    raise HTTPException(status_code=501, detail="Download not implemented yet")


@app.get("/api/download/video/{job_id}")  
async def download_video(job_id: str):
    """Download video file"""
    # In production, redirect to cloud storage URL
    # For now, return placeholder
    raise HTTPException(status_code=501, detail="Download not implemented yet")


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )