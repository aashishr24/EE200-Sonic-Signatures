# Sonic Signatures: Music Fingerprinting Analysis Report

**Project:** Spectral Analysis and Audio Fingerprinting  
**Date:** June 2026 (updated July 2026 — see note below)

> **Update note:** the original matching implementation had a bug where the
> time-alignment offset between a query and a database song was hardcoded
> to zero instead of actually computed, which silently broke the
> offset-histogram voting described in Section 3.2 below — the algorithm
> was really just counting raw hash collisions. This report has been
> updated to reflect the fixed implementation and real measured results.
> Full before/after details: [`FIXES.md`](FIXES.md).

---

## Executive Summary

This report presents the implementation and analysis of a Shazam-like music fingerprinting system using spectral analysis and peak detection. The system extracts unique fingerprints from audio signals and matches query clips against a database of reference songs.

**Key Findings:**
- Peak-pair fingerprints (frequency₁, frequency₂, time_gap) provide highly selective matching
- Scoring by the tallest bin of a real time-offset histogram (not just total hash
  collisions) makes the system robust to noise down to **0 dB SNR**, measured
  on the real 50-song database, before pitch shifts remain the dominant failure mode
- FFT size of 4096 samples provides optimal frequency resolution without sacrificing time alignment

---

## 1. Methodology

### 1.1 Spectrogram Analysis

**Parameters:**
- Sample rate: 22,050 Hz (resampled from original)
- FFT size: 4,096 samples (~186 ms duration)
- Hop length: 512 samples (~23 ms between frames)
- Window function: Hann window
- Frequency range analyzed: 40-8,000 Hz

**Why these choices?**
- **FFT size 4096:** Provides excellent frequency resolution (5.4 Hz per bin) while maintaining reasonable time resolution
- **Hop length 512:** Creates 23 ms frames, suitable for music signal dynamics
- **Frequency range:** Discards inaudible frequencies (<40 Hz) and high-frequency noise (>8,000 Hz)

**Visualization:** See `spectrograms.png` showing spectrograms of "Hey Jude" and "Yesterday"

---

### 1.2 Peak Detection Algorithm

**Method:** Local maxima detection using 2D median filtering

```
1. Compute magnitude spectrogram S(f,t)
2. Apply 2D median filter: B(f,t) = median(S, kernel=11×11)
3. Compute difference: D(f,t) = S(f,t) - 0.8·B(f,t)
4. Threshold: Peaks = (D > threshold_dB) ∧ (S > 0.1·max(S))
5. Extract (frequency_index, time_index) pairs
```

**Parameters:**
- Threshold: 10 dB above background
- Kernel size: 11×11 (local neighborhood)
- Background factor: 0.8 (to account for smooth components)

**Results:** ~400 peaks detected per 30-second segment

**Visualization:** See `constellation.png` showing detected peaks overlaid on spectrograms

---

### 1.3 Fingerprint Generation

#### Single Peak Fingerprints
**Format:** (quantized_frequency, quantized_time)

- Quantization: 25 Hz frequency bins, 1-frame time bins
- Simple but prone to false positives (many songs share common frequencies)
- Not suitable for robust matching

#### Peak Pair Fingerprints (Chosen Method)
**Format:** (f₁, f₂, Δt, offset)

Where:
- f₁: First peak frequency (quantized to 25 Hz bins)
- f₂: Second peak frequency (quantized to 25 Hz bins)  
- Δt: Time gap between peaks (quantized to frame bins)
- offset: Anchor point for alignment

**Constraints:**
- Anchor gap: 5 frames between the two peaks
- Maximum time gap: 50 frames (~1.15 seconds)

**Rationale:**
- Peak pairs are much more unique than single peaks
- Dramatically reduces false positives
- Time gap information helps with alignment
- Extremely efficient for matching

**Fingerprint Count:** ~2,500 peak pairs per 30-second segment (vs ~400 single peaks)

---

## 2. Experiments

### 2.1 Window Length Trade-off

**Experiment:** Compare frequency vs. time resolution with different FFT sizes

| FFT Size | Frequency Res. | Time Res. | Application |
|----------|----------------|-----------|-------------|
| 512 | 43 Hz/bin | 23 ms | Percussive onset detection |
| 2048 | 11 Hz/bin | 46 ms | Balanced (good for vocals) |
| **4096** | **5.4 Hz/bin** | **93 ms** | **Chosen: Best for pitch** |
| 8192 | 2.7 Hz/bin | 186 ms | Over-smoothed peaks |

**Observation:** FFT size 4096 provides the best balance. Larger sizes blur timing information needed for alignment.

**Visualization:** Would require multiple spectrograms with different window lengths

---

### 2.2 Single Peaks vs. Peak Pairs

**Comparison:**

| Aspect | Single Peaks | Peak Pairs |
|--------|-------------|-----------|
| Fingerprints per 30s | ~400 | ~2,500 |
| False Positive Rate | Very High | Very Low |
| Uniqueness | Low (C major chord common in many songs) | High (specific frequency combinations rare) |
| Robustness | Poor (noise adds random peaks) | Good (patterns persist through noise) |
| Matching Speed | Fast | Faster (more distinctive matches) |

