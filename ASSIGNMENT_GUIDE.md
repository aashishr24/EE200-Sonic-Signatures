# Music Identifier: Sonic Signatures - Complete Assignment Guide

## Quick Start

### Installation
```bash
cd /workspaces/EE200
pip install -r requirements.txt
```

### Run Interactive App (Q3B)
```bash
streamlit run ss.py
```

### Run Demo with Synthetic Audio
```bash
python demo.py
```

---

## Q3A: SONIC SIGNATURES - CORE ALGORITHM

### Overview
Build a music fingerprinting system that identifies songs using spectral peaks, similar to Shazam.

### Step 1: Plot DFT Magnitude
Show that DFT provides frequency content but loses timing information.

```python
from project import MusicFingerprinter
import matplotlib.pyplot as plt

fp = MusicFingerprinter()
audio, sr = fp.load_audio("song.wav")

# Compute FFT
frequencies, times, magnitude = fp.compute_spectrogram(audio, sr)

# Plot raw spectrogram
plt.figure(figsize=(12, 6))
plt.pcolormesh(times, frequencies, magnitude, shading='auto', cmap='viridis')
plt.ylabel('Frequency (Hz)')
plt.xlabel('Time (s)')
plt.title('Full Spectrogram - Shows all frequencies present')
plt.colorbar(label='Magnitude (dB)')
plt.ylim([40, 8000])
plt.show()
```

**Observations for report:**
- All frequency information is collapsed across time
- Can see which frequencies exist but not when they occur
- No notion of melody or note sequence

### Step 2: Experiment with Window Sizes

Compare spectrograms with different time-frequency resolution tradeoffs:

```python
# Short window - better time resolution
fp.plot_spectrogram(audio, sr, 
                    window_size=512,
                    hop_len=128,
                    title="Short Window (512 samples) - Better Time Resolution")

# Long window - better frequency resolution  
fp.plot_spectrogram(audio, sr,
                    window_size=4096, 
                    hop_len=512,
                    title="Long Window (4096 samples) - Better Frequency Resolution")

# Very long window
fp.plot_spectrogram(audio, sr,
                    window_size=8192,
                    hop_len=1024,
                    title="Long Window (8192 samples) - Maximum Frequency Resolution")
```

**Key observations to document:**
- Short window: Note onsets are sharp but frequency blurred
- Long window: Frequencies clear but slow to detect changes
- Tradeoff is inherent (Heisenberg Uncertainty)
- Choose based on application needs

### Step 3: Extract and Visualize Peaks

Find the strongest points in the spectrogram:

```python
# Extract peaks
peaks = fp.find_peaks(magnitude, frequencies, threshold_db=10)

# Plot constellation
fp.plot_constellation(magnitude, frequencies, times, peaks,
                      title="Peak Constellation - Song's Fingerprint")
```

**For report:**
- Show peaks overlaid on spectrogram
- Explain that these peaks are the "constellation"
- Rising peaks = rising notes, flat peaks = held notes

### Step 4: Build Fingerprint Database

Create hashes from peak combinations:

```python
# Peak Pair Fingerprints (recommended)
pairs = fp.create_fingerprint_pairs(peaks, frequencies, times)
# Format: (freq1_quantized, freq2_quantized, time_gap_quantized)
# Example: (440, 880, 5) means freq1=11000Hz, freq2=22000Hz, 115ms gap

# Single Peak Fingerprints (baseline)
singles = fp.create_single_peak_fingerprints(peaks, frequencies, times)
# Format: (freq_quantized, time_quantized)
# Example: (440, 10) means 11000Hz peak at 230ms

# Build full database
database = fp.build_database("audio_directory/", use_pairs=True)
# Returns: {song_name: {hash: [offsets], ...}, ...}
```

### Step 5: Query and Match

Identify songs by matching fingerprints:

```python
# Load query clip
query_audio, query_sr = fp.load_audio("query_clip.wav")

# Match against database
results = fp.match_query(query_audio, query_sr, database, use_pairs=True)

# Best match
best_match = max(results.items(), key=lambda x: x[1]['score'])
print(f"Best Match: {best_match[0]} (Score: {best_match[1]['score']})")

# Plot results
fp.plot_offset_histogram(results, best_match[0])
```

### Step 6: Compare Peak Pairs vs Single Peaks

Run same queries with both methods and compare:

```python
# Build two databases
db_pairs = fp.build_database("songs/", use_pairs=True)
db_singles = fp.build_database("songs/", use_pairs=False)

# Match with both
results_pairs = fp.match_query(query, sr, db_pairs, use_pairs=True)
results_singles = fp.match_query(query, sr, db_singles, use_pairs=False)

# Compare scores
print("Peak Pairs Results:")
for song, res in results_pairs.items():
    print(f"  {song}: {res['score']}")
    
print("Single Peaks Results:")
for song, res in results_singles.items():
    print(f"  {song}: {res['score']}")
```

