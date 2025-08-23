#!/bin/bash
# Roastify Environment Setup Script
# This script sets up a conda environment for the Roastify project

set -e  # Exit on any error

echo "🚀 Roastify Environment Setup"
echo "==============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    print_error "Conda is not installed or not in PATH"
    print_info "Please install Miniconda or Anaconda first:"
    print_info "https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

print_status "Conda found: $(conda --version)"

# Check if environment already exists
ENV_NAME="roastify"
if conda env list | grep -q "^${ENV_NAME} "; then
    print_warning "Environment '${ENV_NAME}' already exists"
    read -p "Do you want to remove and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Removing existing environment..."
        conda env remove -n ${ENV_NAME} -y
        print_status "Environment removed"
    else
        print_info "Skipping environment creation"
        SKIP_ENV_CREATE=true
    fi
fi

# Create conda environment
if [[ "$SKIP_ENV_CREATE" != true ]]; then
    print_info "Creating conda environment from environment.yml..."
    conda env create -f environment.yml
    print_status "Conda environment '${ENV_NAME}' created successfully"
fi

# Activate environment and install additional dependencies
print_info "Activating environment and installing additional dependencies..."

# Use conda run to execute commands in the environment
print_info "Installing Playwright browsers..."
conda run -n ${ENV_NAME} playwright install chromium

# Check if ffmpeg is available
if command -v ffmpeg &> /dev/null; then
    print_status "FFmpeg found: $(ffmpeg -version 2>&1 | head -n1)"
else
    print_warning "FFmpeg not found - video generation may not work"
    print_info "Install FFmpeg with: brew install ffmpeg (macOS) or apt install ffmpeg (Ubuntu)"
fi

# Create directories
print_info "Creating project directories..."
mkdir -p backend/assets/beats
mkdir -p backend/assets/samples
mkdir -p cache/profiles
mkdir -p cache/outputs
mkdir -p test_output
mkdir -p logs

print_status "Directories created"

# Copy environment template
print_info "Setting up environment configuration..."
if [ ! -f backend/.env ]; then
    if [ -f backend/.env.example ]; then
        cp backend/.env.example backend/.env
        print_status "Created .env file from template"
        print_warning "IMPORTANT: Edit backend/.env and add your API keys!"
    else
        print_warning ".env.example not found"
    fi
else
    print_info ".env file already exists"
fi

# Test basic imports
print_info "Testing basic imports..."
conda run -n ${ENV_NAME} python -c "
import sys
print(f'Python version: {sys.version}')

# Test core imports
try:
    import fastapi
    print('✅ FastAPI imported successfully')
except ImportError as e:
    print(f'❌ FastAPI import failed: {e}')

try:
    import openai
    print('✅ OpenAI imported successfully')
except ImportError as e:
    print(f'❌ OpenAI import failed: {e}')

try:
    import pydub
    print('✅ PyDub imported successfully')
except ImportError as e:
    print(f'❌ PyDub import failed: {e}')

try:
    import cv2
    print('✅ OpenCV imported successfully')
except ImportError as e:
    print(f'❌ OpenCV import failed: {e}')

try:
    import playwright
    print('✅ Playwright imported successfully')
except ImportError as e:
    print(f'❌ Playwright import failed: {e}')
"

print_status "Import test completed"

# Create sample beats
print_info "Creating sample audio beats..."
conda run -n ${ENV_NAME} python -c "
import sys
sys.path.append('backend')
try:
    from audio import AudioPipeline
    audio_pipeline = AudioPipeline()
    audio_pipeline.create_sample_beats()
    print('✅ Sample beats created')
except Exception as e:
    print(f'⚠️  Could not create sample beats: {e}')
"

echo
print_status "🎉 Roastify environment setup complete!"
echo
echo "Next steps:"
echo "1. Activate the environment: conda activate ${ENV_NAME}"
echo "2. Edit backend/.env and add your API keys (especially OPENAI_API_KEY)"
echo "3. Test the installation:"
echo "   cd backend"
echo "   python test_url_roast.py --sample linkedin --verbose"
echo
echo "4. Start the server:"
echo "   python app.py"
echo
echo "5. Or run a test:"
echo "   python test_url_roast.py --sample linkedin --scenario quick"
echo
print_info "Environment name: ${ENV_NAME}"
print_info "Activate with: conda activate ${ENV_NAME}"
print_info "Deactivate with: conda deactivate"
echo