# EE200 - Music Identifier: Sonic Signatures

A Shazam-like music identification system that uses spectral fingerprints to identify songs from audio clips.

## Project Overview

This project implements a complete music identification pipeline inspired by Shazam's technology:

### Q3A: Sonic Signatures (Core Algorithm)
- **Spectrogram Analysis**: Convert time-domain audio to time-frequency representation
- **Peak Detection**: Extract distinctive frequency peaks from spectrograms  
- **Fingerprinting**: Create robust fingerprints using:
  - **Peak Pairs**: Hash combinations of nearby frequency peaks (more selective)
  - **Single Peaks**: Simple frequency-time tuples (baseline)
- **Database Matching**: Store fingerprints and match query clips using offset histograms
- **Robustness Testing**: Evaluate performance under noise and pitch shifts

### Q3B: Signals to Software (Interactive App)
- Built with **Streamlit** for easy interaction
- **Three main tabs**:
  1. **Build Database**: Upload songs and create fingerprint database
  2. **Query & Identify**: Upload a clip and identify matching song
  3. **Analysis & Insights**: Understand how the system works

## Key Features

✨ **Spectrogram Visualization**
- Plot DFT magnitude to see frequency content
- Compare time vs frequency resolution with different window sizes
- Observe how short windows sacrifice frequency resolution for time precision

🌟 **Peak Constellation**
- Identify strongest peaks in spectrogram
- Visualize peaks overlaid on spectrogram
- Understand why peaks form the basis of fingerprints

🔗 **Fingerprinting Strategies**
- Peak pairs: (freq1, freq2, delta_time) - very selective
- Single peaks: (freq, time) - simpler but with false positives
- Compare both approaches to understand tradeoff

🎯 **Matching & Identification**
- Hash-based database lookup
- Offset histogram alignment
- Confidence scoring

🛡️ **Robustness Analysis**
- Noise injection (varying SNR levels)
- Pitch shift testing (tempo changes)
- Explanation of failure modes

## Installation

```bash
# Clone or navigate to the repo
cd /workspaces/EE200

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Run the Interactive App
```bash
streamlit run ss.py
```

The app will open at `http://localhost:8501`

### Workflow

**Step 1: Build Database**
- Navigate to "Build Database" tab
- Upload .wav files for songs you want to identify
- Click "Build Database" to create fingerprint index
- View statistics (songs, total fingerprints, avg per song)

**Step 2: Identify a Song**
- Go to "Query & Identify" tab
- Upload a query .wav clip (can be from any song in database)
- Click "Identify Song"
- View:
  - **Spectrogram**: Time-frequency representation
  - **Constellation**: Peak locations overlaid
  - **Results**: Best match with confidence score
  - **Offset Histogram**: Shows alignment quality
  - **Score Table**: Comparison with all database songs

**Step 3: Understand the System**
- Read "Analysis & Insights" tab for:
  - Time vs frequency resolution tradeoff
  - Why peak pairs beat single peaks
  - Robustness characteristics
  - Why pitch shifts defeat the system
  - Suggested improvements

## Technical Details

### Spectrogram Parameters
```python
FFT Size (n_fft): 4096          # Determines frequency resolution
Hop Length: 512 samples         # Determines time resolution  
Frequency Range: 40-8000 Hz     # Human speech/music range
Peak Threshold: 10 dB above background
```

### Fingerprinting
```python
# Peak Pairs: (f1_quantized, f2_quantized, delta_t_quantized)
- Frequency quantization: 25 Hz
- Time quantization: 1 frame (~23 ms)
- Anchor gap: Look ahead 5 frames
- Max time gap: 50 frames

# Single Peaks: (freq_quantized, time_quantized)
- Time resolution: 5 frames
```

### Matching Algorithm
1. Extract fingerprints from query audio
2. Hash each fingerprint
3. Look up hashes in database
4. Count matches and build offset histogram
5. Peak offset indicates correct alignment
6. Score = number of matching fingerprints

## Observations & Analysis

### Time vs Frequency Resolution
```
Short Window (512 samples):
  ✅ Good time resolution (precise note onsets)
  ❌ Poor frequency resolution (blurred notes)

Long Window (4096 samples):
  ❌ Poor time resolution (slow to detect changes)
  ✅ Good frequency resolution (sharp frequency peaks)
```

