#!/usr/bin/env python3
"""
Ultra-fast Q3A analysis - optimized for speed with real audio
Uses 2 songs, samples peaks for visualization, focuses on essential outputs
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
import soundfile as sf
import time

# Configuration
SONGS_DIR = "songs_wav"
TEST_SONGS = ["Hey Jude.wav", "Yesterday.wav"]
SR = 22050
ANALYSIS_START = 30  # Start at 30s (skip intro)
ANALYSIS_DUR = 30    # Analyze only 30s (faster)

print("="*80)
print("MUSIC IDENTIFIER - ULTRA-FAST ANALYSIS (Sampled Peaks)")
print("="*80)

# ============================================================================
# PART 1: Load audio segments
# ============================================================================
print("\nPART 1: Loading Test Songs (30s segments starting at 30s)")
print("-" * 80)

audio_data = {}
for song in TEST_SONGS:
    path = os.path.join(SONGS_DIR, song)
    if os.path.exists(path):
        data, sr_loaded = sf.read(path)
        if len(data.shape) > 1:  # stereo
            data = data[:, 0]
        # Extract 30s segment starting at 30s
        start_sample = ANALYSIS_START * sr_loaded
        end_sample = start_sample + (ANALYSIS_DUR * sr_loaded)
        segment = data[start_sample:end_sample].astype(float)
        segment = segment / (np.max(np.abs(segment)) + 1e-10)
        audio_data[song] = segment
        print(f"  ✓ {song}: {len(segment)} samples (~{len(segment)/sr_loaded:.1f}s)")
    else:
        print(f"  ✗ {song}: NOT FOUND")

# ============================================================================
# PART 2: Fast spectrogram with single FFT size
# ============================================================================
print("\nPART 2: Spectrogram Analysis (FFT size 4096)")
print("-" * 80)

fig, axes = plt.subplots(1, 2, figsize=(16, 5))

for idx, (song, audio) in enumerate(audio_data.items()):
    # Compute STFT
    f, t, Sxx = signal.spectrogram(
        audio,
        fs=SR,
        nperseg=4096,
        noverlap=2048,
        nfft=4096,
        window='hann'
    )
    
    # Convert to dB
    Sxx_db = 10 * np.log10(np.abs(Sxx) + 1e-10)
    
    # Plot
    im = axes[idx].pcolormesh(t, f[:500], Sxx_db[:500], shading='gouraud', cmap='viridis')
    axes[idx].set_ylabel('Frequency (Hz)')
    axes[idx].set_xlabel('Time (s)')
    axes[idx].set_title(f'{song} - Spectrogram')
    plt.colorbar(im, ax=axes[idx], label='Power (dB)')

plt.tight_layout()
plt.savefig("Q3A_spectrograms.png", dpi=150, bbox_inches='tight')
print("✓ Saved: Q3A_spectrograms.png")
plt.close()

# ============================================================================
# PART 3: Fast Peak Detection (with sampling for visualization)
# ============================================================================
print("\nPART 3: Peak Detection & Constellation (Sampled for Speed)")
print("-" * 80)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))

for idx, (song, audio) in enumerate(audio_data.items()):
    # Compute spectrogram
    f, t, Sxx = signal.spectrogram(
        audio, fs=SR, nperseg=4096, noverlap=2048, window='hann'
    )
    
    # Normalize to 0-1
    Sxx_norm = (np.abs(Sxx) - np.min(np.abs(Sxx))) / (np.max(np.abs(Sxx)) - np.min(np.abs(Sxx)) + 1e-10)
    
    # Find peaks with lower threshold for faster detection
    background = signal.medfilt2d(Sxx_norm, kernel_size=11)
    diff = Sxx_norm - 0.8 * background
    peaks = (diff > 0.05) & (Sxx_norm > 0.1)  # Threshold for speed
    
    # Get peak coordinates
    peak_indices = np.where(peaks)
    n_peaks = len(peak_indices[0])
    
    # SAMPLE peaks for visualization (every Nth peak)
    sample_rate = max(1, n_peaks // 500)  # Keep ~500 peaks for visualization
    peak_freq_indices = peak_indices[0][::sample_rate]
    peak_time_indices = peak_indices[1][::sample_rate]
    peak_freqs = f[peak_freq_indices]
    peak_times = t[peak_time_indices]
    
    # Plot spectrogram with overlaid peaks
    Sxx_db = 10 * np.log10(np.abs(Sxx) + 1e-10)
    im = axes[idx].pcolormesh(t, f[:500], Sxx_db[:500], shading='gouraud', cmap='viridis', alpha=0.8)
    
    # Overlay sampled peaks (only show peaks in frequency range < 500 Hz)
    mask = peak_freqs < 500
    axes[idx].scatter(peak_times[mask], peak_freqs[mask], c='red', s=20, marker='x', alpha=0.6)
    
    axes[idx].set_ylabel('Frequency (Hz)')
    axes[idx].set_xlabel('Time (s)')
    axes[idx].set_title(f'{song} - Peaks (sampled: {len(peak_times)} / {n_peaks} total)')
    plt.colorbar(im, ax=axes[idx], label='Power (dB)')
    
    print(f"  {song}: {n_peaks} peaks detected (showing {len(peak_times)} sampled)")

plt.tight_layout()
plt.savefig("Q3A_constellation.png", dpi=150, bbox_inches='tight')
print("✓ Saved: Q3A_constellation.png")
plt.close()

# ============================================================================
# PART 4: Simplified Analysis Metrics
# ============================================================================
print("\nPART 4: Analysis Metrics")
print("-" * 80)

# Create a summary figure with metrics
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Metric 1: Energy over time
ax = axes[0, 0]
for song, audio in audio_data.items():
    frame_energy = np.array([
        np.sum(audio[i:i+2048]**2) 
        for i in range(0, len(audio)-2048, 2048)
    ])
    time_axis = np.arange(len(frame_energy)) * 2048 / SR
    ax.plot(time_axis, 10*np.log10(frame_energy + 1e-10), label=song, linewidth=2)
ax.set_xlabel('Time (s)')
ax.set_ylabel('Energy (dB)')
ax.set_title('Frame Energy Over Time')
ax.legend()
ax.grid(True, alpha=0.3)

# Metric 2: Spectrogram frequency content (averaged)
ax = axes[0, 1]
for song, audio in audio_data.items():
    f, t, Sxx = signal.spectrogram(audio, fs=SR, nperseg=4096, noverlap=2048, window='hann')
    mean_power = np.mean(np.abs(Sxx), axis=1)
    ax.semilogy(f[:500], mean_power[:500], label=song, linewidth=2)
ax.set_xlabel('Frequency (Hz)')
ax.set_ylabel('Average Power')
ax.set_title('Average Frequency Content')
ax.legend()
ax.grid(True, alpha=0.3, which='both')

# Metric 3: Waveform
ax = axes[1, 0]
for song, audio in audio_data.items():
    time = np.arange(len(audio)) / SR
    ax.plot(time, audio, label=song, linewidth=0.5, alpha=0.7)
ax.set_xlabel('Time (s)')
ax.set_ylabel('Amplitude')
ax.set_title('Waveform Comparison')
ax.legend()
ax.grid(True, alpha=0.3)

# Metric 4: Summary info
ax = axes[1, 1]
ax.axis('off')
info_text = "ANALYSIS SUMMARY\n" + "="*30 + "\n"
for song, audio in audio_data.items():
    rms = np.sqrt(np.mean(audio**2))
    peak = np.max(np.abs(audio))
    crest_factor = peak / rms if rms > 0 else 0
    info_text += f"\n{song}:\n"
    info_text += f"  Duration: {len(audio)/SR:.1f}s\n"
    info_text += f"  RMS: {rms:.4f}\n"
    info_text += f"  Peak: {peak:.4f}\n"
    info_text += f"  Crest Factor: {crest_factor:.2f}dB\n"

ax.text(0.1, 0.9, info_text, transform=ax.transAxes, 
        fontsize=11, verticalalignment='top', family='monospace',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig("Q3A_analysis_metrics.png", dpi=150, bbox_inches='tight')
print("✓ Saved: Q3A_analysis_metrics.png")
plt.close()

# ============================================================================
# PART 5: Noise Robustness Test
# ============================================================================
print("\nPART 5: Noise Robustness Test")
print("-" * 80)

fig, axes = plt.subplots(1, 1, figsize=(12, 8))

# Use first song for noise test
test_audio = audio_data[TEST_SONGS[0]]
snr_levels = [20, 10, 5, 0]
noise_samples = []

for snr_db in snr_levels:
    # Generate white noise
    noise = np.random.randn(len(test_audio))
    noise = noise / np.std(noise)
    
    # Calculate signal power and scale noise
    signal_power = np.mean(test_audio**2)
    snr_linear = 10**(snr_db/10)
    noise_power = signal_power / snr_linear
    noise = noise * np.sqrt(noise_power)
    
    # Mix
    noisy_signal = test_audio + noise
    noise_samples.append((snr_db, noisy_signal))

# Plot spectrograms of noisy versions
for idx, (snr_db, noisy) in enumerate(noise_samples):
    ax = plt.subplot(2, 2, idx+1)
    f, t, Sxx = signal.spectrogram(noisy, fs=SR, nperseg=4096, noverlap=2048, window='hann')
    Sxx_db = 10 * np.log10(np.abs(Sxx) + 1e-10)
    im = ax.pcolormesh(t, f[:500], Sxx_db[:500], shading='gouraud', cmap='viridis')
    ax.set_ylabel('Frequency (Hz)')
    ax.set_xlabel('Time (s)')
    ax.set_title(f'SNR: {snr_db} dB')
    plt.colorbar(im, ax=ax)

plt.suptitle(f'Noise Robustness Test - {TEST_SONGS[0]}', fontsize=14, y=1.00)
plt.tight_layout()
plt.savefig("Q3A_noise_robustness.png", dpi=150, bbox_inches='tight')
print("✓ Saved: Q3A_noise_robustness.png")
plt.close()

# ============================================================================
# PART 6: Pitch Shift Robustness Test
# ============================================================================
print("\nPART 6: Pitch Shift Robustness Test")
print("-" * 80)

fig, axes = plt.subplots(1, 1, figsize=(12, 8))

test_audio = audio_data[TEST_SONGS[0]]
pitch_shifts = [-5, -2, 0, 2]  # semitones (4 plots only)

for idx, semitones in enumerate(pitch_shifts):
    if semitones == 0:
        shifted = test_audio
        title_text = 'Original'
    else:
        # Simple pitch shift using frequency domain
        shift_factor = 2 ** (semitones / 12)
        # Resample by duplication/skipping
        if shift_factor > 1:  # Pitch down (slower)
            indices = np.arange(0, len(test_audio), 1/shift_factor).astype(int)
            indices = indices[indices < len(test_audio)]
        else:  # Pitch up (faster)
            indices = np.arange(0, len(test_audio), shift_factor).astype(int)
        shifted = test_audio[indices]
        # Pad/trim to original length
        if len(shifted) < len(test_audio):
            shifted = np.pad(shifted, (0, len(test_audio)-len(shifted)))
        else:
            shifted = shifted[:len(test_audio)]
        title_text = f'{semitones:+d} semitones'
    
    ax = plt.subplot(2, 2, idx+1)
    f, t, Sxx = signal.spectrogram(shifted, fs=SR, nperseg=4096, noverlap=2048, window='hann')
    Sxx_db = 10 * np.log10(np.abs(Sxx) + 1e-10)
    im = ax.pcolormesh(t, f[:500], Sxx_db[:500], shading='gouraud', cmap='viridis')
    ax.set_ylabel('Frequency (Hz)')
    ax.set_xlabel('Time (s)')
    ax.set_title(title_text)
    plt.colorbar(im, ax=ax)

plt.suptitle(f'Pitch Shift Robustness - {TEST_SONGS[0]}', fontsize=14, y=1.00)
plt.tight_layout()
plt.savefig("Q3A_pitch_robustness.png", dpi=150, bbox_inches='tight')
print("✓ Saved: Q3A_pitch_robustness.png")
plt.close()

# ============================================================================
# COMPLETION
# ============================================================================
print("\n" + "="*80)
print("ANALYSIS COMPLETE!")
print("="*80)
print("\nGenerated Files:")
print("  • Q3A_spectrograms.png - Spectrogram comparison")
print("  • Q3A_constellation.png - Peak detection visualization")
print("  • Q3A_analysis_metrics.png - Detailed metrics analysis")
print("  • Q3A_noise_robustness.png - Noise robustness test (SNR 20/10/5/0 dB)")
print("  • Q3A_pitch_robustness.png - Pitch shift robustness (±5%, ±2%, 0%)")
print("\n" + "="*80)
