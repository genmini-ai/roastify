# roastify - DISS TRACK GENERATOR
*Any2Any Content Transformation Engine - 12 Hour Hackathon Build*

## 🎯 Project Overview
Transform any social media profile (LinkedIn/Twitter) into a personalized rap diss track with AI-generated lyrics, voice synthesis, and auto-generated music video. This showcases our any2any content transformation engine in the most memorable way possible.

## 🚀 Quick Start

```bash
# Clone repo
git clone [repo]
cd diss-track-generator

# Setup environment
cp .env.example .env
# Add your API keys:
# - OPENAI_API_KEY (GPT-5/GPT-4)
# - ANTHROPIC_API_KEY (Claude for backup)
# - ELEVENLABS_API_KEY (Voice synthesis)
# - REPLICATE_API_KEY (Video generation)
# - BROWSERLESS_API_KEY (Web scraping)

# Install dependencies
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..

# Run everything
docker-compose up

# Or run separately
python backend/app.py
cd frontend && npm start
```

Visit http://localhost:3000

## 🏗️ Architecture

```
Input (LinkedIn/Twitter URL)
    ↓
Profile Scraper (Playwright/Browserless)
    ↓
LLM Analysis (GPT-5)
    ↓
Lyrics Generation (GPT-5 with prompts)
    ↓
Parallel Processing:
    ├── Audio Generation (ElevenLabs)
    └── Beat Selection (Pre-made)
    ↓
Audio Mixing (Pydub)
    ↓
Video Generation (Replicate/Local)
    ↓
Multi-format Export (Showcase any2any)
```

## 📁 Project Structure

```
diss-track-generator/
├── README.md                     # This file
├── docker-compose.yml           # One-click setup
├── .env.example                 # Environment template
│
├── backend/
│   ├── requirements.txt        # Python dependencies
│   ├── app.py                  # FastAPI server
│   ├── scraper.py             # Profile scraping (LinkedIn/Twitter)
│   ├── analyzer.py            # LLM-based profile analysis
│   ├── generator.py           # Lyrics generation pipeline
│   ├── audio.py               # Voice synthesis & mixing
│   ├── video.py               # Video generation
│   ├── transformer.py         # Any2any transformation engine
│   └── demo.py                # Demo optimizations
│
├── frontend/
│   ├── package.json           # Node dependencies
│   ├── src/
│   │   ├── App.jsx           # Main React app
│   │   ├── components/
│   │   │   ├── URLInput.jsx  # URL input component
│   │   │   ├── Generator.jsx # Generation progress
│   │   │   ├── Player.jsx    # Audio/video player
│   │   │   └── Transformer.jsx # Format transformer
│   │   └── utils/
│   │       ├── api.js        # Backend API calls
│   │       └── demo.js       # Demo helpers
│   └── public/
│       └── index.html
│
├── prompts/
│   ├── profile_analysis.md   # Profile analysis prompt
│   ├── lyrics_generation.md  # Rap lyrics prompt
│   ├── roast_angles.md      # Roasting strategies
│   └── transformations.md    # Any2any prompts
│
├── assets/
│   ├── beats/                # Pre-made instrumentals
│   │   ├── trap_beat.mp3
│   │   ├── boom_bap.mp3
│   │   └── lofi_beat.mp3
│   └── templates/            # Video templates
│       └── music_video.json
│
├── cache/                    # Demo cache
│   ├── profiles/            # Pre-scraped profiles
│   └── outputs/             # Pre-generated content
│
└── scripts/
    ├── setup.sh             # Environment setup
    ├── warmup.py           # API pre-warming
    └── demo_flow.py        # Demo automation
```

## 🔧 Core Components

### 1. **Profile Scraper** (`scraper.py`)
- Handles LinkedIn and Twitter URLs
- Uses Playwright for local dev
- Browserless API for production
- Extracts: bio, posts, work history, education

### 2. **LLM Analyzer** (`analyzer.py`)
- GPT-5/Claude analyzes scraped content
- Extracts: personality traits, buzzwords, achievements
- Identifies roast angles
- Generates personality model for content

### 3. **Lyrics Generator** (`generator.py`)
- GPT-5 writes personalized rap lyrics
- Follows hip-hop structure (intro/verse/hook/outro)
- Maintains rhyme schemes
- Incorporates profile-specific references

### 4. **Audio Pipeline** (`audio.py`)
- ElevenLabs for rap voice synthesis
- Pre-made beats for different moods
- Pydub for mixing vocals + beat
- Real-time streaming for speed

