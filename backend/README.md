# Roastify Backend

Transform social media profiles into personalized rap diss tracks with AI-generated lyrics, voice synthesis, and auto-generated music videos.

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install Playwright browsers
playwright install chromium

# 3. Set up environment
cp .env.example .env
# Edit .env and add your API keys

# 4. Run setup script
python setup.py

# 5. Test the backend
python test_backend.py

# 6. Start the server
python app.py
```

Visit http://localhost:8000 for API documentation.

## 🏗️ Architecture

### Core Pipeline
```
URL/Text Input → Profile Scraping → AI Analysis → Lyrics Generation → Audio/Video → Output
```

### Key Components

1. **Profile Scraper** (`scraper.py`)
   - LinkedIn/Twitter profile extraction
   - Playwright + Browserless API support
   - Fallback to manual text input

2. **AI Analyzer** (`analyzer.py`) 
   - OpenAI GPT-4 + Anthropic Claude
   - Personality trait extraction
   - Roast angle identification
   - Buzzword detection

3. **Lyrics Generator** (`generator.py`)
   - Structured rap generation (intro/verse/hook/outro)
   - AABB rhyme scheme
   - Personalized roasting content
   - Wordplay quality scoring

4. **Audio Pipeline** (`audio.py`)
   - OpenAI TTS with voice synthesis
   - Audio effects (compression, reverb, EQ)
   - Beat mixing and BPM synchronization
   - Multiple voice models

5. **Video Generator** (`video.py`)
   - Synchronized lyric display
   - Dynamic backgrounds
   - Profile image integration
   - MP4 output with ffmpeg

6. **API Server** (`app.py`)
   - FastAPI with async processing
   - WebSocket real-time updates
   - Background job processing
   - RESTful endpoints

## 📡 API Endpoints

### Main Endpoints

```http
POST /api/roast
{
  "url": "https://linkedin.com/in/username",
  "style": "playful|aggressive|witty",
  "beat_type": "trap|boom_bap|lofi", 
  "voice_preference": "echo|alloy|fable",
  "include_video": true
}
```

```http
GET /api/status/{job_id}
GET /api/result/{job_id}
```

### WebSocket
```
WS /ws/{job_id}  # Real-time progress updates
```

## 🔧 Configuration

### Required API Keys

Add these to your `.env` file:

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional but recommended  
ANTHROPIC_API_KEY=sk-ant-...
BROWSERLESS_API_KEY=...
REPLICATE_API_KEY=...

# Optional
REDIS_URL=redis://localhost:6379
```

### Audio Configuration

The system supports multiple audio processing approaches:

1. **Primary**: OpenAI TTS + Post-processing
   - Uses OpenAI's `tts-1` model
   - Applies compression, reverb, EQ
   - Syncs to beat BPM

2. **Fallback**: Pre-recorded samples
   - Uses placeholder vocal patterns
   - Dynamic word substitution
   - Guaranteed to work offline

## 🎵 Audio Processing Details

### TTS to Rap Conversion

1. **Voice Selection**: `echo` voice for most rhythmic delivery
2. **Speed Adjustment**: 1.1x speed for rap tempo  
3. **Effects Chain**:
   - High-pass filter (80Hz) to remove rumble
   - Compression (4:1 ratio) for punch
   - Reverb (30% room size) for presence
   - Low-pass filter (8kHz) to smooth harshness
4. **Beat Synchronization**: Tempo analysis and time-stretching
5. **Mixing**: Vocals prominent (80%), beat background (40%)

### Beat Integration

- Pre-loaded instrumental beats (trap, boom-bap, lofi)
- 90 BPM target tempo
- Automatic looping to match vocal length
- Dynamic volume balancing

## 🎬 Video Features

### Visual Elements

- **Dynamic Backgrounds**: Color-shifting gradients
- **Profile Integration**: Avatar creation from name initials
- **Lyric Display**: Synchronized text with timing
- **Brand Overlay**: Roastify branding
- **Effects**: Subtle animations and transitions

### Technical Specs

- Resolution: 1280x720 (720p)
- Frame Rate: 30 FPS
- Format: MP4 (H.264/AAC)
- Duration: Auto-detected from audio

## ⚡ Performance Optimizations

### Parallel Processing

```python
# Simultaneous operations:
- Profile scraping + analysis  
- Beat preparation
- Video template setup

# Sequential operations:
- Lyrics generation (needs analysis)
- Audio synthesis (needs lyrics)
- Video rendering (needs audio)
```

### Caching Strategy

- **Profile Cache**: 24 hours (avoid re-scraping)
- **Analysis Cache**: 12 hours (save LLM costs)
- **Lyrics Cache**: 6 hours (reuse similar requests)
- **Results Cache**: 7 days (completed roasts)

### Fallback Systems

1. **Scraping Fails** → Manual text input
2. **OpenAI Slow** → Anthropic Claude
3. **TTS Fails** → Pre-recorded samples
4. **Video Fails** → Audio-only output
5. **All AI Fails** → Template-based content

## 🧪 Testing

```bash
# Test imports and basic functionality
python test_backend.py

# Test with real API keys
export OPENAI_API_KEY=your-key
python test_backend.py

# Load test (requires additional setup)
python -m pytest tests/ -v
```

## 🚀 Production Deployment

### Environment Setup

1. **Server Requirements**: Python 3.8+, 4GB RAM, ffmpeg
2. **External Services**: OpenAI API, Redis, Cloud Storage
3. **Monitoring**: Sentry error tracking, metrics collection

### Scaling Considerations

- **Queue System**: Redis/Celery for job processing
- **File Storage**: AWS S3/Google Cloud for audio/video
- **CDN**: CloudFlare for asset delivery
- **Load Balancing**: Multiple backend instances

### Security

- Rate limiting (10 requests/hour per IP)
- API key validation and rotation
- Input sanitization and validation
- CORS configuration for frontend domains

## 🐛 Troubleshooting

### Common Issues

1. **"OpenAI API key not found"**
   - Add `OPENAI_API_KEY` to `.env` file
   - Restart server after updating .env

2. **"Playwright browser not found"**
   - Run: `playwright install chromium`

3. **"Audio effects not working"**
   - Install: `pip install pedalboard soundfile`
   - May require system audio libraries

4. **"Video generation failed"**
   - Install ffmpeg: `brew install ffmpeg` (Mac)
   - Check opencv installation: `pip install opencv-python`

5. **"Redis connection failed"**
   - Start Redis: `redis-server`
   - Or disable caching: `CACHE_ENABLED=false`

### Debug Mode

```bash
DEBUG=true LOG_LEVEL=DEBUG python app.py
```

## 📊 Monitoring

### Health Check
```http
GET /  # Returns service status
```

### Metrics
```http
GET /api/metrics  # Performance statistics
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Add tests for new functionality
4. Submit pull request

## 📄 License

Apache 2.0 License - see LICENSE file for details.

---

Built with ❤️ for the hackathon. Ready to roast some profiles! 🔥