# Roastify Test Suite (Simplified MVP)

This directory contains a complete test suite for the simplified Roastify backend pipeline. The MVP architecture skips the analyzer step and goes directly from scraper to lyrics generator, then to audio/video generation.

## 📁 Directory Structure

```
tests/
├── __init__.py                 # Test package initialization
├── fixtures/                   # Sample test data (if needed)
├── outputs/                    # Test output directory (auto-created, gitignored)
├── test_scraper.py            # ✅ Brave Search API scraping tests
├── test_generator.py          # ✅ Simplified lyrics generation (no analyzer needed)
├── test_audio.py              # ✅ TTS audio generation with beats
├── test_video.py              # ✅ Video generation with lyrics overlay
├── test_simple_pipeline.py    # ✅ Scraper → Generator pipeline test
├── test_full_pipeline.py      # ✅ COMPLETE integration test (URL → Video)
└── README.md                  # This file
```

## 🧪 Individual Test Modules

### test_scraper.py - LinkedIn Profile Scraping

Tests LinkedIn profile scraping using Brave Search API.

```bash
# Test with specific LinkedIn URL
python tests/test_scraper.py --url https://linkedin.com/in/username

# Verbose output
python tests/test_scraper.py --url https://linkedin.com/in/username --verbose
```

**Requirements**: 
- BRAVE_API_KEY in .env file

**Output**: Search result with title and description from LinkedIn profile

### test_generator.py - Simplified Lyrics Generation

Tests the new simplified lyrics generator that works directly with search results (no analyzer needed).

```bash
# Test single profile with specific style
python tests/test_generator.py --style playful --profile linkedin_ceo

# Test all styles
python tests/test_generator.py --test styles

# Test all profile types
python tests/test_generator.py --test profiles

# Test API fallbacks
python tests/test_generator.py --test fallbacks

# Run all generator tests
python tests/test_generator.py --test all --verbose
```

**Requirements**:
- OpenAI API key OR Anthropic API key (fallback lyrics if neither)

**Features**:
- Tests with mock LinkedIn profiles (no API keys needed for basic testing)
- Tests different rap styles: playful, aggressive, witty
- Tests with different profile types: CEO, consultant, developer
- API fallback testing

### test_audio.py - TTS Audio Generation

Tests audio generation from lyrics using OpenAI TTS and beat integration.

```bash
# Test with generated lyrics file
python tests/test_audio.py --lyrics-file outputs/simple_pipeline_*.json --voice echo

# Test different voices
python tests/test_audio.py --test voices --lyrics-file outputs/simple_pipeline_*.json

# Test different beats  
python tests/test_audio.py --test beats --lyrics-file outputs/simple_pipeline_*.json

# Test all audio features
python tests/test_audio.py --test all --lyrics-file outputs/simple_pipeline_*.json --verbose
```

**Requirements**:
- OpenAI API key (for TTS)
- Generated lyrics file from previous tests

**Features**:
- Tests different TTS voices (echo, alloy, nova, shimmer)
- Tests different beat types (trap, boom_bap, lofi)
- Generates MP3 audio files with metadata

### test_video.py - Video Generation

Tests video generation with lyrics overlay and profile information.

```bash
# Test with generated audio and lyrics
python tests/test_video.py --audio-file outputs/roast_audio_*.mp3 --lyrics-file outputs/simple_pipeline_*.json

# Test different resolutions
python tests/test_video.py --test resolutions --audio-file outputs/roast_audio_*.mp3 --lyrics-file outputs/simple_pipeline_*.json

# Test all video features
python tests/test_video.py --test all --audio-file outputs/roast_audio_*.mp3 --lyrics-file outputs/simple_pipeline_*.json
```

**Requirements**:
- Generated audio file and lyrics file from previous tests
- Video processing dependencies (cv2, PIL)

**Features**:
- Tests different video resolutions (720p, 1080p, 360p)
- Generates MP4 video files with lyrics overlay
- Adapts search results to ProfileData format