**Why Peak Pairs Win:**

| Aspect | Single Peaks | Peak Pairs |
|--------|--------------|-----------|
| False Positives | Many (common freq occurs in many songs) | Few (combo is rare) |
| Matching Quality | Scattered random matches | All matches at same offset |
| Confidence | Ambiguous | Clear peak in offset histogram |
| Robustness | Easily confused | More selective |

### Step 7: Robustness Testing

Test against noise and pitch shifts:

```python
from scipy import signal

# NOISE TEST
print("=== Noise Robustness ===")
for snr_db in [30, 20, 10, 5, 3]:
    # Generate noise with specific SNR
    noise = np.random.normal(0, 1, len(query_audio))
    signal_power = np.mean(query_audio ** 2)
    noise_power = signal_power / (10 ** (snr_db / 10))
    noise = noise / np.sqrt(np.mean(noise ** 2)) * np.sqrt(noise_power)
    noisy_audio = np.clip(query_audio + noise, -1, 1)
    
    # Try to match
    results = fp.match_query(noisy_audio, sr, database)
    best_match = max(results.items(), key=lambda x: x[1]['score'])
    print(f"SNR {snr_db}dB: {best_match[0]} (score: {best_match[1]['score']})")

# PITCH SHIFT TEST
print("\n=== Pitch Shift Robustness ===")
for factor in [1.1, 1.05, 1.02, 0.98, 0.95, 0.9]:
    # Stretch audio (changes pitch)
    stretched = signal.resample(query_audio, int(len(query_audio) / factor))
    
    results = fp.match_query(stretched, sr, database)
    best_match = max(results.items(), key=lambda x: x[1]['score'])
    pct_change = (factor - 1) * 100
    print(f"Pitch {pct_change:+.1f}%: {best_match[0]} (score: {best_match[1]['score']})")
```

**Key Findings for Report:**
- System handles noise up to ~SNR 10dB
- Fails dramatically with pitch shifts > ±2%
- Human ear: still recognizes tune
- Algorithm: completely lost (frequencies all changed!)

### Step 8: Analysis and Explanation

For your report, explain:

1. **Why spectrograms work** - Preserve time information that DFT loses
2. **Time vs frequency tradeoff** - Window size selection
3. **Why peak pairs beat singles** - Uniqueness and offset alignment
4. **Why pitch shifts fail** - All frequencies shift proportionally
5. **Why it works with noise** - Peaks still detectable above noise floor

---

## Q3B: SIGNALS TO SOFTWARE - INTERACTIVE APP

### Application Architecture

The Streamlit app has 3 main components:

#### Tab 1: Build Database
```
User Action: Upload .wav files → Click "Build Database"
    ↓
Processing:
  - Load each audio file
  - Compute spectrogram
  - Find peaks
  - Create fingerprints
  - Hash and store in database
    ↓
Output: Display statistics
  - Songs indexed: N
  - Total fingerprints: M
  - Avg FPs per song: M/N
```

#### Tab 2: Query & Identify
```
User Action: Upload query clip → Click "Identify"
    ↓
Processing:
  - Load query audio
  - Compute spectrogram
  - Find peaks  
  - Create fingerprints
  - Match against each song
  - Build offset histogram
    ↓
Visualization:
  - Spectrogram
  - Peak constellation
  - Match score histogram
  - Offset histogram for best match
  - Results table
```

#### Tab 3: Analysis & Insights
Educational content explaining:
- How the system works
- Time vs frequency resolution
- Why pairs beat singles
- Robustness characteristics
- Suggested improvements

### Running the App

```bash
streamlit run ss.py
```

The app will start at `http://localhost:8501`

### Using the App

**Step 1: Build Database**
1. Go to "Build Database" tab
2. Upload several .wav files
3. Click "Build Database"
4. Note the statistics displayed

**Step 2: Test Query**
1. Go to "Query & Identify" tab
2. Upload a test clip (can be from a song in database, or modified version)
3. Click "Identify Song"
4. View results:
   - Spectrogram (time-frequency plot)
   - Constellation (peaks highlighted in red)
   - Best match name and score
   - Bar chart comparing all songs
   - Offset histogram for best match
   - Detailed results table

**Step 3: Experiment**
- Adjust configuration sliders in sidebar
- Try noisy clips
- Try clips from songs not in database
- Try time-stretched versions

### Key Features to Demonstrate

✅ **Spectrogram Visualization** - Shows frequency content over time
✅ **Peak Constellation** - Highlights distinctive points
✅ **Match Scoring** - Bar chart of all songs
✅ **Confidence Metric** - Percentage based on matching fingerprints
✅ **Offset Histogram** - Shows alignment quality
✅ **Educational Content** - Analysis tab explains everything

