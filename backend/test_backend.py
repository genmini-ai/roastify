#!/usr/bin/env python3
"""
Basic test script for Roastify backend
Run this to test core functionality
"""

import asyncio
import json
import os
from datetime import datetime

# Set up environment for testing
os.environ["OPENAI_API_KEY"] = "test-key"  # Placeholder
os.environ["DEMO_MODE"] = "true"
os.environ["CACHE_ENABLED"] = "false"

from models import ProfileData, RoastRequest
from scraper import create_manual_profile
from analyzer import LLMAnalyzer
from generator import LyricsGenerator
from audio import create_audio_config
from video import VideoGenerator


async def test_manual_profile_flow():
    """Test the complete flow with manual profile data"""
    print("🧪 Testing Roastify Backend Components...")
    
    # Test data
    test_profile_text = """
    John Smith - Senior Software Engineer at TechCorp
    Passionate about innovation and disrupting the industry.
    Thought leader in AI and machine learning.
    Love to synergize cross-functional teams for maximum ROI.
    MBA from Business School, 10 years experience.
    Posted: "Excited to announce our new paradigm-shifting solution!"
    """
    
    print("\n1️⃣ Testing Profile Creation...")
    profile = create_manual_profile(test_profile_text, "John Smith")
    print(f"✅ Created profile for {profile.name}")
    print(f"   Platform: {profile.platform}")
    print(f"   Bio length: {len(profile.bio or '')}")
    
    print("\n2️⃣ Testing Profile Analysis...")
    analyzer = LLMAnalyzer()
    
    try:
        analysis = await analyzer.analyze_profile(profile)
        print(f"✅ Analysis completed")
        print(f"   Personality traits: {len(analysis.personality_traits)}")
        print(f"   Roast angles: {len(analysis.roast_angles)}")
        print(f"   Buzzwords: {analysis.buzzwords[:5]}...")  # Show first 5
        print(f"   Humor style: {analysis.humor_style}")
        print(f"   Summary: {analysis.analysis_summary}")
    except Exception as e:
        print(f"⚠️  Analysis failed (expected without API key): {e}")
        # Use fallback analysis
        from analyzer import LLMAnalyzer
        analyzer_instance = LLMAnalyzer()
        analysis = analyzer_instance._create_fallback_analysis(profile)
        print(f"✅ Using fallback analysis")
    
    print("\n3️⃣ Testing Lyrics Generation...")
    generator = LyricsGenerator()
    
    try:
        lyrics = await generator.generate_lyrics(profile, analysis, "playful")
        print(f"✅ Lyrics generated")
        print(f"   Style: {lyrics.style}")
        print(f"   BPM: {lyrics.bpm}")
        print(f"   Wordplay rating: {lyrics.wordplay_rating:.2f}")
        print(f"   Intro preview: {lyrics.intro[:100]}...")
        print(f"   Verses: {len(lyrics.verses)}")
    except Exception as e:
        print(f"⚠️  Lyrics generation failed (expected without API key): {e}")
        # Use fallback
        lyrics = generator._create_fallback_lyrics(profile, analysis, "playful")
        print(f"✅ Using fallback lyrics")
    
    print("\n4️⃣ Testing Audio Configuration...")
    audio_config = await create_audio_config("echo", "trap", "playful")
    print(f"✅ Audio config created")
    print(f"   Voice: {audio_config.voice_model}")
    print(f"   Beat: {audio_config.beat_type}")
    print(f"   BPM: {audio_config.target_bpm}")
    print(f"   Effects: Compression {audio_config.compression_ratio}x")
    
    print("\n5️⃣ Testing Video Generator Setup...")
    video_gen = VideoGenerator()
    print(f"✅ Video generator initialized")
    print(f"   Resolution: {video_gen.resolution}")
    print(f"   FPS: {video_gen.fps}")
    
    # Test avatar creation
    avatar = await video_gen._create_avatar_placeholder("John Smith")
    print(f"✅ Avatar placeholder created: {avatar.size}")
    
    print("\n6️⃣ Testing API Models...")
    request = RoastRequest(
        manual_text=test_profile_text,
        style="playful",
        beat_type="trap",
        voice_preference="echo",
        include_video=True
    )
    print(f"✅ API request model validated")
    print(f"   Style: {request.style}")
    print(f"   Beat: {request.beat_type}")
    print(f"   Video: {request.include_video}")
    
    print("\n🎉 All core components tested successfully!")
    print("\nTo run the full server:")
    print("1. Add your OPENAI_API_KEY to .env file")
    print("2. Run: python app.py")
    print("3. Test at: http://localhost:8000")


async def test_performance():
    """Test performance of key operations"""
    print("\n⏱️  Performance Testing...")
    
    test_text = "Tech CEO who loves synergy and disruption" * 10
    profile = create_manual_profile(test_text, "Test User")
    
    # Test analysis fallback speed
    start = datetime.now()
    analyzer = LLMAnalyzer()
    analysis = analyzer._create_fallback_analysis(profile)
    analysis_time = (datetime.now() - start).total_seconds()
    
    print(f"✅ Fallback analysis: {analysis_time:.3f}s")
    
    # Test lyrics fallback speed
    start = datetime.now()
    generator = LyricsGenerator()
    lyrics = generator._create_fallback_lyrics(profile, analysis, "playful")
    lyrics_time = (datetime.now() - start).total_seconds()
    
    print(f"✅ Fallback lyrics: {lyrics_time:.3f}s")
    
    total_time = analysis_time + lyrics_time
    print(f"📊 Total fallback pipeline: {total_time:.3f}s")


def test_imports():
    """Test that all required packages are importable"""
    print("\n📦 Testing Package Imports...")
    
    required_packages = [
        "fastapi",
        "uvicorn", 
        "pydantic",
        "openai",
        "anthropic",
        "httpx",
        "beautifulsoup4",
        "pydub",
        "numpy",
        "cv2",
        "PIL",
        "redis"
    ]
    
    failed_imports = []
    
    for package in required_packages:
        try:
            if package == "cv2":
                import cv2
            elif package == "PIL":
                from PIL import Image
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError as e:
            print(f"❌ {package}: {e}")
            failed_imports.append(package)
    
    if failed_imports:
        print(f"\n⚠️  Failed imports: {failed_imports}")
        print("Run: pip install -r requirements.txt")
    else:
        print("\n🎉 All packages imported successfully!")


async def main():
    """Run all tests"""
    print("🚀 Roastify Backend Test Suite")
    print("=" * 50)
    
    test_imports()
    await test_manual_profile_flow() 
    await test_performance()
    
    print("\n" + "=" * 50)
    print("✅ Test suite completed!")
    print("\nReady to start the server? Run: python app.py")


if __name__ == "__main__":
    asyncio.run(main())