### Peak Pairs vs Single Peaks
```
Single Peaks:
  - Can appear in many songs
  - High false positive rate
  - Scattered matches even for wrong songs

Peak Pairs:
  - Unique frequency combinations
  - Much lower false positive rate
  - Correct song has all pairs aligned at same offset
  - Wrong song has scattered random matches
```

### Robustness Issues

**Handles Well:**
- Background noise (SNR > 10 dB)
- Volume changes
- Small tempo variations

**Fails Against:**
- Pitch shifts (even ±2% fails!)
- Audio compression (MP3 artifacts)
- Significant time stretching

**Why Pitch Shifts Fail:**
1. Song pitch shifted: all frequencies multiplied by α
2. Peak pair (f₁, f₂, Δt) becomes (αf₁, αf₂, Δt)
3. Hash value completely different
4. No matches found in database
5. Human ear still hears same melody, but computer lost it!

## Suggested Improvements

### 1. Chroma Features (Pitch-Invariant)
- Track relative frequency ratios instead of absolute frequencies
- Makes system invariant to pitch shifts
- Captures musical intervals, not absolute notes

### 2. Onset Detection
- Focus on attack times of notes
- Robust to pitch shifts and time stretches
- More musically meaningful

### 3. Temporal Normalization  
- Normalize fingerprints relative to tempo
- Handles tempo variations gracefully

### 4. Hybrid Fingerprints
- Combine multiple features:
  - Spectral peaks
  - MFCC (Mel-Frequency Cepstral Coefficients)
  - Chromagram (pitch-based)
- Redundancy makes matching more robust

### 5. Probabilistic Matching
- Replace binary hashing with probabilistic models
- Soft matching scores instead of binary matches
- Better handling of noisy/degraded audio

## File Structure

```
.
├── project.py          # Core MusicFingerprinter class
│                       # - Spectrogram computation
│                       # - Peak detection
│                       # - Fingerprint creation
│                       # - Database building
│                       # - Query matching
│                       # - Robustness testing
├── ss.py               # Streamlit interactive app
│                       # - Database builder UI
│                       # - Query interface
│                       # - Visualization
│                       # - Analysis tab
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## API Reference

### MusicFingerprinter Class

```python
# Initialize
fingerprinter = MusicFingerprinter(
    target_sr=22050,           # Sample rate
    n_fft=4096,                # FFT window size
    hop_length=512,            # Samples between frames
    freq_min=40,               # Min frequency (Hz)
    freq_max=8000              # Max frequency (Hz)
)

# Load audio
audio, sr = fingerprinter.load_audio("song.wav")

# Compute spectrogram
freqs, times, magnitude = fingerprinter.compute_spectrogram(audio, sr)

# Find peaks
peaks = fingerprinter.find_peaks(magnitude, freqs, threshold_db=10)

# Create fingerprints
pairs = fingerprinter.create_fingerprint_pairs(peaks, freqs, times)
singles = fingerprinter.create_single_peak_fingerprints(peaks, freqs, times)

# Build database
database = fingerprinter.build_database("audio_dir/", use_pairs=True)

# Match query
results = fingerprinter.match_query(query_audio, query_sr, database)
```

## Dependencies

- **streamlit**: Interactive web app
- **numpy**: Numerical computing
- **scipy**: Signal processing (spectrogram, STFT, filtering)
- **matplotlib**: Visualization
- **pandas**: Data handling
- **seaborn**: Enhanced visualization

## Notes for Report

Your report should include:

1. **Spectrograms**
   - Full song spectrogram (showing all frequencies)
   - Comparison of short vs long window sizes
   - Analysis of time vs frequency resolution tradeoff

2. **Constellation Plots**
   - Spectrogram with peak overlay
   - Show how peaks form the fingerprint

3. **Matching Results**
   - Database song spectra/constellations
   - Query clip matching to best match
   - Offset histogram showing alignment

4. **Comparison: Pairs vs Singles**
   - Side-by-side results from same query
   - Explanation of why pairs are more decisive

5. **Robustness Experiments**
   - Noise test: SNR vs recognition success
   - Pitch shift test: percentage change vs success
   - Written analysis of what you observe

6. **Explanations**
   - Why pitch shifts defeat the system
   - Why spectrogram gives time information while DFT doesn't
   - Why peak pairs are superior to single peaks
   - Proposed improvement and its advantages

- Python 3.8+
- See requirements.txt for all dependencies

## License

MIT