import asyncio
import io
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import soundfile as sf
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range
import librosa
import pedalboard as pb
from pedalboard import Reverb, Compressor, HighpassFilter, LowpassFilter
import openai

from models import LyricsData, AudioConfig
from config import settings

logger = logging.getLogger(__name__)


class AudioPipeline:
    def __init__(self):
        self.openai_client = None
        
        if settings.openai_api_key:
            self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        
        self.beats_dir = Path(settings.beats_dir)
        self.samples_dir = Path(settings.samples_dir)
        
        # Ensure directories exist
        self.beats_dir.mkdir(parents=True, exist_ok=True)
        self.samples_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_audio(
        self, 
        lyrics: LyricsData, 
        audio_config: AudioConfig
    ) -> bytes:
        """Main entry point for audio generation"""
        logger.info(f"Generating audio with {audio_config.voice_model} voice")
        
        try:
            # Step 1: Generate vocals with OpenAI TTS
            vocals_audio = await self._generate_vocals(lyrics, audio_config)
            
            # Step 2: Load and prepare beat
            beat_audio = await self._load_beat(audio_config.beat_type)
            
            # Step 3: Process vocals (effects, timing)
            processed_vocals = await self._process_vocals(vocals_audio, audio_config)
            
            # Step 4: Mix vocals with beat
            final_mix = await self._mix_audio(processed_vocals, beat_audio, audio_config)
            
            return final_mix
            
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            # Fallback: return simple TTS without beat
            return await self._generate_fallback_audio(lyrics, audio_config)
    
    async def _generate_vocals(self, lyrics: LyricsData, config: AudioConfig) -> bytes:
        """Generate vocals using OpenAI TTS"""
        if not self.openai_client:
            raise Exception("OpenAI client not available")
        
        # Format lyrics for TTS (remove section markers)
        tts_text = self._format_lyrics_for_tts(lyrics.full_lyrics)
        
        logger.info(f"Generating TTS with voice: {config.voice_model}")
        
        # Use faster speed for rap delivery
        rap_speed = max(config.speed, 1.2)  # Minimum 1.2x speed for rap flow
        
        response = await self.openai_client.audio.speech.create(
            model="tts-1",  # Use tts-1 for speed, tts-1-hd for quality
            voice=config.voice_model,
            input=tts_text,
            speed=rap_speed,
            response_format="mp3"
        )
        
        return response.content
    
    def _format_lyrics_for_tts(self, lyrics: str) -> str:
        """Format lyrics for TTS with enhanced rap delivery"""
        lines = lyrics.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('[') and line.endswith(']'):
                # Section marker - add dramatic pause
                section = line.replace('[', '').replace(']', '')
                if section.upper() in ['HOOK', 'CHORUS']:
                    formatted_lines.append("... YO! ...") # Extra energy for hooks
                else:
                    formatted_lines.append("...")
            else:
                # Enhance lyric line for rap delivery
                enhanced_line = self._enhance_rap_line(line)
                formatted_lines.append(enhanced_line)
        
        # Join with strategic pauses
        return ' ... '.join(formatted_lines)
    
    def _enhance_rap_line(self, line: str) -> str:
        """Enhance a single lyric line for better rap delivery"""
        # Add emphasis to key words
        words = line.split()
        enhanced_words = []
        
        for word in words:
            # Emphasize certain words by making them ALL CAPS
            if any(keyword in word.lower() for keyword in ['roast', 'fire', 'burn', 'drop', 'beat', 'flow']):
                enhanced_words.append(word.upper())
            # Add breaks for rhymes (words ending in common rap rhyme patterns)
            elif word.endswith(('tion', 'ing', 'ight', 'ate', 'ack', 'ow')):
                enhanced_words.append(word + ",")  # Short pause after rhymes
            else:
                enhanced_words.append(word)
        
        enhanced_line = ' '.join(enhanced_words)
        
        # Add rhythm markers
        enhanced_line = enhanced_line.replace('!', '! YEAH!')
        enhanced_line = enhanced_line.replace('?', '? UH!')
        
        return enhanced_line
    
    async def _load_beat(self, beat_type: str) -> AudioSegment:
        """Load instrumental beat"""
        beat_files = {
            "trap": "trap_beat.mp3",
            "boom_bap": "boom_bap.mp3", 
            "lofi": "lofi_beat.mp3"
        }
        
        beat_filename = beat_files.get(beat_type, "trap_beat.mp3")
        beat_path = self.beats_dir / beat_filename
        
        # If beat file doesn't exist, create a simple drum pattern
        if not beat_path.exists():
            logger.warning(f"Beat file {beat_path} not found, creating placeholder")
            return await self._create_placeholder_beat(beat_type)
        
        try:
            beat = AudioSegment.from_file(str(beat_path))
            return beat
        except Exception as e:
            logger.error(f"Failed to load beat {beat_path}: {e}")
            return await self._create_placeholder_beat(beat_type)
    
    def _create_tone(self, frequency: float, duration_ms: int, volume: float = 0.3) -> AudioSegment:
        """Create a sine wave tone"""
        sample_rate = 44100
        duration_s = duration_ms / 1000.0
        t = np.linspace(0, duration_s, int(sample_rate * duration_s), False)
        wave = np.sin(frequency * 2 * np.pi * t) * volume
        wave_int16 = (wave * (2**15)).astype(np.int16)
        
        return AudioSegment(
            wave_int16.tobytes(),
            frame_rate=sample_rate,
            sample_width=2,
            channels=1
        )
    
    async def _create_placeholder_beat(self, beat_type: str) -> AudioSegment:
        """Create EDM-style beat patterns"""
        duration_ms = 180000  # 3 minutes
        beat = AudioSegment.silent(duration=duration_ms)
        
        # Calculate timing (120 BPM for EDM feel)
        bpm = 120
        beat_interval = int(60000 / bpm)  # 500ms per beat at 120 BPM
        bar_length = beat_interval * 4    # 4 beats per bar
        
        if beat_type == "trap":
            return await self._create_edm_trap_beat(beat, beat_interval, bar_length, duration_ms)
        elif beat_type == "boom_bap":
            return await self._create_edm_house_beat(beat, beat_interval, bar_length, duration_ms)
        else:  # lofi -> progressive house
            return await self._create_progressive_beat(beat, beat_interval, bar_length, duration_ms)
    
    async def _create_edm_trap_beat(self, base_beat: AudioSegment, beat_interval: int, bar_length: int, duration_ms: int) -> AudioSegment:
        """Create EDM-trap fusion beat"""
        # Create elements
        kick = self._create_tone(60, 150, 0.8)        # Deep kick
        snare = self._create_tone(200, 100, 0.6)      # Sharp snare
        hi_hat = self._create_tone(8000, 25, 0.3)     # Crisp hi-hat
        bass_drop = self._create_tone(40, 400, 0.7)   # Sub bass
        
        # Build pattern
        for bar_start in range(0, duration_ms, bar_length):
            # 4-on-the-floor kicks
            for beat in range(4):
                base_beat = base_beat.overlay(kick, position=bar_start + beat * beat_interval)
            
            # Snare on 2 and 4
            base_beat = base_beat.overlay(snare, position=bar_start + beat_interval)      # Beat 2
            base_beat = base_beat.overlay(snare, position=bar_start + 3 * beat_interval)  # Beat 4
            
            # Hi-hats (16th notes)
            for sixteenth in range(16):
                if sixteenth % 4 != 0:  # Not on kick beats
                    hi_hat_pos = bar_start + sixteenth * (beat_interval // 4)
                    base_beat = base_beat.overlay(hi_hat, position=hi_hat_pos)
            
            # Bass drop every 8 bars
            if (bar_start // bar_length) % 8 == 0:
                base_beat = base_beat.overlay(bass_drop, position=bar_start)
        
        return base_beat
    
    async def _create_edm_house_beat(self, base_beat: AudioSegment, beat_interval: int, bar_length: int, duration_ms: int) -> AudioSegment:
        """Create house-style beat"""
        kick = self._create_tone(80, 120, 0.9)        # Punchy kick
        clap = self._create_tone(1500, 80, 0.5)       # Clap sound
        hi_hat_closed = self._create_tone(12000, 20, 0.2)  # Closed hi-hat
        hi_hat_open = self._create_tone(8000, 60, 0.3)     # Open hi-hat
        
        for bar_start in range(0, duration_ms, bar_length):
            # Classic 4-on-the-floor
            for beat in range(4):
                base_beat = base_beat.overlay(kick, position=bar_start + beat * beat_interval)
            
            # Clap on 2 and 4
            base_beat = base_beat.overlay(clap, position=bar_start + beat_interval)
            base_beat = base_beat.overlay(clap, position=bar_start + 3 * beat_interval)
            
            # Hi-hat pattern
            for eighth in range(8):
                hi_hat_pos = bar_start + eighth * (beat_interval // 2)
                if eighth % 2 == 1:  # Off-beats
                    hat = hi_hat_open if eighth == 7 else hi_hat_closed
                    base_beat = base_beat.overlay(hat, position=hi_hat_pos)
        
        return base_beat
    
    async def _create_progressive_beat(self, base_beat: AudioSegment, beat_interval: int, bar_length: int, duration_ms: int) -> AudioSegment:
        """Create progressive house style beat"""
        kick = self._create_tone(70, 180, 0.8)
        snare = self._create_tone(250, 90, 0.4)
        perc = self._create_tone(4000, 30, 0.25)
        bass = self._create_tone(55, 300, 0.6)
        
        for bar_start in range(0, duration_ms, bar_length):
            # Kick pattern (not every beat for groove)
            kick_pattern = [0, 2.5, 3.5]  # Syncopated
            for kick_beat in kick_pattern:
                kick_pos = bar_start + int(kick_beat * beat_interval)
                base_beat = base_beat.overlay(kick, position=kick_pos)
            
            # Snare on 2
            base_beat = base_beat.overlay(snare, position=bar_start + beat_interval)
            
            # Percussion elements
            for perc_beat in [1.5, 2.75, 3.25]:
                perc_pos = bar_start + int(perc_beat * beat_interval)
                base_beat = base_beat.overlay(perc, position=perc_pos)
            
            # Bass line (every 2 bars)
            if (bar_start // bar_length) % 2 == 0:
                base_beat = base_beat.overlay(bass, position=bar_start)
        
        return base_beat
    
    async def _process_vocals(self, vocals_bytes: bytes, config: AudioConfig) -> AudioSegment:
        """Apply audio effects to vocals for rap sound"""
        logger.info("Processing vocals with effects")
        
        # Convert bytes to AudioSegment
        vocals = AudioSegment.from_file(io.BytesIO(vocals_bytes), format="mp3")
        
        # Step 1: Basic processing
        vocals = normalize(vocals)  # Normalize volume
        
        # Step 2: Apply effects using pedalboard
        vocals_processed = await self._apply_audio_effects(vocals, config)
        
        # Step 3: Adjust timing to match BPM
        vocals_synced = await self._sync_to_bpm(vocals_processed, config.target_bpm)
        
        return vocals_synced
    
    async def _apply_audio_effects(self, audio: AudioSegment, config: AudioConfig) -> AudioSegment:
        """Apply audio effects using pedalboard"""
        try:
            # Convert AudioSegment to numpy array
            samples = np.array(audio.get_array_of_samples())
            
            # Handle stereo
            if audio.channels == 2:
                samples = samples.reshape((-1, 2))
            
            # Convert to float32
            samples = samples.astype(np.float32) / (2**15)
            
            # Simplified vocal processing for maximum clarity
            board = pb.Pedalboard([
                # Only essential processing
                # Remove high-pass filter to keep vocal warmth
                
                # Very gentle compression to control peaks only
                Compressor(
                    threshold_db=-12,  # Higher threshold - less compression
                    ratio=2.0,         # Gentle ratio for natural sound
                    attack_ms=5,       # Medium attack
                    release_ms=100     # Medium release
                ),
                
                # Minimal reverb for presence only
                Reverb(
                    room_size=0.3,     # Small room
                    damping=0.7,       # High damping for less reverb tail
                    wet_level=0.1,     # Very little wet signal
                    dry_level=0.9,     # Mostly dry for clarity
                    width=0.5          # Narrow width for focus
                ),
            ])
            
            # Apply main effects
            processed = board(samples, sample_rate=audio.frame_rate)
            
            # Skip excitement processing for maximum vocal clarity
            final_processed = processed  # Use processed vocals as-is
            
            # Apply saturation/distortion for edge (clip very gently)
            final_processed = np.clip(final_processed, -0.95, 0.95)
            
            # Convert back to AudioSegment
            processed_int = (final_processed * (2**15)).astype(np.int16)
            
            if audio.channels == 2:
                processed_int = processed_int.flatten()
            
            processed_audio = AudioSegment(
                processed_int.tobytes(),
                frame_rate=audio.frame_rate,
                sample_width=audio.sample_width,
                channels=audio.channels
            )
            
            return processed_audio
            
        except Exception as e:
            logger.warning(f"Effects processing failed, using basic processing: {e}")
            # Fallback to basic pydub effects
            return self._apply_basic_effects(audio, config)
    
    def _apply_basic_effects(self, audio: AudioSegment, config: AudioConfig) -> AudioSegment:
        """Fallback effects using pydub only"""
        # Basic compression
        audio = compress_dynamic_range(audio, threshold=-20, ratio=config.compression_ratio)
        
        # Simple EQ (boost mids for vocal clarity)
        audio = audio.low_pass_filter(8000)  # Cut harsh highs
        audio = audio.high_pass_filter(100)  # Cut low rumble
        
        # Add slight saturation by increasing gain then normalizing
        audio = audio + 3  # +3dB gain
        audio = normalize(audio)
        
        return audio
    
    async def _sync_to_bpm(self, vocals: AudioSegment, target_bpm: int) -> AudioSegment:
        """Sync vocals timing to target BPM"""
        try:
            # Convert to numpy for librosa processing
            samples = np.array(vocals.get_array_of_samples(), dtype=np.float32)
            samples = samples / (2**15)  # Normalize to float
            
            # Estimate tempo
            tempo, _ = librosa.beat.beat_track(y=samples, sr=vocals.frame_rate)
            current_bpm = float(tempo)
            
            logger.info(f"Estimated vocal BPM: {current_bpm:.1f}, target: {target_bpm}")
            
            # Calculate stretch ratio
            stretch_ratio = current_bpm / target_bpm
            
            # Only adjust if significantly different
            if abs(stretch_ratio - 1.0) > 0.1:
                # Time-stretch using librosa
                stretched = librosa.effects.time_stretch(samples, rate=stretch_ratio)
                
                # Convert back to AudioSegment
                stretched_int = (stretched * (2**15)).astype(np.int16)
                
                synced_audio = AudioSegment(
                    stretched_int.tobytes(),
                    frame_rate=vocals.frame_rate,
                    sample_width=vocals.sample_width,
                    channels=vocals.channels
                )
                
                return synced_audio
            
            return vocals
            
        except Exception as e:
            logger.warning(f"BPM sync failed, using original: {e}")
            return vocals
    
    async def _mix_audio(
        self, 
        vocals: AudioSegment, 
        beat: AudioSegment, 
        config: AudioConfig
    ) -> bytes:
        """Mix vocals with beat"""
        logger.info("Mixing vocals with beat")
        
        # Ensure beat is long enough
        vocals_duration = len(vocals)
        if len(beat) < vocals_duration:
            # Loop the beat
            loops_needed = (vocals_duration // len(beat)) + 1
            beat = beat * loops_needed
        
        # Trim beat to vocals length
        beat = beat[:vocals_duration]
        
        # BALANCED CLEAR MIX
        vocals = vocals.apply_gain(+12)  # +12dB clear vocals (keep this!)
        beat = beat.apply_gain(-6)       # -6dB audible beats in background
        
        # Simple mix for vocal clarity
        mixed = vocals.overlay(beat)
        
        # Simple mastering to preserve vocal loudness
        mixed = normalize(mixed)  # Basic normalization only
        
        # Export to bytes
        buffer = io.BytesIO()
        mixed.export(buffer, format="mp3", bitrate="192k")
        
        return buffer.getvalue()
    
    async def _mix_with_ducking(self, vocals: AudioSegment, beat: AudioSegment) -> AudioSegment:
        """Mix vocals and beat with EDM-style sidechain ducking simulation"""
        # Basic mix first
        mixed = vocals.overlay(beat)
        
        # Simulate sidechain ducking by detecting vocal presence and reducing beat
        # This is a simplified version - real sidechain would use the kick pattern
        try:
            # Convert to numpy for processing
            mixed_samples = np.array(mixed.get_array_of_samples()).astype(np.float32) / (2**15)
            beat_samples = np.array(beat.get_array_of_samples()).astype(np.float32) / (2**15)
            
            # Simple ducking: reduce beat when vocals are present
            # Detect vocal energy (simplified)
            window_size = int(mixed.frame_rate * 0.1)  # 100ms windows
            ducked_beat_samples = beat_samples.copy()
            
            for i in range(0, len(mixed_samples) - window_size, window_size):
                window = mixed_samples[i:i+window_size]
                vocal_energy = np.mean(np.abs(window))
                
                # Duck the beat proportionally to vocal energy
                duck_amount = min(0.7, vocal_energy * 2)  # Max 70% ducking
                ducked_beat_samples[i:i+window_size] *= (1 - duck_amount)
            
            # Reconstruct audio
            final_samples = np.array(vocals.get_array_of_samples()).astype(np.float32) / (2**15)
            final_samples += ducked_beat_samples
            
            # Convert back to AudioSegment
            final_int16 = np.clip(final_samples * (2**15), -2**15, 2**15-1).astype(np.int16)
            
            ducked_mixed = AudioSegment(
                final_int16.tobytes(),
                frame_rate=mixed.frame_rate,
                sample_width=mixed.sample_width,
                channels=mixed.channels
            )
            
            return ducked_mixed
            
        except Exception as e:
            logger.warning(f"Ducking failed, using simple mix: {e}")
            return mixed
    
    async def _master_edm_style(self, audio: AudioSegment) -> AudioSegment:
        """Apply EDM-style mastering"""
        try:
            # Multi-band compression simulation
            # High frequency enhancement
            enhanced = audio.apply_gain(1)  # Slight boost
            
            # Final limiting and loudness
            enhanced = normalize(enhanced)  # Normalize first
            enhanced = enhanced.apply_gain(-0.5)  # Leave some headroom
            
            # Stereo widening (if stereo)
            if audio.channels == 2:
                # Simple stereo widening by delaying one channel slightly
                left = enhanced.split_to_mono()[0]
                right = enhanced.split_to_mono()[1]
                
                # Add slight delay to right channel for width
                right_delayed = AudioSegment.silent(duration=2) + right  # 2ms delay
                right_delayed = right_delayed[:len(left)]  # Trim to match
                
                enhanced = AudioSegment.from_mono_audiosegments(left, right_delayed)
            
            return enhanced
            
        except Exception as e:
            logger.warning(f"EDM mastering failed, using basic processing: {e}")
            # Fallback to basic processing
            processed = normalize(audio)
            processed = processed.apply_gain(-1)  # -1dB headroom
            return processed
    
    async def _generate_fallback_audio(self, lyrics: LyricsData, config: AudioConfig) -> bytes:
        """Generate simple TTS-only audio as fallback"""
        logger.info("Using fallback audio generation")
        
        try:
            if not self.openai_client:
                raise Exception("No TTS available")
            
            # Simple TTS without effects
            tts_text = self._format_lyrics_for_tts(lyrics.full_lyrics)
            
            response = await self.openai_client.audio.speech.create(
                model="tts-1",
                voice=config.voice_model,
                input=tts_text,
                speed=config.speed
            )
            
            return response.content
            
        except Exception as e:
            logger.error(f"Fallback audio generation failed: {e}")
            # Ultimate fallback: silent audio
            silence = AudioSegment.silent(duration=30000)  # 30 second silence
            buffer = io.BytesIO()
            silence.export(buffer, format="mp3")
            return buffer.getvalue()
    
    def create_sample_beats(self):
        """Create sample beats for testing (run once)"""
        logger.info("Creating sample beats")
        
        # This would be called during setup to create placeholder beats
        for beat_type in ["trap", "boom_bap", "lofi"]:
            beat_path = self.beats_dir / f"{beat_type}_beat.mp3"
            
            if not beat_path.exists():
                # Create a simple beat placeholder
                beat = AudioSegment.silent(duration=180000)  # 3 minutes
                
                # Add simple rhythm based on type
                if beat_type == "trap":
                    # Trap: 808 on 1 and 3, snare on 2 and 4
                    kick = self._create_tone(60, 200)  # Low kick
                    snare = self._create_tone(200, 100)  # Snare
                elif beat_type == "boom_bap":
                    # Boom bap: Classic hip-hop pattern
                    kick = self._create_tone(80, 300)
                    snare = self._create_tone(250, 150)
                else:  # lofi
                    # Lofi: Softer, jazz-influenced
                    kick = self._create_tone(70, 250, 0.2)  # Lower volume
                    snare = self._create_tone(180, 120, 0.2)  # Lower volume
                
                # Add pattern every 667ms (90 BPM)
                for i in range(0, 180000, 2667):  # Every 4 beats
                    beat = beat.overlay(kick, position=i)           # Beat 1
                    beat = beat.overlay(snare, position=i + 667)    # Beat 2
                    beat = beat.overlay(kick, position=i + 1334)    # Beat 3
                    beat = beat.overlay(snare, position=i + 2001)   # Beat 4
                
                # Export
                beat.export(str(beat_path), format="mp3", bitrate="128k")
                logger.info(f"Created sample beat: {beat_path}")


async def create_audio_config(
    voice_model: str = "echo",
    beat_type: str = "trap",
    style: str = "playful"
) -> AudioConfig:
    """Create audio configuration"""
    
    # Adjust settings based on style
    if style == "aggressive":
        compression_ratio = 6.0
        autotune_strength = 0.3
    elif style == "witty":
        compression_ratio = 3.0
        autotune_strength = 0.5
    else:  # playful
        compression_ratio = 4.0
        autotune_strength = 0.7
    
    return AudioConfig(
        voice_model=voice_model,
        speed=1.1,
        pitch_shift=0.0,
        autotune_strength=autotune_strength,
        reverb_level=0.3,
        compression_ratio=compression_ratio,
        beat_type=beat_type,
        target_bpm=90
    )