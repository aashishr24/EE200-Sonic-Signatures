# Sonic Signatures — Music Identifier

A Shazam-like music identification system that uses spectral fingerprints to identify songs from audio clips.

**🎵 Live demo: [musicashish.streamlit.app](https://musicashish.streamlit.app)**
*(pre-loaded with a 50-song database — try Query & Identify or Batch Mode directly, no setup needed)*

> **Engineering note:** the matching algorithm originally had a subtle bug where
> the time-alignment ("offset") between a query clip and a database song was
> never actually tracked — it was hardcoded to zero, silently reducing the
> whole system to a raw hash-collision counter instead of true Shazam-style
> alignment matching. I found this by testing against real noisy audio (it
> was misidentifying songs at surprisingly mild noise levels), traced it to
> the scoring logic, and fixed it to compute a real per-hash time offset and
> score by the tallest bin in the resulting histogram. That took noise
> robustness from failing at ~25dB SNR up to correct identification down to
> 0dB SNR on the real song database. Full before/after details in
> [`FIXES.md`](FIXES.md).

## Project Overview

This project implements a complete music identification pipeline inspired by Shazam's technology:

### Core Algorithm: Spectral Fingerprinting
- **Spectrogram Analysis**: Convert time-domain audio to time-frequency representation
- **Peak Detection**: Extract distinctive frequency peaks from spectrograms  
- **Fingerprinting**: Create robust fingerprints using:
  - **Peak Pairs**: Hash combinations of nearby frequency peaks (more selective)
  - **Single Peaks**: Simple frequency-time tuples (baseline)
- **Database Matching**: Store fingerprints and match query clips using real time-offset histograms
- **Robustness Testing**: Evaluate performance under noise and pitch shifts

### Interactive App
- Built with **Streamlit** for easy interaction
- Ships with a pre-built, pre-indexed database so it works immediately — no manual upload/build step
- **Four main tabs**:
  1. **Build Database**: Pre-loaded on startup; optionally add/rebuild from your own files (.wav or .mp3)
  2. **Query & Identify**: Upload a clip and identify the matching song, with spectrogram/constellation/offset-histogram visuals
  3. **Batch Mode**: Upload multiple clips and get a `results.csv` (`filename,prediction`)
  4. **Analysis & Insights**: Understand how the system works

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
# Clone the repo
git clone https://github.com/aashishr24/EE200-Sonic-Signatures.git
cd EE200-Sonic-Signatures

# Install dependencies (ffmpeg is required for MP3 support -
# on Debian/Ubuntu: apt install ffmpeg; already handled automatically
# on Streamlit Cloud via packages.txt)
pip install -r requirements.txt
```

## Usage

### Run the Interactive App
```bash
streamlit run ss.py
```

The app will open at `http://localhost:8501` with the pre-built `song_database.pkl`
(50 songs) already loaded — no setup needed.

### Workflow

**Step 1: Song Database**
- Already loaded on startup from `song_database.pkl`
- Optionally upload your own `.wav`/`.mp3` files in "Add / Rebuild From Your Own Files"

**Step 2: Identify a Song**
- Go to "Query & Identify" tab
- Upload a query `.wav` or `.mp3` clip
- Click "Identify Song"
- View:
  - **Spectrogram**: Time-frequency representation
  - **Constellation**: Peak locations overlaid
  - **Offset Histogram**: Real time-alignment histogram — sharp spike for a correct match, scattered for a wrong one
  - **Results**: Best match with confidence score, and a table comparing all database songs

**Step 3: Batch Mode**
- Upload multiple clips at once
- Download `results.csv` (`filename,prediction`)

**Step 4: Understand the System**
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
1. Extract fingerprints from query audio, each tagged with its real timestamp
2. Hash each fingerprint and look it up in the database
3. For every hash match, compute the time offset: `db_time - query_time`
4. Bucket these offsets into a histogram
5. **Score = height of the tallest bin** — i.e. how many fingerprints agree
   on one consistent alignment, not just the total number of collisions.
   A true match produces one sharp spike at the correct offset; a wrong
   song produces small, scattered bars across many offsets.

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

**Handles Well (measured on the real 50-song database):**
- Background noise: correct identification down to **0 dB SNR**
- Volume changes
- Small tempo variations

**Fails Against:**
- Pitch shifts (even ±1-2% noticeably weakens the match, ±5% fails)
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
├── project.py            # Core MusicFingerprinter class
│                          # - Spectrogram computation, peak detection
│                          # - Fingerprint creation (pairs + singles)
│                          # - Database building, query matching (real
│                          #   time-offset histogram), robustness testing
├── ss.py                  # Streamlit interactive app (single-clip + batch mode)
├── db_loader.py           # Auto-loads the pre-built database on app startup
├── song_database.pkl      # Pre-built fingerprint database (50 songs)
├── songs/                 # Original song library (as provided, unrenamed)
├── build_database.py      # Standalone CLI script to (re)build the database
├── convert_to_wav.py      # Utility: batch-convert audio to .wav
├── demo.py / run_analysis.py / fast_analysis.py /
│   minimal_analysis.py / ultra_fast_analysis.py
│                          # Report-figure/analysis generation scripts
├── requirements.txt       # Python dependencies
├── packages.txt           # System packages (ffmpeg, for Streamlit Cloud)
├── FIXES.md               # Changelog of bugs found and fixed
├── TECHNICAL_REPORT.md    # Full technical writeup
└── README.md              # This file
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
- **pydub** (+ **ffmpeg**): MP3/compressed audio decoding

- Python 3.8+
- See `requirements.txt` for all dependencies, `FIXES.md` for the full
  changelog of bugs found and fixed since the original implementation.

## License

MIT