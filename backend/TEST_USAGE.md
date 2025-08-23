# Roastify URL Test Script Usage

Test the complete Roastify pipeline with real LinkedIn/Twitter URLs or sample data.

## 🚀 Quick Start

```bash
# Make sure you're in the backend directory
cd backend

# Test with sample LinkedIn profile
python test_url_roast.py --sample linkedin --verbose

# Test with sample Twitter profile  
python test_url_roast.py --sample twitter --verbose

# Test with real LinkedIn URL
python test_url_roast.py --linkedin https://linkedin.com/in/username --verbose

# Test with real Twitter URL
python test_url_roast.py --twitter https://twitter.com/username --verbose
```

## 📁 Output Structure

Each test run creates a timestamped subfolder in `test_output/`:

```
test_output/
└── run_20240823_143022_linkedin_johnsmith/
    ├── profile.json      # Scraped/sample profile data
    ├── analysis.json     # AI personality analysis
    ├── lyrics.txt        # Generated rap lyrics
    ├── audio.mp3         # Generated audio track
    ├── video.mp4         # Generated music video (if enabled)
    ├── results.json      # Complete test results and timing
    └── log.txt          # Detailed execution log
```

## 🎛️ Command Options

### Input Options (choose one)
- `--linkedin URL` - Test with LinkedIn profile URL
- `--twitter URL` - Test with Twitter/X profile URL  
- `--sample {linkedin|twitter}` - Use built-in sample data

### Generation Options
- `--style {playful|aggressive|witty}` - Roast style (default: playful)
- `--beat {trap|boom_bap|lofi}` - Beat type (default: trap)
- `--voice {echo|alloy|fable|onyx|nova|shimmer}` - Voice model (default: echo)

### Test Options
- `--scenario {quick|full|aggressive|witty}` - Use predefined scenario
- `--audio-only` - Skip video generation (faster testing)
- `--verbose` - Show detailed progress and logging

## 🎭 Predefined Scenarios

- **quick**: Fast test with audio-only output
- **full**: Complete test with audio and video
- **aggressive**: Aggressive roasting style with boom-bap beat
- **witty**: Witty style with lofi beat

```bash
# Quick audio-only test
python test_url_roast.py --sample linkedin --scenario quick

# Full test with video
python test_url_roast.py --sample twitter --scenario full
```

## 🔑 API Key Requirements

The script adapts based on available API keys:

### Full Mode (Best Quality)
- **Required**: `OPENAI_API_KEY`
- **Features**: AI analysis, AI lyrics, OpenAI TTS, full video

### Partial Mode
- **Required**: `ANTHROPIC_API_KEY` 
- **Features**: AI analysis, AI lyrics, fallback audio, basic video

### Fallback Mode (No API Keys)
- **Required**: None
- **Features**: Template analysis/lyrics, silent audio, basic video

## 📋 Example Commands

```bash
# Test with real LinkedIn profile, verbose output
python test_url_roast.py --linkedin https://linkedin.com/in/elonmusk --verbose

# Test Twitter with aggressive style
python test_url_roast.py --twitter https://twitter.com/sundarpichai --style aggressive

# Quick test with sample data
python test_url_roast.py --sample linkedin --audio-only

# Full test with custom settings
python test_url_roast.py --sample twitter --style witty --beat lofi --voice alloy

# Use predefined scenario
python test_url_roast.py --sample linkedin --scenario full --verbose
```

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **API Key Missing**
   ```bash
   # Add to .env file
   echo "OPENAI_API_KEY=your-key-here" >> .env
   ```

3. **Permission Denied**
   ```bash
   # Make script executable
   chmod +x test_url_roast.py
   ```

4. **Scraping Fails**
   - Script automatically falls back to sample data
   - Use `--sample` option for consistent testing

### Test Modes

The script automatically detects your environment:
- ✅ **Full mode**: OpenAI API key available
- ⚠️ **Partial mode**: Only Anthropic API key  
- 🔄 **Fallback mode**: No API keys (uses templates)

## 📊 Results Analysis

Check the generated files:
- **results.json**: Complete timing and status info
- **log.txt**: Detailed execution log with timestamps
- **lyrics.txt**: Human-readable lyrics with metadata
- **analysis.json**: AI personality analysis results

## 🎯 Performance Benchmarks

Typical execution times:
- **Quick mode** (audio-only): 5-15 seconds
- **Full mode** (with video): 15-45 seconds  
- **Fallback mode**: 2-8 seconds

Times vary based on:
- API response speed
- Profile complexity
- System performance
- Video generation requirements

---

Ready to roast some profiles! 🔥