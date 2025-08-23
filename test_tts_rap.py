#!/usr/bin/env python3
"""
Quick test script for OpenAI TTS rap capabilities
"""
import os
from dotenv import load_dotenv
import openai

# Load environment
load_dotenv('backend/.env')

# Sample rap lyrics
rap_lyrics = """
Yo, check it, we testing the TTS flow
Making sure the rhythm and the beat can go
With artificial voices spitting fire like this
OpenAI TTS putting rap to the test, never miss

LinkedIn profiles getting roasted with precision
Every word hitting hard with lyrical vision
From CEO to consultant, nobody's safe
When the AI starts rapping, it's sealing their fate
"""

def test_tts_voices():
    """Test different OpenAI TTS voices for rap"""
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    voices = ["echo", "alloy", "nova", "shimmer"]
    
    for voice in voices:
        print(f"🎤 Testing {voice} voice...")
        
        try:
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=rap_lyrics,
                speed=1.1  # Slightly faster for rap feel
            )
            
            # Save the audio
            output_file = f"test_rap_{voice}.mp3"
            with open(output_file, "wb") as f:
                f.write(response.content)
            
            print(f"✅ {voice} voice generated: {output_file} ({len(response.content):,} bytes)")
            
        except Exception as e:
            print(f"❌ Failed to generate {voice}: {e}")

if __name__ == "__main__":
    test_tts_voices()
    print("\n🎵 TTS rap test complete! Check the generated MP3 files.")