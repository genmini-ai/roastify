#!/usr/bin/env python3
"""
Simple script to download free beats for Roastify

This downloads CC-licensed beats from Freesound.org or creates simple synthetic beats.
"""
import os
import requests
from pathlib import Path
import sys

BEATS_DIR = Path("backend/assets/beats")

def download_file(url: str, filename: str) -> bool:
    """Download a file from URL"""
    try:
        print(f"Downloading {filename}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        filepath = BEATS_DIR / filename
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Downloaded {filename}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to download {filename}: {e}")
        return False

async def create_synthetic_beats():
    """Create synthetic beats using the existing audio pipeline"""
    print("Creating synthetic beats as placeholders...")
    
    try:
        sys.path.insert(0, str(Path("backend")))
        from audio import AudioPipeline
        
        audio_pipeline = AudioPipeline()
        
        # Create each beat type
        beat_types = ["trap", "boom_bap", "lofi"]
        
        for beat_type in beat_types:
            print(f"Creating {beat_type} beat...")
            beat = await audio_pipeline._create_placeholder_beat(beat_type)
            
            filename = f"{beat_type}_beat.mp3"
            filepath = BEATS_DIR / filename
            
            # Export beat
            beat.export(str(filepath), format="mp3", bitrate="128k")
            print(f"✅ Created {filename}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create synthetic beats: {e}")
        return False

def main():
    """Main function"""
    print("🎵 Roastify Beat Downloader")
    print("=" * 40)
    
    # Create beats directory if it doesn't exist
    BEATS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Option 1: Try to download real beats (commented out for now - need API keys)
    print("For now, creating synthetic beats...")
    print("To add real beats, manually download MP3 files and place them in:")
    print(f"  {BEATS_DIR.absolute()}")
    print()
    print("Required filenames:")
    print("  - trap_beat.mp3")  
    print("  - boom_bap.mp3")
    print("  - lofi_beat.mp3")
    print()
    
    # Option 2: Create synthetic beats as placeholders
    import asyncio
    success = asyncio.run(create_synthetic_beats())
    
    if success:
        print("\n🎉 Beats setup complete!")
        print("Test with: python tests/test_audio.py --lyrics-file tests/outputs/simple_pipeline_*.json")
    else:
        print("\n❌ Beat setup failed. Please add beats manually.")

if __name__ == "__main__":
    main()