### test_simple_pipeline.py - Scraper → Generator Pipeline

Tests the core simplified pipeline: Scraper → Generator (no analyzer).

```bash
# Test core pipeline with LinkedIn URL
python tests/test_simple_pipeline.py --url https://linkedin.com/in/username

# Test with different style
python tests/test_simple_pipeline.py --url https://linkedin.com/in/username --style aggressive

# Verbose output
python tests/test_simple_pipeline.py --url https://linkedin.com/in/username --verbose
```

**Requirements**:
- BRAVE_API_KEY (for scraping)
- OpenAI API key OR Anthropic API key (for lyrics generation)

**Output**: 
- Complete rap lyrics generated from LinkedIn profile
- Saved as both JSON and formatted text files

### test_full_pipeline.py - COMPLETE Integration Test 🚀

Tests the **complete end-to-end pipeline**: LinkedIn URL → Scraping → Lyrics → Audio → Video

```bash
# Complete pipeline test (URL to video)
python tests/test_full_pipeline.py --url https://linkedin.com/in/username

# Test with different options
python tests/test_full_pipeline.py --url https://linkedin.com/in/username --style aggressive --voice nova --beat boom_bap

# Audio-only test (skip video)
python tests/test_full_pipeline.py --url https://linkedin.com/in/username --skip-video

# Full verbose test
python tests/test_full_pipeline.py --url https://linkedin.com/in/username --style playful --voice echo --resolution 1920x1080 --verbose
```

**Requirements**:
- BRAVE_API_KEY (for scraping)
- OpenAI API key (for lyrics generation AND TTS audio)
- All pipeline dependencies

**Features**:
- **Complete pipeline**: URL → Scraper → Generator → Audio → Video
- **Comprehensive timing**: Tracks performance of each step
- **File management**: Saves all intermediate and final outputs
- **Flexible options**: Different styles, voices, beats, resolutions
- **Error handling**: Graceful failures with detailed logging
- **Final deliverable**: Complete roast video ready to share!

**Output files**:
```
outputs/
├── full_pipeline_xinyu_h_20250823_123456.json     # Complete metadata
├── full_pipeline_lyrics_xinyu_h_20250823_123456.txt    # Formatted lyrics  
├── full_pipeline_audio_xinyu_h_20250823_123456.mp3     # Audio with TTS + beat
└── full_pipeline_video_xinyu_h_20250823_123456.mp4     # Final roast video
```


## 🚀 Quick Start

1. **Set up environment**:
   ```bash
   # Required for scraping
   echo "BRAVE_API_KEY=your-key-here" >> backend/.env
   
   # Required for lyrics (choose one or both)
   echo "OPENAI_API_KEY=your-key-here" >> backend/.env
   echo "ANTHROPIC_API_KEY=your-key-here" >> backend/.env
   ```

2. **Test individual components**:

   **Scraper** (requires Brave API key):
   ```bash
   python tests/test_scraper.py --url https://linkedin.com/in/someone
   ```

   **Generator** (works with mock data, no API keys needed):
   ```bash
   python tests/test_generator.py --test single --style playful
   ```

   **Audio** (requires OpenAI for TTS):
   ```bash
   python tests/test_audio.py --lyrics-file outputs/simple_pipeline_*.json
   ```

3. **Test pipeline stages**:

   **Core pipeline** (scraper → generator):
   ```bash
   python tests/test_simple_pipeline.py --url https://linkedin.com/in/someone --style playful
   ```

4. **Test COMPLETE pipeline** (URL → Video):
   ```bash
   python tests/test_full_pipeline.py --url https://linkedin.com/in/someone --style playful
   ```

## 📋 Test Results

All tests save outputs to `tests/outputs/` with timestamps:

```
outputs/
# Individual component outputs
├── linkedin_scrape_*.json                    # Scraper results
├── lyrics_linkedin_ceo_playful_*.json        # Generator results (mock data)
├── rap_linkedin_ceo_playful_*.txt            # Formatted lyrics
├── roast_audio_echo_trap_*.mp3               # Generated audio files
├── roast_video_720p_*.mp4                    # Generated video files

# Pipeline outputs
├── simple_pipeline_*.json                    # Scraper → Generator results
├── rap_lyrics_*.txt                          # Pipeline lyrics

# COMPLETE pipeline outputs (the final deliverables!)
├── full_pipeline_user_name_*.json            # Complete metadata & timing
├── full_pipeline_lyrics_user_name_*.txt      # Formatted lyrics
├── full_pipeline_audio_user_name_*.mp3       # Final audio (TTS + beat)
└── full_pipeline_video_user_name_*.mp4       # 🎬 FINAL ROAST VIDEO
```

## 🏗️ Simplified Architecture

The MVP removes the analyzer step for faster, simpler roast generation:

```
OLD: URL → Scraper → Analyzer → Generator → Audio/Video
NEW: URL → Scraper → Generator → Audio → Video
      ↓        ↓         ↓       ↓      ↓
   LinkedIn  Brave   Direct   TTS   Lyrics
   Profile  Search   Roast   +Beat  Overlay
```

**Benefits**:
- ✅ Faster: One less LLM call
- ✅ Simpler: No complex personality analysis  
- ✅ Cheaper: Fewer API tokens
- ✅ MVP-ready: Direct path from LinkedIn profile to rap lyrics

The generator now creates roasts directly from LinkedIn search results (title + description), making its own assumptions about what's roast-worthy.

## 🔄 Recommended Test Workflow

**1. Start with individual components:**
```bash
# Test generator with mock data (no APIs needed)
python tests/test_generator.py --style playful --profile linkedin_ceo

# Test scraper with real LinkedIn URL
python tests/test_scraper.py --url https://linkedin.com/in/test-profile
```

**2. Test pipeline stages:**
```bash
# Test scraper → generator pipeline
python tests/test_simple_pipeline.py --url https://linkedin.com/in/test-profile --style playful

# Test audio generation from lyrics
python tests/test_audio.py --lyrics-file outputs/simple_pipeline_*.json --voice echo
```

**3. Run complete integration test:**
```bash
# Generate final roast video (the full experience!)
python tests/test_full_pipeline.py --url https://linkedin.com/in/test-profile --style playful

# Check all outputs
ls tests/outputs/
```

**4. Advanced testing:**
```bash
# Test different combinations
python tests/test_full_pipeline.py --url https://linkedin.com/in/someone --style aggressive --voice nova --beat boom_bap --resolution 1920x1080

# Audio-only testing (faster)
python tests/test_full_pipeline.py --url https://linkedin.com/in/someone --skip-video --verbose
```

## 🚨 Troubleshooting

**"No Brave API key found"**: Add `BRAVE_API_KEY=your-key` to `backend/.env`

**"No API generation available"**: Add `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` to `backend/.env`

**Import errors**: Run tests from project root: `python tests/test_generator.py`

**Empty lyrics**: Check API keys are valid and have sufficient credits

## 🎯 Testing Summary

| Test File | Purpose | Requirements | Output |
|-----------|---------|--------------|---------|
| `test_generator.py` | Lyrics generation | None (uses mock data) | Rap lyrics with different styles |
| `test_scraper.py` | LinkedIn scraping | BRAVE_API_KEY | LinkedIn profile title/description |
| `test_audio.py` | TTS audio generation | OpenAI API key | MP3 audio files |
| `test_video.py` | Video with lyrics | Previous outputs | MP4 video files |
| `test_simple_pipeline.py` | Core pipeline | BRAVE + OpenAI/Anthropic | Lyrics from real LinkedIn |
| **`test_full_pipeline.py`** | **COMPLETE system** | **All APIs** | **🎬 Final roast video** |

**Start here**: `test_full_pipeline.py --url https://linkedin.com/in/your-target` 🚀