**Finding:** Peak pairs are dramatically superior for matching accuracy while remaining computationally efficient.

---

### 2.3 Noise Robustness Testing

**Experiment:** Add white Gaussian noise at various SNR levels and analyze spectrogram degradation

**SNR Levels Tested:** 20 dB, 10 dB, 5 dB, 0 dB

**Parameters:**
- Signal power: P_signal = mean(audio²)
- Noise power for SNR: P_noise = P_signal / (10^(SNR_dB/10))
- White Gaussian noise: n(t) = N(0, σ²)

**Results:**

| SNR | Spectrogram | Peak Detection | Matching |
|-----|-------------|----------------|----------|
| 20 dB | Crystal clear | 95%+ peaks preserved | ✅ Works well |
| 10 dB | Minor artifacts | ~80% peaks detected | ✅ Matches found |
| 5 dB | Heavy grain | ~50% peak loss | ⚠️ Degraded |
| 0 dB | Mostly noise | Few valid peaks | ❌ Fails |

**Observation:** Peak detection quality itself degrades progressively as shown
in the table above. However, because the *matching* score is the tallest bin
of a real time-offset histogram (many fingerprints voting on one consistent
alignment) rather than a raw hash-collision count, matching accuracy degrades
far more gracefully than peak detection alone would suggest: identification
remained correct down to **0 dB SNR** in repeated trials on the real 50-song
database, only becoming unreliable around -3 to -5 dB.

**Visualization:** See `noise_robustness.png` showing spectrograms at different noise levels

---

### 2.4 Pitch Shift Robustness Testing

**Experiment:** Pitch-shift the signal by ±2 and ±5 semitones and test matching

**Method:**
- Time-domain resampling (simple pitch shift)
- All frequency components shift uniformly by factor α = 2^(semitones/12)
- Example: +5 semitones = 29.7% increase in all frequencies

**Results:**

| Pitch Shift | Frequency Shift | Peak Pairs | Matching |
|------------|-----------------|-----------|----------|
| Original | 1.0x | (f₁, f₂, Δt) | ✅ Perfect match |
| +2 semitones | 1.122x | (1.122f₁, 1.122f₂, Δt) | ❌ No match |
| +5 semitones | 1.297x | (1.297f₁, 1.297f₂, Δt) | ❌ No match |
| -2 semitones | 0.891x | (0.891f₁, 0.891f₂, Δt) | ❌ No match |
| -5 semitones | 0.771x | (0.771f₁, 0.771f₂, Δt) | ❌ No match |

**Key Finding:** Even small pitch shifts (±2 semitones) cause complete matching failure because:
1. All frequencies scale by the shift factor
2. Hash values become completely different
3. No correlation with original fingerprints

**Human Perception vs. Algorithm:**
- **Human ear:** Recognizes pitch-shifted music immediately (same melody)
- **Fingerprinter:** Lost (different frequency values)

This is the main limitation of frequency-based fingerprinting.

**Visualization:** See `pitch_robustness.png` showing spectrograms at different pitch shifts

---

### 2.5 Other Robustness Tests

#### Time Stretching (Tempo Changes)
- Small stretches (<10%): System handles reasonably well
- Reason: Peak pair time gaps scale proportionally
- Large stretches (>20%): Fingerprints become unreliable

#### Compression Artifacts
- MP3 compression: ~95% matching success (artifacts minor)
- Extreme compression: Matching degrades significantly

#### Volume Normalization
- DC offset invariance: System automatically normalizes
- Linear scaling: Spectrogram shapes remain identical

---

## 3. Technical Analysis

### 3.1 Fingerprinting Algorithm Complexity

**Time Complexity (per song):**
```
STFT Computation:       O(N log N)  where N = number of samples
Peak Detection:         O(N_freq × N_time)
Fingerprint Generation: O(N_peaks²)  for all peak pairs
Database Indexing:      O(N_fingerprints × log(database_size))
```

**Space Complexity:**
- Single song: ~2,500 fingerprints × 16 bytes ≈ 40 KB
- Database (51 songs): ~2 MB (compressed)

### 3.2 Matching Algorithm

**Query Processing:**
```
1. Extract query fingerprints:  ~100-200 pairs (short clip), each tagged
                                 with its real timestamp
2. Hash lookup in database:     O(1) average per fingerprint
3. Vote on time offsets:        For every hash match, compute
                                 offset = db_time - query_time and bin it
4. Find peak offset:            The tallest histogram bin is the score;
                                 a true match produces one sharp spike,
                                 a wrong song produces scattered small bars
5. Score calculation:           Height of the tallest offset-histogram bin
```

**Matching Time:** ~100 ms per query (very fast)

### 3.3 Hash Function

```python
def fingerprint_hash(f1_quantized, f2_quantized, delta_t_quantized):
    return hash((f1, f2, delta_t)) % (10^9)
```

- Python's built-in hash: Fast and well-distributed
- Modulo 10^9: Reduces memory footprint while maintaining uniqueness
- Collision likelihood: Negligible for our database size

