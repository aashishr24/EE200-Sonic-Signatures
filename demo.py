"""
Demo script showing how to use the music fingerprinter with synthetic audio.
This is useful for testing without real audio files.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from project import MusicFingerprinter
import tempfile
import os

def generate_synthetic_song(sr=22050, duration=3, frequencies=None):
    """
    Generate synthetic audio with specified frequencies.
    
    Args:
        sr: Sample rate
        duration: Duration in seconds
        frequencies: List of (freq, start_time, duration) tuples
        
    Returns:
        audio: Synthesized waveform
    """
    if frequencies is None:
        frequencies = [
            (440, 0.0, 0.5),   # A4
            (494, 0.5, 0.5),   # B4
            (523, 1.0, 0.5),   # C5
            (587, 1.5, 0.5),   # D5
            (659, 2.0, 0.5),   # E5
            (784, 2.5, 0.5),   # G5
        ]
    
    t = np.arange(sr * duration) / sr
    audio = np.zeros(sr * duration)
    
    for freq, start, dur in frequencies:
        mask = (t >= start) & (t < start + dur)
        # Add sine wave with envelope to avoid clicks
        phase = 2 * np.pi * freq * (t[mask] - start)
        envelope = np.sin(np.pi * (t[mask] - start) / dur) ** 0.5
        audio[mask] += 0.3 * np.sin(phase) * envelope
    
    return audio.astype(np.float32)

def main():
    """Run demo of the music fingerprinter."""
    print("\n" + "="*60)
    print("Music Fingerprinter Demo")
    print("="*60 + "\n")
    
    # Initialize fingerprinter
    fingerprinter = MusicFingerprinter()
    
    # Create temporary directory for demo files
    demo_dir = tempfile.mkdtemp()
    print(f"Demo directory: {demo_dir}\n")
    
    # Generate synthetic test songs
    print("Step 1: Generating synthetic test songs...")
    
    songs = {
        "song_1": [(440, 0.0, 0.5), (494, 0.5, 0.5), (523, 1.0, 0.5)],
        "song_2": [(587, 0.0, 0.5), (659, 0.5, 0.5), (784, 1.0, 0.5)],
        "song_3": [(523, 0.0, 0.5), (440, 0.5, 0.5), (494, 1.0, 0.5)],
    }
    
    song_files = {}
    sr = 22050
    
    for song_name, freqs in songs.items():
        # Generate audio
        audio = generate_synthetic_song(sr=sr, duration=3, frequencies=freqs)
        
        # Save as WAV
        filepath = os.path.join(demo_dir, f"{song_name}.wav")
        wavfile.write(filepath, sr, (audio * 32767).astype(np.int16))
        song_files[song_name] = filepath
        print(f"  ✓ Generated {song_name}.wav")
    
    print()
    
    # Build database
    print("Step 2: Building fingerprint database...")
    database = {}
    
    for song_name, filepath in song_files.items():
        print(f"\n  Processing {song_name}...")
        
        audio, _ = fingerprinter.load_audio(filepath)
        frequencies, times, magnitude = fingerprinter.compute_spectrogram(audio, sr)
        peaks = fingerprinter.find_peaks(magnitude, frequencies, threshold_db=5)
        
        print(f"    Found {len(peaks)} peaks")
        
        # Create fingerprints
        pairs = fingerprinter.create_fingerprint_pairs(peaks, frequencies, times)
        print(f"    Created {len(pairs)} peak pair fingerprints")
        
        # Store in database
        from collections import defaultdict
        database[song_name] = defaultdict(list)
        for fp in pairs:
            fp_hash = hash(fp) % (10 ** 9)
            database[song_name][fp_hash].append(0)
        database[song_name] = dict(database[song_name])
    
    print(f"\n  Database complete: {len(database)} songs indexed")
    
    # Test query: song_1 (should match perfectly)
    print("\n" + "="*60)
    print("Step 3: Testing query - Unmodified song_1")
    print("="*60 + "\n")
    
    query_audio, _ = fingerprinter.load_audio(song_files["song_1"])
    results = fingerprinter.match_query(query_audio, sr, database)
    
    print("Match Scores:")
    for song, result in sorted(results.items(), key=lambda x: x[1]['score'], reverse=True):
        score = result['score']
        num_fps = result['num_query_peaks']
        conf = (score / num_fps * 100) if num_fps > 0 else 0
        print(f"  {song:10s}: {score:4d} matches (confidence: {conf:5.1f}%)")
    
    best_match = max(results.items(), key=lambda x: x[1]['score'])
    print(f"\n  ✓ Best match: {best_match[0]}")
    
    # Test query: noisy version of song_1
    print("\n" + "="*60)
    print("Step 4: Testing robustness - Add noise to song_1")
    print("="*60 + "\n")
    
    noise = np.random.normal(0, 0.1, len(query_audio))
    noisy_audio = np.clip(query_audio + noise, -1, 1)
    
    results = fingerprinter.match_query(noisy_audio, sr, database)
    
    print("Match Scores (with noise):")
    for song, result in sorted(results.items(), key=lambda x: x[1]['score'], reverse=True):
        score = result['score']
        num_fps = result['num_query_peaks']
        conf = (score / num_fps * 100) if num_fps > 0 else 0
        print(f"  {song:10s}: {score:4d} matches (confidence: {conf:5.1f}%)")
    
    best_match = max(results.items(), key=lambda x: x[1]['score'])
    print(f"\n  ✓ Best match: {best_match[0]}")
    
    # Visualization
    print("\n" + "="*60)
    print("Step 5: Generating visualizations...")
    print("="*60 + "\n")
    
    # Plot spectrogram and constellation for song_1
    frequencies, times, magnitude = fingerprinter.compute_spectrogram(query_audio, sr)
    peaks = fingerprinter.find_peaks(magnitude, frequencies, threshold_db=5)
    
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    
    # Spectrogram
    ax = axes[0]
    pcm = ax.pcolormesh(times, frequencies, magnitude, shading='auto', cmap='viridis')
    ax.set_ylabel('Frequency (Hz)')
    ax.set_title('Song 1 - Spectrogram')
    ax.set_ylim([fingerprinter.freq_min, fingerprinter.freq_max])
    plt.colorbar(pcm, ax=ax, label='Magnitude (dB)')
    
    # Constellation
    ax = axes[1]
    pcm = ax.pcolormesh(times, frequencies, magnitude, shading='auto', cmap='viridis', alpha=0.7)
    if peaks:
        freq_peaks = frequencies[np.array([p[0] for p in peaks])]
        time_peaks = times[np.array([p[1] for p in peaks])]
        ax.scatter(time_peaks, freq_peaks, c='red', s=50, marker='o', 
                  edgecolors='white', linewidth=0.5, alpha=0.8, label='Peaks')
    ax.set_ylabel('Frequency (Hz)')
    ax.set_xlabel('Time (s)')
    ax.set_title('Song 1 - Peak Constellation')
    ax.set_ylim([fingerprinter.freq_min, fingerprinter.freq_max])
    ax.legend()
    plt.colorbar(pcm, ax=ax, label='Magnitude (dB)')
    
    plt.tight_layout()
    viz_path = os.path.join(demo_dir, "spectrogram_constellation.png")
    plt.savefig(viz_path, dpi=100)
    print(f"  ✓ Saved visualization to {viz_path}")
    plt.close()
    
    # Cleanup
    print("\n" + "="*60)
    print("Demo Complete!")
    print("="*60)
    print(f"\nTo run the interactive app:")
    print("  streamlit run ss.py")
    print("\nTo use real audio files:")
    print("  1. Upload .wav files in the 'Build Database' tab")
    print("  2. Upload a query clip in the 'Query & Identify' tab")
    print("  3. View results with spectrograms and peak constellations")

if __name__ == "__main__":
    main()
