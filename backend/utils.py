import logging
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any
import asyncio
from datetime import datetime
import functools

logger = logging.getLogger(__name__)


def generate_job_id() -> str:
    """Generate unique job ID"""
    return str(uuid.uuid4())


def create_temp_file(suffix: str = "") -> Path:
    """Create temporary file"""
    temp_dir = Path(tempfile.gettempdir()) / "roastify"
    temp_dir.mkdir(exist_ok=True)
    
    temp_file = temp_dir / f"{uuid.uuid4().hex}{suffix}"
    return temp_file


async def run_with_timeout(coro, timeout: float):
    """Run coroutine with timeout"""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.error(f"Operation timed out after {timeout} seconds")
        raise


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system usage"""
    import re
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    return sanitized[:100]


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{int(minutes)}m {secs:.1f}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{int(hours)}h {int(minutes)}m"


def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    from urllib.parse import urlparse
    try:
        return urlparse(url).netloc.lower()
    except:
        return ""


def is_valid_url(url: str) -> bool:
    """Check if URL is valid"""
    from urllib.parse import urlparse
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


class ProgressTracker:
    """Track progress of long-running operations"""
    
    def __init__(self, total_steps: int):
        self.total_steps = total_steps
        self.current_step = 0
        self.step_descriptions = {}
        self.start_time = datetime.now()
        
    def add_step(self, step_number: int, description: str):
        """Add step description"""
        self.step_descriptions[step_number] = description
    
    def complete_step(self, step_number: int):
        """Mark step as completed"""
        self.current_step = max(self.current_step, step_number)
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current progress"""
        progress_percent = (self.current_step / self.total_steps) * 100
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        if self.current_step > 0:
            estimated_total = elapsed * (self.total_steps / self.current_step)
            remaining = max(0, estimated_total - elapsed)
        else:
            remaining = None
        
        current_description = self.step_descriptions.get(
            self.current_step + 1, 
            "Processing..."
        )
        
        return {
            "progress": progress_percent,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "current_description": current_description,
            "elapsed_seconds": elapsed,
            "estimated_remaining": remaining
        }


def setup_error_handlers():
    """Setup global error handlers"""
    import sys
    import traceback
    
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    sys.excepthook = handle_exception


class FileManager:
    """Manage temporary files and cleanup"""
    
    def __init__(self):
        self.temp_files = set()
        self.temp_dir = Path(tempfile.gettempdir()) / "roastify"
        self.temp_dir.mkdir(exist_ok=True)
    
    def create_temp_file(self, suffix: str = "") -> Path:
        """Create temporary file"""
        temp_file = self.temp_dir / f"{uuid.uuid4().hex}{suffix}"
        self.temp_files.add(temp_file)
        return temp_file
    
    def cleanup(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to cleanup {temp_file}: {e}")
        
        self.temp_files.clear()
    
    def __del__(self):
        self.cleanup()


# Global file manager
file_manager = FileManager()


def validate_request_data(data: Dict[str, Any], required_fields: list) -> list:
    """Validate request data"""
    missing_fields = []
    
    for field in required_fields:
        if field not in data or not data[field]:
            missing_fields.append(field)
    
    return missing_fields


def rate_limit_key(identifier: str, window: str) -> str:
    """Create rate limit key"""
    return f"rate_limit:{identifier}:{window}"


async def check_rate_limit(
    cache_manager, 
    identifier: str, 
    limit: int, 
    window_seconds: int
) -> bool:
    """Check if request is within rate limit"""
    key = rate_limit_key(identifier, str(window_seconds))
    
    try:
        current_count = await cache_manager.get(key) or 0
        
        if current_count >= limit:
            return False
        
        # Increment counter
        await cache_manager.set(key, current_count + 1, expire_seconds=window_seconds)
        return True
        
    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        return True  # Allow on error


def format_error_response(error: Exception, job_id: str = None) -> Dict[str, Any]:
    """Format error response"""
    return {
        "error": True,
        "message": str(error),
        "type": type(error).__name__,
        "job_id": job_id,
        "timestamp": datetime.now().isoformat()
    }


class MetricsCollector:
    """Collect performance metrics"""
    
    def __init__(self):
        self.metrics = {}
    
    def record_duration(self, operation: str, duration: float):
        """Record operation duration"""
        if operation not in self.metrics:
            self.metrics[operation] = []
        
        self.metrics[operation].append(duration)
    
    def get_stats(self, operation: str) -> Dict[str, float]:
        """Get statistics for operation"""
        if operation not in self.metrics:
            return {}
        
        durations = self.metrics[operation]
        
        return {
            "count": len(durations),
            "avg": sum(durations) / len(durations),
            "min": min(durations),
            "max": max(durations),
            "total": sum(durations)
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get all statistics"""
        return {op: self.get_stats(op) for op in self.metrics.keys()}


# Global metrics collector
metrics = MetricsCollector()


def log_performance(operation: str):
    """Decorator to log performance"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = datetime.now()
            try:
                result = await func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                metrics.record_duration(operation, duration)
                logger.info(f"{operation} completed in {duration:.2f}s")
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(f"{operation} failed after {duration:.2f}s: {e}")
                raise
        return wrapper
    return decorator