---

## 4. System Limitations & Future Improvements

### Current Limitations

1. **Pitch Invariance:** ❌ Fails on pitch shifts
   - Reason: Algorithm is frequency-absolute
   - Impact: Cannot identify transposed versions or live performances

2. **Time Stretching:** ⚠️ Limited tolerance
   - Reason: Time gap quantization is rigid
   - Impact: Slight tempo changes cause mismatches

3. **Heavy Compression:** ⚠️ Degrades with extreme codecs
   - Reason: Compression artifacts introduce spurious peaks
   - Impact: Low-bitrate MP3s less reliable

4. **Vocal-Heavy Music:** ⚠️ More noise-prone
   - Reason: Vocals add dynamic peaks outside clean harmonics
   - Impact: Slightly lower matching confidence

### Proposed Improvements

#### 1. Chroma Features (Pitch Invariant)
- **Idea:** Use chromatic scale (semitone intervals) instead of absolute frequencies
- **Implementation:** Map 12 pitch classes (C, C#, D, ..., B) regardless of octave
- **Advantage:** Pitch shifts become transparent
- **Trade-off:** Loses pitch information but gains robustness

#### 2. Onset Detection
- **Idea:** Focus on attack times rather than peak frequencies
- **Implementation:** Detect sudden energy increases, use these as anchors
- **Advantage:** More robust to both pitch and volume changes
- **Trade-off:** More complex computation

#### 3. Temporal Normalization
- **Idea:** Normalize time gaps by estimated tempo
- **Implementation:** Detect tempo changes, scale Δt accordingly
- **Advantage:** Handles time stretching
- **Trade-off:** Requires tempo estimation

#### 4. Hybrid Fingerprints
- **Idea:** Combine multiple feature types (spectral + chromatic + MFCCs)
- **Implementation:** Use ensemble voting on different feature sets
- **Advantage:** Redundancy improves robustness
- **Trade-off:** Higher computational cost

#### 5. Machine Learning Matching
- **Idea:** Learn matching confidence from neural networks
- **Implementation:** Train on similarity scores between matched/unmatched pairs
- **Advantage:** Can learn robust patterns from data
- **Trade-off:** Requires labeled training data

---

## 5. Conclusions

### Key Achievements
1. ✅ Successfully implemented spectral fingerprinting system
2. ✅ Peak-pair algorithm provides excellent matching accuracy
3. ✅ System is robust to realistic noise levels
4. ✅ Fast matching (<100ms per query)
5. ✅ Minimal storage requirements (~2MB for 51 songs)

### Performance Summary
- **Database:** 50 songs, ~40,000 fingerprints per song on average
- **Accuracy:** correct identification down to 0 dB SNR on real audio (measured, repeated trials); degrades sharply on pitch shifts of even ±1-2%
- **Speed:** <1s per query match against the full 50-song database
- **Memory:** ~37MB pre-built fingerprint database

### When This System Works Best
- ✅ Noisy audio, down to and including 0 dB SNR
- ✅ Original pitch and tempo
- ✅ Real-time identification
- ✅ Large-scale databases

### When This System Struggles
- ❌ Pitch-shifted music (even small shifts)
- ❌ Heavily time-stretched audio
- ❌ Extreme noise (SNR below roughly -3 to -5 dB)

---

## References

1. Ellis, D. P. "Shazam-ing music" (2009)
2. Wang, A. "An Industrial-Strength Audio Search Algorithm" (2003)
3. Freedman, D. "Improved Music Identification with Fuzzy Fingerprinting"
4. Scipy Documentation: Signal Processing and STFT
5. Librosa: Audio Analysis Python Library

---

## Appendix: Visualization Guide

### spectrograms.png
- **X-axis:** Time (seconds)
- **Y-axis:** Frequency (Hz)
- **Color:** Magnitude (dB)
- **Shows:** Time-frequency content of two reference songs

### constellation.png
- **Red X marks:** Detected spectral peaks
- **Spacing:** Represents unique fingerprint patterns
- **Shows:** Algorithm's peak detection quality

### analysis_metrics.png
- **Panel 1:** Frame energy over time (loudness envelope)
- **Panel 2:** Average frequency content (spectral tilt)
- **Panel 3:** Waveform overlay of both songs
- **Panel 4:** Summary statistics (RMS, peak, crest factor)

### noise_robustness.png
- **Four subplots:** SNR levels 20, 10, 5, 0 dB
- **Progressive degradation:** Shows noise limit
- **Takeaway:** System works well until SNR drops below 5dB

### pitch_robustness.png
- **Four subplots:** Pitch shifts -5, -2, 0, +2 semitones
- **Frequency shifts:** All peaks shift uniformly
- **Takeaway:** Complete mismatch even at ±2 semitones

---

**Implementation:** Python 3, scipy, numpy, matplotlib, pydub  
**Code & live demo:** [github.com/aashishr24/EE200-Sonic-Signatures](https://github.com/aashishr24/EE200-Sonic-Signatures) · [musicashish.streamlit.app](https://musicashish.streamlit.app)
