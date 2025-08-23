"""
Test-specific configuration for Roastify
"""
import os
from pathlib import Path
from datetime import datetime
import re


class TestConfig:
    """Configuration for test runs"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_output_root = self.project_root / "test_output"
        self.backend_dir = Path(__file__).parent
        
        # Ensure test output directory exists
        self.test_output_root.mkdir(exist_ok=True)
    
    def create_run_folder(self, platform: str, name: str) -> Path:
        """Create a new run folder with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sanitized_name = self.sanitize_name(name)
        
        folder_name = f"run_{timestamp}_{platform}_{sanitized_name}"
        run_folder = self.test_output_root / folder_name
        
        run_folder.mkdir(exist_ok=True)
        return run_folder
    
    @staticmethod
    def sanitize_name(name: str) -> str:
        """Sanitize name for folder usage"""
        # Remove special characters and replace with underscore
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
        # Remove multiple underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Limit length
        return sanitized[:20].strip('_')
    
    @staticmethod
    def extract_name_from_url(url: str) -> str:
        """Extract name from social media URL"""
        # LinkedIn: extract username from /in/username
        if 'linkedin.com' in url:
            match = re.search(r'/in/([^/?]+)', url)
            if match:
                return match.group(1)
        
        # Twitter: extract username from twitter.com/username or x.com/username
        if 'twitter.com' in url or 'x.com' in url:
            match = re.search(r'(?:twitter\.com|x\.com)/([^/?]+)', url)
            if match:
                return match.group(1)
        
        # Fallback: use domain
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            return parsed.netloc.replace('.', '_')
        except:
            return "unknown"
    
    def get_platform_from_url(self, url: str) -> str:
        """Determine platform from URL"""
        url_lower = url.lower()
        if 'linkedin.com' in url_lower:
            return 'linkedin'
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'twitter'
        else:
            return 'other'


# Test data samples for fallback testing
SAMPLE_PROFILES = {
    'linkedin': {
        'name': 'John Business',
        'url': 'https://linkedin.com/in/johnbusiness',
        'text': '''
        John Business - Senior Vice President of Strategic Innovation
        🚀 Passionate about leveraging synergies to drive scalable solutions
        💡 Thought leader in digital transformation and disruptive technologies
        🌟 10+ years of experience optimizing cross-functional team dynamics
        
        Experience:
        - VP Strategic Innovation at TechCorp (2019-present)
        - Director of Business Development at StartupInc (2016-2019)  
        - Senior Consultant at ConsultingFirm (2014-2016)
        
        Education:
        - MBA in Strategic Leadership, Business University
        - BS Computer Science, Tech College
        
        Recent Posts:
        "Excited to announce our paradigm-shifting solution that will revolutionize the industry!"
        "Grateful for the opportunity to spearhead this mission-critical initiative"
        "Thrilled to be leveraging AI to optimize our customer-centric approach"
        '''
    },
    'twitter': {
        'name': 'Tech Guru',
        'url': 'https://twitter.com/techguru',
        'text': '''
        Tech Guru (@techguru)
        🧠 AI Researcher | 🚀 Startup Founder | 💭 Deep Thoughts
        Building the future one algorithm at a time
        
        Recent Tweets:
        "Just disrupted another industry with our revolutionary ML model 🤖"
        "Hot take: Most people don't understand exponential growth"
        "Building in stealth mode. Big announcement coming soon... 👀"
        "Debugging is just having a conversation with your past self"
        "The metaverse will change everything. Mark my words."
        '''
    }
}


# Test configurations for different scenarios
TEST_SCENARIOS = {
    'quick': {
        'style': 'playful',
        'beat_type': 'trap',
        'voice_preference': 'echo',
        'include_video': False,  # Audio only for speed
        'description': 'Quick test - audio only'
    },
    'full': {
        'style': 'playful',
        'beat_type': 'trap',
        'voice_preference': 'echo',
        'include_video': True,
        'description': 'Full test - audio and video'
    },
    'aggressive': {
        'style': 'aggressive',
        'beat_type': 'boom_bap',
        'voice_preference': 'echo',
        'include_video': True,
        'description': 'Aggressive style with boom-bap beat'
    },
    'witty': {
        'style': 'witty',
        'beat_type': 'lofi',
        'voice_preference': 'alloy',
        'include_video': True,
        'description': 'Witty style with lofi beat'
    }
}


def check_api_keys():
    """Check which API keys are available"""
    keys_status = {}
    
    required_keys = [
        'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY',
        'BROWSERLESS_API_KEY',
        'REPLICATE_API_KEY'
    ]
    
    for key in required_keys:
        value = os.getenv(key)
        keys_status[key] = {
            'available': bool(value),
            'value': value[:10] + '...' if value else None
        }
    
    return keys_status


def get_test_mode():
    """Determine test mode based on available API keys"""
    keys = check_api_keys()
    
    if keys['OPENAI_API_KEY']['available']:
        return 'full'  # Can do everything
    elif keys['ANTHROPIC_API_KEY']['available']:
        return 'partial'  # Can do analysis but not TTS
    else:
        return 'fallback'  # Use built-in fallbacks only