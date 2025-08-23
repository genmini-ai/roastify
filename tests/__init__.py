"""
Roastify Test Suite

This package contains individual component tests for the Roastify system.
Each module tests a specific component in isolation.

Usage:
    # Test individual components
    python test_scraper.py --url https://linkedin.com/in/someone
    python test_gemini.py --verbose
    python test_analyzer.py --test openai
    
    # Run all tests with pytest
    pytest tests/ -v
    
    # Run specific test file
    pytest tests/test_scraper.py -v

Components:
    - test_scraper: Profile scraping and PDF generation
    - test_gemini: Gemini analyzer functionality  
    - test_analyzer: All profile analyzers
    - test_generator: Lyrics generation
    - test_audio: Audio synthesis pipeline
    - test_video: Video generation
    - test_integration: End-to-end tests
"""

import sys
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

__version__ = "1.0.0"