---

## Report Requirements

Your written report should include:

### 1. Spectrograms (Q3A)
- [ ] Full DFT magnitude of a song
- [ ] Spectrogram with short window (512 samples)
- [ ] Spectrogram with long window (4096 samples)
- [ ] Written comparison of time vs frequency resolution

### 2. Constellation Plots (Q3A)
- [ ] Spectrogram with peak overlay for several songs
- [ ] Show red circles at detected peaks
- [ ] Caption explaining what the constellation represents

### 3. Fingerprinting (Q3A)
- [ ] Example fingerprints (peak pairs or singles)
- [ ] Explain quantization levels
- [ ] Show sample database structure

### 4. Matching Results (Q3A)
- [ ] Query matched to best match in database
- [ ] Side-by-side spectrograms/constellations
- [ ] Offset histogram showing alignment

### 5. Pair vs Single Comparison (Q3A)
- [ ] Same query matched with both methods
- [ ] Results table or plot comparing scores
- [ ] **Explanation** of why pairs are better

### 6. Robustness Testing (Q3A)
- [ ] Noise test: SNR vs success rate (table or graph)
- [ ] Pitch shift test: % change vs success rate
- [ ] Description of observations
- [ ] Explanation of failure modes

### 7. Analysis (Q3A)
- [ ] Why pitch shifts defeat the system
- [ ] Why spectrograms beat raw DFT
- [ ] Why peak pairs beat single peaks
- [ ] Suggest one improvement and explain why

### 8. App Screenshots (Q3B)
- [ ] Database building interface
- [ ] Query results with spectrogram
- [ ] Peak constellation visualization
- [ ] Match results display

---

## Troubleshooting

### No peaks detected?
- Lower the `threshold_db` parameter
- Use `threshold_db=5` instead of 10
- Check that audio is loud enough

### App not starting?
```bash
pip install streamlit scipy matplotlib
streamlit run ss.py
```

### No matches found?
- Database might be empty - build it first
- Peak detection threshold might be too high
- Query might be very different from database songs

### Pitch shift test failing completely?
- This is expected! System is NOT pitch-invariant
- Document this as a limitation
- Suggest chroma features as improvement

---

## Suggested Improvements (for Discussion)

1. **Chroma Features** - Track pitch relationships instead of absolute frequencies
2. **Onset Detection** - Focus on note attacks rather than frequencies
3. **Temporal Normalization** - Handle tempo changes
4. **Hybrid Fingerprints** - Combine multiple feature types
5. **Probabilistic Matching** - Soft scores instead of binary hashes

---

## File Structure

```
/workspaces/EE200/
├── project.py           ← Core MusicFingerprinter class
├── ss.py                ← Streamlit interactive app
├── demo.py              ← Demo with synthetic audio
├── requirements.txt     ← Python dependencies
├── README.md            ← Project documentation
├── ASSIGNMENT_GUIDE.md  ← This file
└── [audio files] (user-provided for testing)
```

---

## API Reference

### MusicFingerprinter Class

```python
from project import MusicFingerprinter

# Create instance
fp = MusicFingerprinter(
    target_sr=22050,        # Sample rate
    n_fft=4096,             # FFT size
    hop_length=512,         # Samples between frames
    freq_min=40,            # Min frequency (Hz)
    freq_max=8000           # Max frequency (Hz)
)

# Load audio
audio, sr = fp.load_audio("file.wav")

# Compute spectrogram
frequencies, times, magnitude = fp.compute_spectrogram(audio, sr)

# Plot with custom window
frequencies, times, magnitude = fp.plot_spectrogram(
    audio, sr,
    window_size=1024,
    hop_len=256,
    title="Custom Spectrogram"
)

# Find peaks
peaks = fp.find_peaks(magnitude, frequencies, threshold_db=10)
# Returns: [(freq_bin, time_bin), ...]

# Visualize peaks
fp.plot_constellation(magnitude, frequencies, times, peaks, title="Peaks")

# Create fingerprints
pairs = fp.create_fingerprint_pairs(peaks, frequencies, times)
singles = fp.create_single_peak_fingerprints(peaks, frequencies, times)

# Build database
database = fp.build_database("audio_dir/", use_pairs=True)

# Match query
results = fp.match_query(query_audio, query_sr, database, use_pairs=True)
# Returns: {song: {'score': int, 'offset_histogram': dict}, ...}

# Plot results
fp.plot_offset_histogram(results, best_song_name)
```

---

## Good Luck! 🎵

Remember:
- Start with the demo to understand the system
- Build your own database with test songs
- Document everything in your report
- Use the app to visualize intermediate steps
- Compare peak pairs vs single peaks carefully
- Explain WHY things work or fail, not just THAT they do
