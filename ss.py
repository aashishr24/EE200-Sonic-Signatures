"""
Q3B: Signals to Software - Interactive Music Identifier App
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from project import MusicFingerprinter
import tempfile
import os
from collections import defaultdict
import json

st.set_page_config(page_title="🎵 Music Identifier", layout="wide")

st.title("🎵 Music Identifier - Sonic Signatures")
st.markdown("A Shazam-like application that identifies songs using spectral fingerprints")
st.markdown("---")

# Initialize fingerprinter
@st.cache_resource
def get_fingerprinter():
    return MusicFingerprinter()

fingerprinter = get_fingerprinter()

# Sidebar configuration
st.sidebar.title("⚙️ Configuration")
freq_min = st.sidebar.slider("Min Frequency (Hz)", 20, 200, 40)
freq_max = st.sidebar.slider("Max Frequency (Hz)", 2000, 10000, 8000)
threshold_db = st.sidebar.slider("Peak Detection Threshold (dB)", 5, 20, 10)
use_pairs = st.sidebar.checkbox("Use Peak Pairs (vs Single Peaks)", value=True)

# Update fingerprinter if needed
if freq_min != fingerprinter.freq_min or freq_max != fingerprinter.freq_max:
    fingerprinter.freq_min = freq_min
    fingerprinter.freq_max = freq_max
    fingerprinter.min_freq_bin = int(freq_min * fingerprinter.n_fft / fingerprinter.target_sr)
    fingerprinter.max_freq_bin = int(freq_max * fingerprinter.n_fft / fingerprinter.target_sr)

# Main app tabs
tab1, tab2, tab3 = st.tabs(["📚 Build Database", "🔍 Query & Identify", "📊 Analysis"])

# ==================== TAB 1: BUILD DATABASE ====================
with tab1:
    st.header("1. Build Song Database")
    st.write("Upload audio files (.wav) to build the fingerprint database.")
    
    # File upload
    uploaded_files = st.file_uploader(
        "Upload WAV files",
        type=['wav'],
        accept_multiple_files=True,
        help="Select one or more .wav files to add to the database"
    )
    
    # Create database
    if uploaded_files:
        if st.button("🔨 Build Database", key="build_db"):
            st.info("Building database from uploaded files...")
            
            # Create temporary directory for uploaded files
            temp_dir = tempfile.mkdtemp()
            
            # Save uploaded files
            for uploaded_file in uploaded_files:
                file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(file_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
            
            # Build database
            progress_bar = st.progress(0)
            database = {}
            
            for idx, filename in enumerate(os.listdir(temp_dir)):
                if filename.endswith('.wav'):
                    filepath = os.path.join(temp_dir, filename)
                    song_name = os.path.splitext(filename)[0]
                    
                    try:
                        audio, sr = fingerprinter.load_audio(filepath)
                        frequencies, times, magnitude = fingerprinter.compute_spectrogram(audio, sr)
                        peaks = fingerprinter.find_peaks(magnitude, frequencies, threshold_db)
                        
                        if use_pairs:
                            fingerprints = fingerprinter.create_fingerprint_pairs(peaks, frequencies, times)
                        else:
                            fingerprints = fingerprinter.create_single_peak_fingerprints(peaks, frequencies, times)
                        
                        # Build hash map
                        database[song_name] = defaultdict(list)
                        for fp in fingerprints:
                            fp_hash = hash(fp) % (10 ** 9)
                            database[song_name][fp_hash].append(0)  # Simplified offset tracking
                        
                        database[song_name] = dict(database[song_name])
                        
                        progress_bar.progress((idx + 1) / len([f for f in os.listdir(temp_dir) if f.endswith('.wav')]))
                        
                    except Exception as e:
                        st.error(f"Error processing {song_name}: {e}")
            
            st.session_state.database = database
            st.session_state.temp_dir = temp_dir
            st.success(f"✅ Database built! {len(database)} songs indexed.")
            
            # Display database statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Songs in DB", len(database))
            with col2:
                total_fps = sum(len(fps) for fps in database.values())
                st.metric("Total Fingerprints", total_fps)
            with col3:
                avg_fps = total_fps / len(database) if database else 0
                st.metric("Avg FPs per Song", int(avg_fps))

# ==================== TAB 2: QUERY & IDENTIFY ====================
with tab2:
    st.header("2. Query & Identify Songs")
    
    if 'database' not in st.session_state or not st.session_state.database:
        st.warning("⚠️ No database loaded! Build a database first in the 'Build Database' tab.")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Upload Query Clip")
            query_file = st.file_uploader(
                "Upload a WAV file to identify",
                type=['wav'],
                key='query_upload'
            )
        
        with col2:
            st.subheader("Or Record from Mic")
            # Placeholder for future recording functionality
            st.info("Recording feature coming soon!")
        
        if query_file:
            if st.button("🔎 Identify Song", key="identify"):
                # Save and process query
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
                    tmp.write(query_file.getbuffer())
                    query_path = tmp.name
                
                try:
                    query_audio, query_sr = fingerprinter.load_audio(query_path)
                    
                    # Show query info
                    st.subheader("Query Audio Analysis")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Duration", f"{len(query_audio) / query_sr:.2f}s")
                    with col2:
                        st.metric("Sample Rate", f"{query_sr} Hz")
                    with col3:
                        st.metric("Length", f"{len(query_audio)} samples")
                    
                    # Extract fingerprints
                    with st.spinner("Extracting fingerprints..."):
                        frequencies, times, magnitude = fingerprinter.compute_spectrogram(query_audio, query_sr)
                        peaks = fingerprinter.find_peaks(magnitude, frequencies, threshold_db)
                        
                        if use_pairs:
                            query_fps = fingerprinter.create_fingerprint_pairs(peaks, frequencies, times)
                        else:
                            query_fps = fingerprinter.create_single_peak_fingerprints(peaks, frequencies, times)
                        
                        st.success(f"Found {len(peaks)} peaks, {len(query_fps)} fingerprints")
                    
                    # Plot spectrogram
                    st.subheader("📊 Spectrogram")
                    fig = plt.figure(figsize=(12, 5))
                    plt.pcolormesh(times, frequencies, magnitude, shading='auto', cmap='viridis', alpha=0.7)
                    plt.ylabel('Frequency (Hz)')
                    plt.xlabel('Time (s)')
                    plt.colorbar(label='Magnitude (dB)')
                    plt.ylim([fingerprinter.freq_min, fingerprinter.freq_max])
                    st.pyplot(fig)
                    
                    # Plot constellation
                    st.subheader("🌟 Peak Constellation")
                    fig = plt.figure(figsize=(12, 5))
                    plt.pcolormesh(times, frequencies, magnitude, shading='auto', cmap='viridis', alpha=0.7)
                    if peaks:
                        freq_peaks = frequencies[np.array([p[0] for p in peaks])]
                        time_peaks = times[np.array([p[1] for p in peaks])]
                        plt.scatter(time_peaks, freq_peaks, c='red', s=50, marker='o',
                                   edgecolors='white', linewidth=0.5, alpha=0.8)
                    plt.ylabel('Frequency (Hz)')
                    plt.xlabel('Time (s)')
                    plt.colorbar(label='Magnitude (dB)')
                    plt.ylim([fingerprinter.freq_min, fingerprinter.freq_max])
                    st.pyplot(fig)
                    
                    # Match against database
                    with st.spinner("Matching against database..."):
                        results = fingerprinter.match_query(query_audio, query_sr, 
                                                           st.session_state.database, use_pairs)
                    
                    # Find best match
                    best_match = max(results.items(), key=lambda x: x[1]['score'])
                    best_song = best_match[0]
                    best_score = best_match[1]['score']
                    
                    # Display results
                    st.subheader("🎯 Identification Results")
                    
                    # Best match card
                    if best_score > 0:
                        st.success(f"✅ Best Match: **{best_song}** (Score: {best_score})")
                        
                        # Score histogram
                        fig = plt.figure(figsize=(10, 5))
                        song_names = list(results.keys())
                        scores = [results[s]['score'] for s in song_names]
                        colors = ['green' if s == best_song else 'steelblue' for s in song_names]
                        plt.bar(song_names, scores, color=colors, alpha=0.7)
                        plt.ylabel('Match Score')
                        plt.xlabel('Song')
                        plt.title('Matching Scores for All Songs')
                        plt.xticks(rotation=45, ha='right')
                        plt.tight_layout()
                        st.pyplot(fig)
                        
                        # Offset histogram for best match
                        st.subheader("📈 Offset Histogram (Best Match)")
                        if results[best_song]['offset_histogram']:
                            histogram = results[best_song]['offset_histogram']
                            fig = plt.figure(figsize=(10, 5))
                            offsets = list(histogram.keys())
                            counts = list(histogram.values())
                            plt.bar(offsets, counts, width=0.8, alpha=0.7, color='green')
                            plt.xlabel('Time Offset')
                            plt.ylabel('Number of Matching Fingerprints')
                            plt.title(f'Alignment for "{best_song}"')
                            plt.tight_layout()
                            st.pyplot(fig)
                        
                        # Comparison table
                        st.subheader("📋 All Song Scores")
                        results_data = []
                        for song, res in sorted(results.items(), key=lambda x: x[1]['score'], reverse=True):
                            results_data.append({
                                'Song': song,
                                'Match Score': res['score'],
                                'Query FPs': res['num_query_peaks'],
                                'Confidence': f"{(res['score'] / max(1, res['num_query_peaks']) * 100):.1f}%"
                            })
                        st.dataframe(results_data, use_container_width=True)
                    else:
                        st.error("❌ No matches found in database!")
                    
                    os.unlink(query_path)
                    
                except Exception as e:
                    st.error(f"Error processing query: {e}")

# ==================== TAB 3: ANALYSIS & INSIGHTS ====================
with tab3:
    st.header("3. Analysis & Insights")
    
    st.subheader("🔬 Understanding the System")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Spectrogram Time vs Frequency Resolution
        
        **Short Window (e.g., 512 samples):**
        - ✅ Better **time resolution** - precise onset times
        - ❌ Poorer **frequency resolution** - frequencies blurred
        - Use for: Percussive, fast-changing sounds
        
        **Long Window (e.g., 4096 samples):**
        - ❌ Poorer **time resolution** - slower to detect changes
        - ✅ Better **frequency resolution** - sharp frequency peaks
        - Use for: Sustained tones, precise frequency content
        """)
    
    with col2:
        st.markdown("""
        ### Why Peak Pairs > Single Peaks
        
        **Single Peaks:**
        - Can appear in many songs
        - High false positive rate
        - Not robust to noise/shifts
        
        **Peak Pairs:**
        - Unique combinations (frequency1, frequency2, time_gap)
        - Much lower false positive rate
        - Fingerprints are more distinctive
        - Better alignment at correct offset
        """)
    
    st.divider()
    
    st.subheader("🛡️ Robustness Characteristics")
    
    analysis_col1, analysis_col2 = st.columns(2)
    
    with analysis_col1:
        st.markdown("""
        ### ✅ What This System Handles Well
        
        - **Background noise** (up to SNR ~10dB)
        - **Volume changes** (DC offset invariant)
        - **Small time compressions** (slight speedup)
        
        ### ❌ What Challenges This System
        
        - **Pitch shifts** (even small ±5%)
        - **Heavy compression** (audio codecs)
        - **Significant time stretching**
        - **Extreme noise** (SNR < 5dB)
        """)
    
    with analysis_col2:
        st.markdown("""
        ### Why Pitch Shifts Fail
        
        When the song is pitch-shifted:
        1. All frequency peaks shift up/down uniformly
        2. Peak pair frequencies change: (f₁, f₂, Δt)
        3. Becomes (αf₁, αf₂, Δt) where α is shift factor
        4. Hash values completely different
        5. No matches found despite same melody
        
        **Human ear:** Still recognizes the tune
        **Fingerprinter:** Lost!
        """)
    
    st.divider()
    
    st.subheader("💡 Suggested Improvements")
    
    improvements = {
        "1. **Chroma Features**": "Instead of absolute frequencies, track relative frequency relationships (semitones). Makes system invariant to pitch shifts.",
        "2. **Onset Detection**": "Focus on attack times of notes, not just frequency. More robust to pitch shifts.",
        "3. **Temporal Normalization**": "Normalize fingerprints by time compression factor. Handles tempo changes.",
        "4. **Statistical Matching**": "Use probabilistic matching instead of binary hashing for better robustness.",
        "5. **Hybrid Fingerprints**": "Combine multiple feature types (chromagram + MFCC + spectral peaks) for redundancy."
    }
    
    for title, description in improvements.items():
        st.markdown(f"**{title}**  \n{description}\n")
    
    st.divider()
    
    st.subheader("📊 System Parameters")
    
    param_col1, param_col2 = st.columns(2)
    
    with param_col1:
        st.write("**Current Configuration:**")
        st.info(f"""
        - FFT Size: {fingerprinter.n_fft}
        - Hop Length: {fingerprinter.hop_length}
        - Frequency Range: {fingerprinter.freq_min}-{fingerprinter.freq_max} Hz
        - Peak Threshold: {threshold_db} dB
        - Fingerprint Type: {'Peak Pairs' if use_pairs else 'Single Peaks'}
        """)
    
    with param_col2:
        st.write("**Explanation:**")
        st.markdown("""
        - **FFT Size**: Higher = better frequency resolution
        - **Hop Length**: Smaller = better time resolution
        - **Frequency Range**: Ignore inaudible/noise frequencies
        - **Peak Threshold**: Higher = fewer, stronger peaks
        - **Fingerprint Type**: Pairs are more selective
        """)
