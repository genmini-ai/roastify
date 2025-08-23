import React, { useState } from 'react';
import './App.css';

type RoastStatus = 'idle' | 'processing' | 'completed' | 'error';

interface ProgressStep {
  step: number;
  message: string;
  percentage: number;
}

const App: React.FC = () => {
  const [linkedinUrl, setLinkedinUrl] = useState('');
  const [voice, setVoice] = useState('echo');
  const [beat, setBeat] = useState('trap');
  const [style, setStyle] = useState('playful');
  const [status, setStatus] = useState<RoastStatus>('idle');
  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState<ProgressStep | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  const voices = [
    { value: 'alloy', label: 'Alloy', emoji: '🤖' },
    { value: 'echo', label: 'Echo', emoji: '🔊' },
    { value: 'fable', label: 'Fable', emoji: '📚' },
    { value: 'onyx', label: 'Onyx', emoji: '⚫' },
    { value: 'nova', label: 'Nova', emoji: '✨' },
    { value: 'shimmer', label: 'Shimmer', emoji: '💫' }
  ];

  const beats = [
    { value: 'trap', label: 'Trap', emoji: '🔥' },
    { value: 'boom_bap', label: 'Boom Bap', emoji: '💥' },
    { value: 'lofi', label: 'Lo-fi', emoji: '🎵' }
  ];

  const styles = [
    { value: 'playful', label: 'Playful', emoji: '😄' },
    { value: 'aggressive', label: 'Aggressive', emoji: '😈' },
    { value: 'witty', label: 'Witty', emoji: '🧠' }
  ];

  const handleRoast = async () => {
    if (!linkedinUrl) {
      alert('Please enter a LinkedIn URL!');
      return;
    }

    setStatus('processing');
    setProgress({ step: 0, message: 'Starting roast generation...', percentage: 0 });

    try {
      // Start roast generation
      const response = await fetch('http://localhost:8000/api/roast', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: linkedinUrl,
          voice_preference: voice,
          beat_type: beat,
          style: style,
          include_video: true
        })
      });

      const data = await response.json();
      setJobId(data.job_id);

      // Connect WebSocket for progress updates
      const ws = new WebSocket(`ws://localhost:8000/ws/${data.job_id}`);
      
      ws.onmessage = (event) => {
        const update = JSON.parse(event.data);
        
        if (update.type === 'progress') {
          setProgress({
            step: update.current_step,
            message: update.message,
            percentage: update.percentage
          });
        } else if (update.type === 'complete') {
          setStatus('completed');
          setVideoUrl(`http://localhost:8000/api/download/video/${data.job_id}`);
          setAudioUrl(`http://localhost:8000/api/download/audio/${data.job_id}`);
          ws.close();
        } else if (update.type === 'error') {
          setStatus('error');
          alert(`Error: ${update.message}`);
          ws.close();
        }
      };

      ws.onerror = () => {
        // Fallback to polling if WebSocket fails
        pollStatus(data.job_id);
      };
    } catch (error) {
      setStatus('error');
      alert('Failed to start roast generation!');
    }
  };

  const pollStatus = async (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/status/${jobId}`);
        const data = await response.json();
        
        if (data.status === 'completed') {
          clearInterval(interval);
          setStatus('completed');
          setVideoUrl(`http://localhost:8000/api/download/video/${jobId}`);
          setAudioUrl(`http://localhost:8000/api/download/audio/${jobId}`);
        } else if (data.status === 'failed') {
          clearInterval(interval);
          setStatus('error');
          alert(`Error: ${data.error_message}`);
        } else if (data.progress) {
          setProgress({
            step: data.steps_completed,
            message: data.current_step,
            percentage: data.progress * 100
          });
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 2000);
  };

  const resetRoast = () => {
    setStatus('idle');
    setLinkedinUrl('');
    setProgress(null);
    setVideoUrl(null);
    setAudioUrl(null);
    setJobId(null);
  };

  return (
    <div className="app">
      <div className="pixel-background"></div>
      
      <header className="header">
        <h1 className="logo">
          <span className="fire-emoji">🔥</span>
          ROASTIFY
          <span className="fire-emoji">🔥</span>
        </h1>
        <p className="tagline">Turn LinkedIn Profiles into Fire Rap Disses</p>
      </header>

      {status === 'idle' && (
        <div className="roast-form">
          <div className="input-group">
            <label className="pixel-label">LinkedIn URL</label>
            <input
              type="url"
              className="pixel-input"
              placeholder="https://linkedin.com/in/username"
              value={linkedinUrl}
              onChange={(e) => setLinkedinUrl(e.target.value)}
            />
          </div>

          <div className="options-row">
            <div className="input-group">
              <label className="pixel-label">Voice</label>
              <select 
                className="pixel-select"
                value={voice}
                onChange={(e) => setVoice(e.target.value)}
              >
                {voices.map(v => (
                  <option key={v.value} value={v.value}>
                    {v.emoji} {v.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="input-group">
              <label className="pixel-label">Beat</label>
              <select 
                className="pixel-select"
                value={beat}
                onChange={(e) => setBeat(e.target.value)}
              >
                {beats.map(b => (
                  <option key={b.value} value={b.value}>
                    {b.emoji} {b.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="input-group">
              <label className="pixel-label">Style</label>
              <select 
                className="pixel-select"
                value={style}
                onChange={(e) => setStyle(e.target.value)}
              >
                {styles.map(s => (
                  <option key={s.value} value={s.value}>
                    {s.emoji} {s.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <button 
            className="roast-button"
            onClick={handleRoast}
          >
            <span className="button-fire">🔥</span>
            ROAST 'EM!
            <span className="button-fire">🔥</span>
          </button>
        </div>
      )}

      {status === 'processing' && progress && (
        <div className="progress-container">
          <div className="progress-message">{progress.message}</div>
          <div className="progress-bar">
            <div 
              className="progress-fill"
              style={{ width: `${progress.percentage}%` }}
            >
              <div className="progress-pixels"></div>
            </div>
          </div>
          <div className="progress-percentage">{Math.round(progress.percentage)}%</div>
          
          <div className="loading-animation">
            <span className="fire-animation">🔥</span>
            <span className="fire-animation">🎤</span>
            <span className="fire-animation">🎵</span>
            <span className="fire-animation">🎬</span>
          </div>
        </div>
      )}

      {status === 'completed' && videoUrl && (
        <div className="results-container">
          <h2 className="results-title">🔥 Your Roast is Ready! 🔥</h2>
          
          <div className="video-container">
            <video 
              controls 
              className="roast-video"
              src={videoUrl}
              poster="/placeholder-video.png"
            >
              Your browser does not support the video tag.
            </video>
          </div>

          <div className="download-buttons">
            <a 
              href={videoUrl} 
              download 
              className="pixel-button download-button"
            >
              📹 Download Video
            </a>
            <a 
              href={audioUrl} 
              download 
              className="pixel-button download-button"
            >
              🎵 Download Audio
            </a>
          </div>

          <button 
            className="roast-button another-button"
            onClick={resetRoast}
          >
            🔥 Roast Another Profile
          </button>
        </div>
      )}

      {status === 'error' && (
        <div className="error-container">
          <h2 className="error-title">😵 Roast Failed!</h2>
          <p>Something went wrong with the roast generation.</p>
          <button 
            className="roast-button"
            onClick={resetRoast}
          >
            Try Again
          </button>
        </div>
      )}
    </div>
  );
};

export default App;