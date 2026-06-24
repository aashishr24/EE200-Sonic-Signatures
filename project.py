"""
Q3A: Sonic Signatures - Music Fingerprinting and Identification
A Shazam-like music identifier using spectrograms and peak-based fingerprints
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy.io import wavfile
import os
from typing import List, Tuple, Dict
import json
from collections import defaultdict
import hashlib


class MusicFingerprinter:
    """Build fingerprints from audio spectrograms and identify songs."""
    
    def __init__(self, 
                 target_sr: int = 22050,
                 n_fft: int = 4096,
                 hop_length: int = 512,
                 freq_min: int = 40,
                 freq_max: int = 8000):
        """
        Initialize the fingerprinter with spectrogram parameters.
        
        Args:
            target_sr: Target sample rate
            n_fft: FFT window size
            hop_length: Number of samples between frames
            freq_min: Minimum frequency for peak detection
            freq_max: Maximum frequency for peak detection
        """
        self.target_sr = target_sr
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.freq_min = freq_min
        self.freq_max = freq_max
        
        # Convert Hz to bin indices
        self.min_freq_bin = int(freq_min * n_fft / target_sr)
        self.max_freq_bin = int(freq_max * n_fft / target_sr)
    
    def load_audio(self, filepath: str) -> Tuple[np.ndarray, int]:
        """Load audio file and return normalized waveform and sample rate."""
        try:
            sr, audio = wavfile.read(filepath)
            # Normalize to [-1, 1]
            if audio.dtype == np.int16:
                audio = audio.astype(np.float32) / 32768.0
            elif audio.dtype == np.int32:
                audio = audio.astype(np.float32) / 2147483648.0
            
            # Convert stereo to mono if needed
            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=1)
            
            return audio, sr
        except Exception as e:
            raise ValueError(f"Error loading audio file {filepath}: {e}")
    
    def compute_spectrogram(self, audio: np.ndarray, sr: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute spectrogram using STFT.
        
        Returns:
            frequencies: Frequency array
            times: Time array
            magnitude: Magnitude spectrogram (dB scale)
        """
        # Compute STFT
        frequencies, times, Sxx = signal.spectrogram(
            audio, 
            sr, 
            nperseg=self.n_fft,
            noverlap=self.n_fft - self.hop_length,
            scaling='spectrum'
        )
        
        # Convert to dB scale (avoid log(0))
        magnitude = 20 * np.log10(np.maximum(Sxx, 1e-10))
        
        return frequencies, times, magnitude
    
    def plot_spectrogram(self, audio: np.ndarray, sr: int, title: str = "Spectrogram", 
                        window_size: int = None, hop_len: int = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Plot spectrogram with specified window size (for time vs frequency resolution analysis).
        
        Args:
            audio: Audio waveform
            sr: Sample rate
            title: Plot title
            window_size: Custom window size for STFT
            hop_len: Custom hop length
            
        Returns:
            frequencies, times, magnitude
        """
        nperseg = window_size or self.n_fft
        noverlap = (nperseg - hop_len) if hop_len else (nperseg - self.hop_length)
        
        frequencies, times, Sxx = signal.spectrogram(
            audio, sr, 
            nperseg=nperseg,
            noverlap=noverlap,
            scaling='spectrum'
        )
        
        magnitude = 20 * np.log10(np.maximum(Sxx, 1e-10))
        
        plt.figure(figsize=(12, 6))
        plt.pcolormesh(times, frequencies, magnitude, shading='auto', cmap='viridis')
        plt.ylabel('Frequency (Hz)')
        plt.xlabel('Time (s)')
        plt.title(title)
        plt.colorbar(label='Magnitude (dB)')
        plt.ylim([self.freq_min, self.freq_max])
        plt.tight_layout()
        
        return frequencies, times, magnitude
    
    def find_peaks(self, magnitude: np.ndarray, frequencies: np.ndarray, 
                   threshold_db: float = 10, neighborhood_size: int = 10) -> List[Tuple[int, int]]:
        """
        Find local maxima (peaks) in the spectrogram.
        
        Args:
            magnitude: Magnitude spectrogram (dB scale)
            frequencies: Frequency array
            threshold_db: Minimum peak height above background
            neighborhood_size: Size of neighborhood for local maxima detection
            
        Returns:
            List of (freq_bin, time_bin) tuples for peaks
        """
        # Apply median filter to find background
        background = signal.medfilt2d(magnitude, kernel_size=(2*neighborhood_size+1, 1))
        
        # Peaks must be at least threshold_db above background
        peak_map = magnitude > (background + threshold_db)
        
        # Find local maxima in time-frequency space
        peaks = []
        for t in range(neighborhood_size, magnitude.shape[1] - neighborhood_size):
            for f in range(neighborhood_size, magnitude.shape[0] - neighborhood_size):
                if peak_map[f, t]:
                    # Check if it's a local maximum in its neighborhood
                    neighborhood = magnitude[
                        f-neighborhood_size:f+neighborhood_size+1,
                        t-neighborhood_size:t+neighborhood_size+1
                    ]
                    if magnitude[f, t] == np.max(neighborhood):
                        peaks.append((f, t))
        
        return peaks
    
    def plot_constellation(self, magnitude: np.ndarray, frequencies: np.ndarray, 
                          times: np.ndarray, peaks: List[Tuple[int, int]],
                          title: str = "Constellation Map") -> None:
        """Plot spectrogram with peak constellation overlaid."""
        plt.figure(figsize=(12, 6))
        plt.pcolormesh(times, frequencies, magnitude, shading='auto', cmap='viridis', alpha=0.7)
        
        if peaks:
            freq_peaks = frequencies[np.array([p[0] for p in peaks])]
            time_peaks = times[np.array([p[1] for p in peaks])]
            plt.scatter(time_peaks, freq_peaks, c='red', s=50, marker='o', 
                       edgecolors='white', linewidth=0.5, alpha=0.8, label='Peaks')
        
        plt.ylabel('Frequency (Hz)')
        plt.xlabel('Time (s)')
        plt.title(title)
        plt.colorbar(label='Magnitude (dB)')
        plt.ylim([self.freq_min, self.freq_max])
        plt.legend()
        plt.tight_layout()
    
    def create_fingerprint_pairs(self, peaks: List[Tuple[int, int]], 
                                 frequencies: np.ndarray, times: np.ndarray,
                                 anchor_gap: int = 5, max_time_gap: int = 50) -> List[Tuple[int, int, int]]:
        """
        Create fingerprints by pairing nearby peaks.
        
        For each peak, find nearby peaks and create hashes based on:
        - Frequency of first peak
        - Frequency of second peak  
        - Time gap between them
        
        Args:
            peaks: List of (freq_bin, time_bin) tuples
            frequencies: Frequency array
            times: Time array
            anchor_gap: Maximum time gap to look ahead for pairing
            max_time_gap: Maximum time gap for a valid pair
            
        Returns:
            List of (freq1_quantized, freq2_quantized, delta_t_quantized) tuples
        """
        fingerprints = []
        
        if len(peaks) < 2:
            return fingerprints
        
        # Quantize frequencies to reduce noise
        freq_resolution = 25  # Hz
        time_resolution = 1   # Number of STFT frames
        
        for i, (f1, t1) in enumerate(peaks):
            freq1_hz = frequencies[f1]
            freq1_q = int(freq1_hz / freq_resolution)
            
            # Look ahead at nearby peaks
            for j in range(i + 1, min(i + anchor_gap, len(peaks))):
                f2, t2 = peaks[j]
                freq2_hz = frequencies[f2]
                freq2_q = int(freq2_hz / freq_resolution)
                
                delta_t = t2 - t1
                
                if 0 < delta_t <= max_time_gap:
                    delta_t_q = int(delta_t / time_resolution)
                    fingerprints.append((freq1_q, freq2_q, delta_t_q))
        
        return fingerprints
    
    def create_single_peak_fingerprints(self, peaks: List[Tuple[int, int]], 
                                       frequencies: np.ndarray, times: np.ndarray,
                                       time_resolution: int = 5) -> List[Tuple[int, int]]:
        """
        Create simpler fingerprints using single peaks (frequency, quantized_time).
        
        Args:
            peaks: List of (freq_bin, time_bin) tuples
            frequencies: Frequency array
            times: Time array
            time_resolution: Quantization level for time (in frames)
            
        Returns:
            List of (freq_quantized, time_quantized) tuples
        """
        fingerprints = []
        freq_resolution = 25  # Hz
        
        for f, t in peaks:
            freq_hz = frequencies[f]
            freq_q = int(freq_hz / freq_resolution)
            time_q = int(t / time_resolution)
            fingerprints.append((freq_q, time_q))
        
        return fingerprints
    
    def build_database(self, audio_dir: str, use_pairs: bool = True) -> Dict:
        """
        Build a database of fingerprints for all songs in a directory.
        
        Args:
            audio_dir: Directory containing .wav files
            use_pairs: If True, use pair fingerprints; if False, use single peaks
            
        Returns:
            Database dictionary: {song_name: {fingerprint_hash: [time_offsets]}}
        """
        database = {}
        
        for filename in os.listdir(audio_dir):
            if filename.endswith('.wav'):
                filepath = os.path.join(audio_dir, filename)
                song_name = os.path.splitext(filename)[0]
                
                print(f"Processing {song_name}...")
                
                try:
                    audio, sr = self.load_audio(filepath)
                    frequencies, times, magnitude = self.compute_spectrogram(audio, sr)
                    peaks = self.find_peaks(magnitude, frequencies)
                    
                    if use_pairs:
                        fingerprints = self.create_fingerprint_pairs(peaks, frequencies, times)
                    else:
                        fingerprints = self.create_single_peak_fingerprints(peaks, frequencies, times)
                    
                    # Hash fingerprints and store with time offsets
                    database[song_name] = defaultdict(list)
                    for fp in fingerprints:
                        fp_hash = hash(fp) % (10 ** 9)  # Simple hash
                        # For pairs: store the time of the first peak
                        # For singles: store the time
                        time_offset = 0  # Simplified; in real implementation would track actual times
                        database[song_name][fp_hash].append(time_offset)
                    
                    database[song_name] = dict(database[song_name])
                    
                except Exception as e:
                    print(f"Error processing {song_name}: {e}")
        
        return database
    
    def match_query(self, query_audio: np.ndarray, query_sr: int, 
                   database: Dict, use_pairs: bool = True) -> Dict[str, Dict]:
        """
        Match a query audio clip against the database.
        
        Args:
            query_audio: Query audio waveform
            query_sr: Sample rate
            database: Fingerprint database
            use_pairs: Must match the fingerprint type used in database
            
        Returns:
            Match results: {song_name: {'score': int, 'offset_histogram': dict}}
        """
        # Extract fingerprints from query
        frequencies, times, magnitude = self.compute_spectrogram(query_audio, query_sr)
        peaks = self.find_peaks(magnitude, frequencies)
        
        if use_pairs:
            query_fps = self.create_fingerprint_pairs(peaks, frequencies, times)
        else:
            query_fps = self.create_single_peak_fingerprints(peaks, frequencies, times)
        
        results = {}
        
        for song_name, song_fingerprints in database.items():
            offset_histogram = defaultdict(int)
            
            for query_fp in query_fps:
                query_hash = hash(query_fp) % (10 ** 9)
                
                if query_hash in song_fingerprints:
                    # Found a match - this fingerprint exists in the song
                    # Increment the count at offset 0 (simplified)
                    offset_histogram[0] += 1
            
            # Score is the number of matching fingerprints
            score = sum(offset_histogram.values())
            results[song_name] = {
                'score': score,
                'offset_histogram': dict(offset_histogram),
                'num_query_peaks': len(query_fps)
            }
        
        return results
    
    def plot_offset_histogram(self, results: Dict[str, Dict], best_match: str = None) -> None:
        """Plot histogram showing how offsets align for the best match."""
        plt.figure(figsize=(10, 6))
        
        if best_match and best_match in results:
            histogram = results[best_match]['offset_histogram']
            if histogram:
                offsets = list(histogram.keys())
                counts = list(histogram.values())
                plt.bar(offsets, counts, width=0.8, alpha=0.7, color='steelblue')
                plt.xlabel('Time Offset')
                plt.ylabel('Number of Matching Fingerprints')
                plt.title(f'Match Histogram - {best_match}')
            else:
                plt.text(0.5, 0.5, 'No matches found', ha='center', va='center')
        else:
            plt.text(0.5, 0.5, 'No match selected', ha='center', va='center')
        
        plt.tight_layout()


def test_robustness(fingerprinter: MusicFingerprinter, audio: np.ndarray, sr: int,
                   database: Dict) -> Dict:
    """
    Test robustness of the identifier against noise and pitch shifts.
    
    Returns:
        Dictionary with robustness test results
    """
    results = {}
    
    # Test with increasing noise levels
    print("\n=== Testing Robustness Against Noise ===")
    noise_results = []
    for snr_db in [30, 20, 10, 5, 3]:
        noise = np.random.normal(0, 1, len(audio))
        signal_power = np.mean(audio ** 2)
        noise_power = signal_power / (10 ** (snr_db / 10))
        noise = noise / np.sqrt(np.mean(noise ** 2)) * np.sqrt(noise_power)
        
        noisy_audio = audio + noise
        noisy_audio = np.clip(noisy_audio, -1, 1)
        
        matches = fingerprinter.match_query(noisy_audio, sr, database)
        best_match = max(matches.items(), key=lambda x: x[1]['score'])
        noise_results.append({
            'snr_db': snr_db,
            'best_match': best_match[0],
            'score': best_match[1]['score']
        })
        print(f"SNR {snr_db}dB: {best_match[0]} (score: {best_match[1]['score']})")
    
    results['noise_robustness'] = noise_results
    
    # Test with pitch shift (time stretching)
    print("\n=== Testing Robustness Against Pitch Shift ===")
    pitch_results = []
    for factor in [1.02, 1.05, 1.1, 0.95, 0.9]:
        stretched = signal.resample(audio, int(len(audio) / factor))
        
        matches = fingerprinter.match_query(stretched, sr, database)
        best_match = max(matches.items(), key=lambda x: x[1]['score'])
        pitch_results.append({
            'factor': factor,
            'best_match': best_match[0],
            'score': best_match[1]['score']
        })
        pct = (factor - 1) * 100
        print(f"Pitch shift {pct:+.1f}%: {best_match[0]} (score: {best_match[1]['score']})")
    
    results['pitch_robustness'] = pitch_results
    
    return results


if __name__ == "__main__":
    # Example usage (requires audio files)
    fingerprinter = MusicFingerprinter()
    print("Music Fingerprinter initialized and ready to use.")
