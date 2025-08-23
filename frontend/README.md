# 🔥 Roastify Frontend

Super cool black pixelated frontend for the Roastify app - Turn LinkedIn profiles into fire rap disses!

## Features

- **Retro 8-bit pixel art styling** with animated backgrounds
- **Real-time progress tracking** with WebSocket integration
- **Clean UX** with direct LinkedIn URL input and options
- **Video player** for generated roasts
- **Download capabilities** for video and audio files
- **Responsive design** for mobile and desktop

## Quick Start

1. **Serve the frontend:**
   ```bash
   cd frontend
   python -m http.server 3000
   ```

2. **Open in browser:**
   ```
   http://localhost:3000
   ```

3. **Make sure backend is running:**
   ```bash
   # In another terminal
   cd backend
   python app.py
   ```

## Usage

1. Enter a LinkedIn URL (e.g., `https://linkedin.com/in/username`)
2. Choose your preferred voice (Alloy, Echo, Fable, etc.)
3. Select a beat style (Trap, Boom Bap, Lo-fi)
4. Pick roast style (Playful, Aggressive, Witty)
5. Click **"ROAST 'EM! 🔥"**
6. Watch the progress bar and enjoy the show!
7. Download your generated video and audio

## Tech Stack

- **React 18** with TypeScript (via Babel)
- **CSS3** with custom pixel art animations
- **WebSocket** for real-time progress updates
- **Fetch API** for backend communication
- **Google Fonts** (Press Start 2P for retro vibes)

## Files

- `index.html` - Main HTML file with React setup
- `App.tsx` - Main React component with all functionality
- `App.css` - Pixel art styling and animations
- `package.json` - Project configuration

## API Integration

The frontend communicates with the backend at:
- `POST /api/roast` - Start roast generation
- `WebSocket /ws/{job_id}` - Real-time progress updates
- `GET /api/status/{job_id}` - Fallback status polling
- `GET /api/download/video/{job_id}` - Download video
- `GET /api/download/audio/{job_id}` - Download audio

## Customization

The pixelated theme can be customized in `App.css`:
- Colors: Modify CSS variables for different color schemes
- Animations: Adjust keyframes for different effects
- Layout: Change grid layouts and responsive breakpoints