# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

This is a hackathon project for "roastify" - a social media profile to rap diss track generator. The project includes a complete backend implementation with comprehensive testing infrastructure.

## Development Commands

Based on the project architecture outlined in README.md, the following commands are expected once implementation begins:

### Backend (Python/FastAPI)
```bash
# Setup environment (recommended: conda with Python 3.11)
conda create -n roastify python=3.11
conda activate roastify

# Install Python dependencies
pip install -r requirements.txt

# Set required environment variables
export OPENAI_API_KEY="your-openai-api-key"
export GOOGLE_API_KEY="your-google-api-key"

# Run backend server
python backend/app.py

# Run development test script
python test_url_roast.py --linkedin https://linkedin.com/in/someone

# Alternative Docker approach
docker-compose up
```

### Frontend (React)
```bash
# Install frontend dependencies
cd frontend && npm install

# Start development server (expected on port 3000)
npm start

# Build for production
npm run build
```

### Full Stack Development
```bash
# Run everything with Docker
docker-compose up

# Or run separately in different terminals
python backend/app.py
cd frontend && npm start
```

## Project Architecture

This is a social media profile to rap diss track generator with the following architecture:

**Technology Stack**:
- **Backend**: Python with FastAPI
- **Frontend**: React (Node.js) - planned
- **AI Services**: OpenAI GPT for TTS/lyrics, Google Gemini for PDF analysis
- **Web Scraping**: Playwright for PDF generation (replaces Browserless API)
- **Containerization**: Docker with docker-compose

**Core Components** (Implemented):

1. **Profile Scraper** (`backend/scraper.py`): Extracts profile data and generates PDFs from LinkedIn/Twitter URLs
2. **Profile Analyzer** (`backend/analyzer.py`): Main analyzer with fallback system
   - **OpenAI Analyzer** (`backend/openai_analyzer.py`): GPT-based profile analysis  
   - **Gemini Analyzer** (`backend/gemini_analyzer.py`): PDF-based analysis using Google Gemini
3. **Lyrics Generator** (`backend/generator.py`): Creates rap diss track lyrics with different humor styles
4. **Audio Processor** (`backend/audio.py`): TTS generation and audio processing
5. **Video Generator** (`backend/video.py`): Video creation with lyric synchronization
6. **Cache System** (`backend/cache.py`): Redis-based caching for API responses

**Frontend Structure**:
- Main React app with URL input, generation progress, and media player components
- API integration layer for backend communication
- Demo optimization helpers

**Key Data Flow**:
```
Input URL → Profile Scraping → AI Analysis → Content Generation → Audio/Video Processing → Multi-format Export
```

## Environment Configuration

The project requires the following API keys for external services:

```bash
# Required AI Services
OPENAI_API_KEY=sk-...          # For TTS and lyrics generation
GOOGLE_API_KEY=...             # For Gemini PDF analysis

# Optional: Caching and demo
DEMO_MODE=true                 # Enable demo optimizations
CACHE_ENABLED=true             # Enable Redis caching
REDIS_URL=redis://localhost:6379
```

**Note**: The project has been updated to use local PDF generation with Playwright instead of the Browserless API, and Google Gemini instead of other AI services for more cost-effective operation.

## Testing Infrastructure

The project includes a comprehensive test suite for all components:

### Test Commands
```bash
# Run individual component tests
python tests/test_scraper.py --url https://linkedin.com/in/someone
python tests/test_gemini.py --verbose  
python tests/test_analyzer.py --test comparison
python tests/test_generator.py --style playful
python tests/test_audio.py --voice alloy
python tests/test_video.py --resolution 720p

# Run all tests for a component
python tests/test_scraper.py --test all
python tests/test_analyzer.py --test all --verbose

# Use pytest for comprehensive testing
pytest tests/ -v
pytest tests/test_scraper.py -v
```

### Test Coverage
- **Profile scraping**: PDF generation, platform detection, fallback mechanisms
- **AI Analysis**: OpenAI and Gemini analyzers, comparison benchmarks
- **Content generation**: Lyrics creation, style variations, quality validation
- **Audio pipeline**: TTS generation, voice variations, format conversion
- **Video creation**: Synchronization, visual effects, resolution testing

See `tests/README.md` for detailed usage instructions.

## Development Notes

- **Async Processing**: Heavy use of asyncio for parallel task execution
- **PDF-First Architecture**: Local PDF generation with Gemini analysis for better content understanding
- **Fallback Systems**: OpenAI analyzer fallback when Gemini unavailable, manual profile creation for scraping failures
- **Comprehensive Testing**: Individual component tests with performance benchmarking
- **Quality Validation**: Scoring systems for analysis, lyrics, and media generation quality

## Important Considerations

**Performance Targets**:
- Total generation time: ~8 seconds
- Parallel processing for AI analysis, content generation, and audio preparation
- Caching to avoid redundant API calls

**Architecture Decisions**:
- FastAPI backend for async capabilities and automatic API documentation
- React frontend for responsive UI and real-time updates
- Docker for consistent development and deployment environments
- Multi-format export capability as core differentiator