# Beats Directory

This directory should contain the instrumental beats for mixing with rap vocals.

## Required Files:
- `trap_beat.mp3` - Trap style beat (120-140 BPM)
- `boom_bap.mp3` - Boom bap hip-hop beat (90-100 BPM)  
- `lofi_beat.mp3` - Lo-fi hip-hop beat (70-90 BPM)

## Where to Get Free Beats:

### Option 1: Free Beat Websites
- **Freesound.org** - Search for "trap beat", "hip hop beat", etc.
- **YouTube Audio Library** - royalty-free beats
- **Sample Focus** - free tier available
- **BeatStars** - free beats section

### Option 2: Quick Setup Script
Run this script to download some free beats:

```bash
# From the backend directory
python download_beats.py
```

### Option 3: Manual Download
1. Download 3 beats in MP3 format (around 2-3 minutes each)
2. Rename them to match the required filenames above
3. Place them in this directory

### Beat Requirements:
- Format: MP3
- Length: 2-3 minutes minimum (will loop if needed)
- BPM: Match the style (trap=120-140, boom_bap=90-100, lofi=70-90)
- Quality: 128kbps or higher

## Testing
Once beats are added, test with:
```bash
python tests/test_audio.py --lyrics-file tests/outputs/simple_pipeline_*.json
```