"""
QUICK REFERENCE - Music Identifier Commands
"""

# ========================================
# INSTALLATION
# ========================================
cd /workspaces/EE200
pip install -r requirements.txt

# ========================================
# START INTERACTIVE APP
# ========================================
streamlit run ss.py
# Opens at http://localhost:8501

# ========================================
# RUN DEMO WITH SYNTHETIC AUDIO
# ========================================
python demo.py

# ========================================
# PYTHON EXAMPLES
# ========================================

from project import MusicFingerprinter
import matplotlib.pyplot as plt

# Initialize
fp = MusicFingerprinter()

# Load audio
audio, sr = fp.load_audio("song.wav")

# Compute and plot spectrogram
frequencies, times, magnitude = fp.plot_spectrogram(audio, sr)
plt.show()

# Find peaks
peaks = fp.find_peaks(magnitude, frequencies, threshold_db=10)

# Plot constellation
fp.plot_constellation(magnitude, frequencies, times, peaks)
plt.show()

# Create fingerprints
pairs = fp.create_fingerprint_pairs(peaks, frequencies, times)
singles = fp.create_single_peak_fingerprints(peaks, frequencies, times)

print(f"Found {len(peaks)} peaks")
print(f"Created {len(pairs)} peak pair fingerprints")
print(f"Created {len(singles)} single peak fingerprints")

# Build database from directory
database = fp.build_database("audio_files/", use_pairs=True)
print(f"Database: {len(database)} songs")

# Match query
query_audio, query_sr = fp.load_audio("query.wav")
results = fp.match_query(query_audio, query_sr, database, use_pairs=True)

# Show results
for song_name in sorted(results.keys(), 
                        key=lambda s: results[s]['score'], 
                        reverse=True)[:3]:
    score = results[song_name]['score']
    print(f"{song_name}: {score} matches")

# ========================================
# TESTING WITH NOISE
# ========================================

import numpy as np
from scipy import signal

# Add noise to query
snr_db = 10
noise = np.random.normal(0, 1, len(query_audio))
signal_power = np.mean(query_audio ** 2)
noise_power = signal_power / (10 ** (snr_db / 10))
noise = noise / np.sqrt(np.mean(noise ** 2)) * np.sqrt(noise_power)
noisy = np.clip(query_audio + noise, -1, 1)

# Test with noise
results_noisy = fp.match_query(noisy, query_sr, database)

# ========================================
# TESTING WITH PITCH SHIFT
# ========================================

# Pitch shift ±5% (time stretch)
factor = 1.05  # 5% pitch shift
stretched = signal.resample(query_audio, int(len(query_audio) / factor))

# Test with pitch shift
results_pitch = fp.match_query(stretched, query_sr, database)

# ========================================
# KEY VARIABLES TO ADJUST
# ========================================

# Fingerprinter parameters
fp = MusicFingerprinter(
    target_sr=22050,        # Sample rate (default: 22050)
    n_fft=4096,             # FFT size (default: 4096)
                            #   - Larger = better frequency resolution
                            #   - Smaller = better time resolution
    hop_length=512,         # Samples between frames (default: 512)
                            #   - Smaller = more time precision
    freq_min=40,            # Minimum frequency Hz (default: 40)
    freq_max=8000           # Maximum frequency Hz (default: 8000)
)

# Peak detection
peaks = fp.find_peaks(magnitude, frequencies, 
                      threshold_db=10,           # Adjust: 5-20
                      neighborhood_size=10)     # Adjust: 5-20

# Fingerprinting
pairs = fp.create_fingerprint_pairs(peaks, frequencies, times,
                                    anchor_gap=5,         # Look ahead N frames
                                    max_time_gap=50)      # Max frame gap

singles = fp.create_single_peak_fingerprints(peaks, frequencies, times,
                                             time_resolution=5)  # Quantization

# ========================================
# REPORT CHECKLIST
# ========================================

Q3A - SONIC SIGNATURES:
☐ Plot DFT magnitude (full song)
☐ Plot spectrogram (different window sizes)
☐ Explain time vs frequency resolution
☐ Plot constellation (peaks on spectrogram)
☐ Show fingerprint examples
☐ Show database structure
☐ Show matching results (query → best match)
☐ Compare pairs vs singles (same query, both methods)
☐ Explain why pairs are better
☐ Noise robustness test (graph or table)
☐ Pitch shift robustness test (graph or table)
☐ Explain why pitch shifts fail
☐ Suggest one improvement

Q3B - SIGNALS TO SOFTWARE:
☐ Show app database builder interface
☐ Show query upload interface
☐ Show results with spectrogram
☐ Show results with constellation
☐ Show match scores visualization
☐ Demonstrate offset histogram
☐ Show analysis/insights tab
☐ Document intermediate steps shown

# ========================================
# COMMON ISSUES & FIXES
# ========================================

No peaks found?
  → Reduce threshold_db (try 5 instead of 10)
  → Check that audio is loud enough

No matches?
  → Build database first (in app tab 1)
  → Check database was saved (view statistics)
  → Try songs from database as query first

Pitch shift test gives zero matches?
  → This is expected! Document as limitation
  → Explain why frequencies all change
  → Suggest chroma features as fix

App crashes on file upload?
  → Check file is .wav format
  → Verify file is not corrupted
  → Try loading same file locally first

# ========================================
# VISUALIZATION TIPS
# ========================================

# Spectrogram with peaks
fig, ax = plt.subplots(figsize=(12, 6))
pcm = ax.pcolormesh(times, frequencies, magnitude, cmap='viridis', alpha=0.8)
if peaks:
    peak_freqs = frequencies[np.array([p[0] for p in peaks])]
    peak_times = times[np.array([p[1] for p in peaks])]
    ax.scatter(peak_times, peak_freqs, c='red', s=100, marker='o',
              edgecolors='white', linewidth=1, alpha=0.9, label='Peaks')
ax.set_ylabel('Frequency (Hz)')
ax.set_xlabel('Time (s)')
ax.set_title('Song Spectrogram with Peak Constellation')
ax.set_ylim([40, 8000])
plt.colorbar(pcm, label='Magnitude (dB)')
plt.legend()
plt.tight_layout()
plt.show()

# Comparison plots
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Short window
axes[0].pcolormesh(times_short, freqs_short, mag_short, cmap='viridis')
axes[0].set_title('Short Window - Better Time Resolution')

# Long window
axes[1].pcolormesh(times_long, freqs_long, mag_long, cmap='viridis')
axes[1].set_title('Long Window - Better Frequency Resolution')

for ax in axes:
    ax.set_ylabel('Frequency (Hz)')
    ax.set_xlabel('Time (s)')
    ax.set_ylim([40, 8000])

plt.tight_layout()
plt.show()

# ========================================
# FURTHER READING
# ========================================

The Shazam algorithm paper (2003):
"An Industrial-Strength Audio Search Algorithm"
Wang, A. (2003). IEEE Signal Processing Magazine

Key concepts:
- Time-frequency analysis (STFT)
- Peak detection in 2D (local maxima)
- Hash-based fingerprinting
- Offset histogram matching
- Robustness against compression & noise
