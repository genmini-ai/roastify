#!/usr/bin/env python3
"""
Setup script for Roastify backend
Run this to initialize the backend environment
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(cmd: str, description: str):
    """Run a command and handle errors"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return None


def main():
    print("🚀 Setting up Roastify Backend...")
    
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        print("⚠️  Some dependencies failed to install. You may need to install them manually.")
    
    # Install Playwright browsers
    if not run_command("playwright install chromium", "Installing Playwright browser"):
        print("⚠️  Playwright browser installation failed. Web scraping may not work.")
    
    # Create directories
    print("📁 Creating directories...")
    dirs_to_create = [
        "assets/beats",
        "assets/samples", 
        "cache/profiles",
        "cache/outputs",
        "logs"
    ]
    
    for dir_path in dirs_to_create:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"   Created: {dir_path}")
    
    # Copy environment file
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if not env_file.exists() and env_example.exists():
        print("📄 Creating .env file from template...")
        with open(env_example) as f:
            content = f.read()
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✅ Created .env file")
        print("⚠️  IMPORTANT: Add your API keys to the .env file!")
        print("   Required: OPENAI_API_KEY")
        print("   Optional: ANTHROPIC_API_KEY, BROWSERLESS_API_KEY, REPLICATE_API_KEY")
    
    # Test basic imports
    print("🔍 Testing imports...")
    try:
        import fastapi
        import openai
        import pydub
        import cv2
        import numpy
        print("✅ Core dependencies imported successfully")
    except ImportError as e:
        print(f"❌ Import test failed: {e}")
        print("Some functionality may not work.")
    
    # Create sample beat files (placeholders)
    print("🎵 Creating sample beats...")
    try:
        from audio import AudioPipeline
        audio_pipeline = AudioPipeline()
        audio_pipeline.create_sample_beats()
        print("✅ Sample beats created")
    except Exception as e:
        print(f"⚠️  Could not create sample beats: {e}")
    
    print("\n🎉 Roastify Backend setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file and add your API keys")
    print("2. Start Redis server (if using caching): redis-server")
    print("3. Run the server: python app.py")
    print("4. Open http://localhost:8000 to check health")
    print("\nAPI Documentation: http://localhost:8000/docs")


if __name__ == "__main__":
    main()