### 5. **Video Generator** (`video.py`)
- Simple but effective visualizations
- Lyrics sync with audio
- Profile images with effects
- Export in multiple formats

### 6. **Any2Any Transformer** (`transformer.py`)
- Showcases our core technology
- Diss track → LinkedIn recommendation
- Diss track → PowerPoint presentation
- Diss track → Academic paper

## 💨 Speed Optimizations

### Critical Path (Must Work)
1. URL → Profile text extraction
2. LLM analysis → Roast angles
3. Generate lyrics
4. Basic TTS audio
5. Display results

### Parallel Processing
```python
async def generate_content():
    # Run simultaneously
    tasks = [
        analyze_profile(),     # 2-3s
        generate_lyrics(),     # 2-3s
        prepare_beat(),        # 0.1s (pre-loaded)
    ]
    results = await asyncio.gather(*tasks)
```

### Caching Strategy
- Cache scraped profiles (avoid re-scraping)
- Cache LLM responses (save API calls)
- Pre-load beats and assets
- Use CDN for static files

## 🎮 Demo Scripts

### YC Demo Focus
```python
# Emphasize: Growth, virality, clear monetization
- Quick generation (show speed)
- Share functionality (viral potential)  
- Creator economy angle ($$$)
```

### Afore Demo Focus
```python
# Emphasize: Technical depth, infrastructure
- Show LLM orchestration
- Explain any2any architecture
- Discuss scaling challenges
```

## 🚨 Fallback Plans

1. **If scraping fails**: Manual text input
2. **If GPT-5 is slow**: Use GPT-4-turbo
3. **If ElevenLabs fails**: Pre-recorded audio
4. **If video gen fails**: Static image + audio
5. **Nuclear option**: Pre-recorded demo video

## 📊 Metrics to Show

- Generation time: ~8 seconds
- Transformation options: 10+ formats
- Information preservation: 94%
- Potential market: 2M+ creators
- Revenue model: $50/month subscription

## 🔑 Environment Variables

```bash
# LLMs
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Audio/Video
ELEVENLABS_API_KEY=...
REPLICATE_API_KEY=...

# Scraping
BROWSERLESS_API_KEY=...
BRIGHT_DATA_PROXY=... # Backup for LinkedIn

# Demo Config
DEMO_MODE=true
CACHE_ENABLED=true
TARGET_AUDIENCE=yc # or 'afore'
MAX_GENERATION_TIME=10 # seconds

# Optional
REDIS_URL=redis://localhost:6379
SENTRY_DSN=... # Error tracking
```

## 🏃‍♂️ 12-Hour Timeline

| Hour | Focus | Deliverable |
|------|-------|------------|
| 0-2 | Setup & Scraping | Working URL → text extraction |
| 2-4 | LLM Integration | Profile analysis + lyrics generation |
| 4-6 | Audio Pipeline | TTS + beat mixing working |
| 6-8 | Basic Frontend | Input → Results display |
| 8-9 | Video Generation | Basic video output |
| 9-10 | Transformations | Show any2any capability |
| 10-11 | Polish & Debug | Fix critical issues |
| 11-12 | Demo Practice | Rehearse, prepare backups |

## 🎯 Demo Flow (90 seconds)

1. **Hook (0-15s)**
   - "We transform any content into any format"
   - Input judge's LinkedIn URL

2. **Magic (15-45s)**
   - Show real-time generation
   - Play diss track (keep it short!)
   - Audience laughs

3. **Business (45-75s)**
   - "But watch this..." 
   - Transform to different formats
   - "Same engine powers content for 2M creators"

4. **Close (75-90s)**
   - "$50/month, 40% margins"
   - "Already have 100 beta users"
   - "This demo IS our marketing"

## 🐛 Known Issues & Solutions

| Issue | Solution |
|-------|----------|
| LinkedIn requires login | Use cached profiles for demo |
| GPT-5 too slow | Fallback to GPT-4-turbo |
| Rate limits | Multiple API keys, rotate |
| CORS errors | Proxy through backend |

## 🚀 Post-Hackathon

If we win:
1. Polish the transformation engine
2. Add more input sources (TikTok, Instagram)
3. Add more output formats
4. Build creator dashboard
5. Launch on Product Hunt
6. Sell to Adobe for $100M 😎

## 📝 Notes

- **Keep it simple**: Better to have 3 working features than 10 broken ones
- **Demo is everything**: 50% coding, 50% preparing demo
- **Have backups**: Everything that can fail, will fail
- **Energy matters**: High energy presentation wins

---

*Built with 💔 and 🔥 at [Hackathon Name]*
*"Transforming content and feelings since 2024"*
