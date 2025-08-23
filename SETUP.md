# Roastify Environment Setup Guide

This guide will help you set up the complete Roastify development environment using Conda.

## 🚀 Quick Setup (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd roastify

# Run the automated setup script
./setup_env.sh

# Activate the environment
conda activate roastify

# Add your API keys to .env
cd backend
vim .env  # Add your OPENAI_API_KEY and other keys

# Test the installation
python test_url_roast.py --sample linkedin --verbose
```

## 📋 Manual Setup

If you prefer to set up manually or the automated script doesn't work:

### 1. Prerequisites

- **Conda**: Install [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or Anaconda
- **Python 3.11+**: Will be installed via conda
- **Git**: For cloning the repository

### 2. Create Conda Environment

```bash
# Create environment from YAML file
conda env create -f environment.yml

# Activate the environment
conda activate roastify

# Install Playwright browsers
playwright install chromium
```

### 3. Install System Dependencies

#### macOS
```bash
# Install FFmpeg for video processing
brew install ffmpeg

# Install system audio libraries (if needed)
brew install portaudio
```

#### Ubuntu/Debian
```bash
# Install FFmpeg
sudo apt update
sudo apt install ffmpeg

# Install system dependencies
sudo apt install portaudio19-dev python3-pyaudio
sudo apt install libsndfile1-dev  # For soundfile
```

#### Windows
```bash
# Install FFmpeg - download from https://ffmpeg.org/download.html
# Add FFmpeg to your PATH

# Or use chocolatey
choco install ffmpeg
```

### 4. Environment Configuration

```bash
# Copy environment template
cd backend
cp .env.example .env

# Edit the .env file and add your API keys
vim .env
```

Required API keys:
- `OPENAI_API_KEY`: For TTS and LLM (required)
- `ANTHROPIC_API_KEY`: For LLM fallback (optional)
- `BROWSERLESS_API_KEY`: For web scraping (optional)
- `REPLICATE_API_KEY`: For advanced video generation (optional)

### 5. Create Project Directories

```bash
mkdir -p backend/assets/{beats,samples}
mkdir -p cache/{profiles,outputs}
mkdir -p test_output
mkdir -p logs
```

## 🧪 Testing Your Setup

### Quick Test
```bash
# Activate environment
conda activate roastify
cd backend

# Test with sample data (no API keys required)
python test_url_roast.py --sample linkedin --scenario quick --verbose

# Test with API keys (if configured)
python test_url_roast.py --sample linkedin --scenario full --verbose
```

### Test Individual Components

```bash
# Test basic imports
python -c "
import fastapi, openai, pydub, cv2, playwright
print('✅ All core modules imported successfully')
"

# Test backend server
python app.py &
curl http://localhost:8000/
kill %1  # Stop the server
```

## 📦 Environment Structure

The conda environment includes:

### Core Framework
- **FastAPI**: Web framework for API
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation

### AI/ML
- **OpenAI**: GPT models and TTS
- **Anthropic**: Claude models (fallback)

### Audio Processing
- **PyDub**: Audio manipulation
- **Librosa**: Audio analysis
- **Pedalboard**: Audio effects
- **SoundFile**: Audio I/O

### Video Processing  
- **OpenCV**: Video processing
- **Pillow**: Image manipulation

### Web Scraping
- **Playwright**: Browser automation
- **BeautifulSoup**: HTML parsing

### Utilities
- **Redis**: Caching
- **Requests/HTTPX**: HTTP clients
- **Tenacity**: Retry logic

## 🔧 Configuration Options

### Environment Variables (.env)

```bash
# Core AI APIs
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Web Scraping
BROWSERLESS_API_KEY=your-browserless-key-here
PLAYWRIGHT_HEADLESS=true

# Video Generation
REPLICATE_API_KEY=your-replicate-key-here

# Caching (optional)
REDIS_URL=redis://localhost:6379
CACHE_ENABLED=true

# Configuration
DEMO_MODE=false
MAX_GENERATION_TIME=15
DEBUG=false
LOG_LEVEL=INFO

# Server
HOST=0.0.0.0  
PORT=8000
CORS_ORIGINS=["http://localhost:3000"]
```

### Audio Configuration

The system automatically creates sample beats in `backend/assets/beats/`:
- `trap_beat.mp3`: Modern trap-style instrumental
- `boom_bap.mp3`: Classic hip-hop beat
- `lofi_beat.mp3`: Chill lo-fi instrumental

## 🚨 Troubleshooting

### Common Issues

#### 1. Conda Environment Creation Fails
```bash
# Clear conda cache
conda clean --all

# Try creating with specific Python version
conda create -n roastify python=3.11
conda activate roastify
pip install -r backend/requirements.txt
```

#### 2. Playwright Browser Installation Fails
```bash
# Install browsers manually
conda activate roastify
playwright install chromium

# Or install all browsers
playwright install
```

#### 3. Audio Dependencies Issues
```bash
# macOS: Install system dependencies
brew install portaudio ffmpeg

# Linux: Install system packages
sudo apt install portaudio19-dev libsndfile1-dev ffmpeg

# Reinstall audio packages
pip uninstall pydub librosa soundfile pedalboard
pip install pydub librosa soundfile pedalboard
```

#### 4. OpenCV Import Errors
```bash
# Reinstall opencv
pip uninstall opencv-python
pip install opencv-python

# Or use conda version
conda install opencv
```

#### 5. Import Errors in Test Script
```bash
# Check that you're in the right directory and environment
pwd  # Should be in roastify/backend
conda list  # Should show roastify packages
python -c "import sys; print(sys.path)"  # Check Python path
```

### Testing Different Modes

The system supports different operational modes:

#### Full Mode (Best Quality)
- Requires: `OPENAI_API_KEY`
- Features: AI analysis, AI lyrics, OpenAI TTS, full video

```bash
export OPENAI_API_KEY=your-key
python test_url_roast.py --sample linkedin --scenario full
```

#### Partial Mode  
- Requires: `ANTHROPIC_API_KEY`
- Features: AI analysis, AI lyrics, fallback audio, basic video

```bash
export ANTHROPIC_API_KEY=your-key
python test_url_roast.py --sample linkedin --scenario full
```

#### Fallback Mode (No API Keys)
- Requires: Nothing
- Features: Template analysis/lyrics, placeholder audio, basic video

```bash
unset OPENAI_API_KEY ANTHROPIC_API_KEY
python test_url_roast.py --sample linkedin --scenario quick
```

## 📊 Performance Optimization

### For Development
```bash
# Quick testing with audio-only
python test_url_roast.py --sample linkedin --audio-only

# Skip video generation for speed
export DEMO_MODE=true
```

### For Production
```bash
# Enable caching
export CACHE_ENABLED=true
export REDIS_URL=redis://localhost:6379

# Start Redis server
redis-server &

# Use production settings
export DEBUG=false
export LOG_LEVEL=INFO
```

## 🆘 Getting Help

If you encounter issues:

1. **Check the logs**: Look in the generated `test_output/*/log.txt` files
2. **Run with verbose**: Add `--verbose` to see detailed output
3. **Test components individually**: Use the individual test scripts
4. **Check dependencies**: Ensure all required packages are installed

## 🎯 Next Steps

Once your environment is set up:

1. **Test with sample data**: `python test_url_roast.py --sample linkedin --verbose`
2. **Test with real URLs**: `python test_url_roast.py --linkedin https://linkedin.com/in/username`  
3. **Start the server**: `python app.py`
4. **Build a frontend**: Connect to the API at `http://localhost:8000`

---

Ready to start roasting profiles! 🔥