from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
import uuid


class ProfileData(BaseModel):
    """Scraped social media profile data"""
    url: str
    platform: Literal["linkedin", "twitter", "manual", "generic"] = "manual"
    name: str
    bio: Optional[str] = None
    posts: List[str] = []
    work_history: List[str] = []
    education: List[str] = []
    skills: List[str] = []
    achievements: List[str] = []
    raw_text: Optional[str] = None  # Fallback for manual input
    scraped_at: datetime = Field(default_factory=datetime.now)


class AnalysisResult(BaseModel):
    """LLM analysis of profile data"""
    personality_traits: List[str]
    roast_angles: List[str]
    buzzwords: List[str]
    key_achievements: List[str]
    insecurity_points: List[str]  # Things to poke fun at
    humor_style: Literal["aggressive", "playful", "witty"] = "playful"
    confidence_score: float = Field(ge=0.0, le=1.0)  # How roastable they are
    analysis_summary: str


class LyricsData(BaseModel):
    """Generated rap lyrics with structure"""
    intro: str
    verses: List[str]  # Usually 2-3 verses
    hook: str  # Chorus/hook
    outro: str
    rhyme_scheme: str = "AABB"
    bpm: int = 90
    style: Literal["aggressive", "playful", "witty"] = "playful"
    wordplay_rating: float = Field(ge=0.0, le=1.0)
    full_lyrics: str  # Combined formatted lyrics
    timing_marks: List[Dict[str, Any]] = []  # For audio sync


class AudioConfig(BaseModel):
    """Audio generation configuration"""
    voice_model: str = "echo"  # OpenAI TTS voice
    speed: float = 1.1
    pitch_shift: float = 0.0
    autotune_strength: float = 0.7
    reverb_level: float = 0.3
    compression_ratio: float = 4.0
    beat_type: Literal["trap", "boom_bap", "lofi"] = "trap"
    target_bpm: int = 90


class VideoConfig(BaseModel):
    """Video generation configuration"""
    resolution: str = "1280x720"
    fps: int = 30
    duration: Optional[float] = None  # Auto-detected from audio
    lyric_style: str = "modern"
    background_style: str = "dynamic"
    include_profile_image: bool = True
    effects_intensity: float = 0.7


class RoastRequest(BaseModel):
    """Main API request for roast generation"""
    url: Optional[str] = None
    manual_text: Optional[str] = None
    style: Literal["aggressive", "playful", "witty"] = "playful"
    beat_type: Literal["trap", "boom_bap", "lofi"] = "trap"
    voice_preference: str = "echo"
    include_video: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://linkedin.com/in/username",
                "style": "playful",
                "beat_type": "trap",
                "voice_preference": "echo",
                "include_video": True
            }
        }


class JobStatus(BaseModel):
    """Job processing status"""
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: Literal["pending", "processing", "completed", "failed"] = "pending"
    progress: float = Field(ge=0.0, le=1.0, default=0.0)
    current_step: str = ""
    steps_completed: List[str] = []
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None


class GenerationResult(BaseModel):
    """Complete generation result"""
    job_id: str
    profile: ProfileData
    analysis: Optional[AnalysisResult] = None
    lyrics: LyricsData
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    audio_duration: Optional[float] = None
    generation_time: float = 0.0
    metadata: Dict[str, Any] = {}


class RoastResponse(BaseModel):
    """API response for roast generation"""
    job_id: str
    status: str
    message: str = ""
    result: Optional[GenerationResult] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "abc123-def456",
                "status": "processing",
                "message": "Your roast is being generated..."
            }
        }


class TransformRequest(BaseModel):
    """Request for content transformation"""
    roast_id: str
    target_format: Literal["linkedin", "powerpoint", "essay", "tweet"] = "linkedin"
    tone: Literal["professional", "casual", "academic"] = "professional"


class TransformResult(BaseModel):
    """Transformed content result"""
    original_roast_id: str
    target_format: str
    transformed_content: str
    metadata: Dict[str, Any] = {}


class CacheEntry(BaseModel):
    """Redis cache entry"""
    key: str
    value: Any
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)


class HealthCheck(BaseModel):
    """Health check response"""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
    services: Dict[str, str] = {}
    version: str = "1.0.0"