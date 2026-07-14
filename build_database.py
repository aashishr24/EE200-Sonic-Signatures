#!/usr/bin/env python3
"""
Build and cache song database for deployment
This script pre-indexes all songs and saves as pickle for fast loading
"""
import os
import pickle
import sys
from collections import defaultdict
from project import MusicFingerprinter

SONGS_DIR = "songs_wav"
DATABASE_CACHE = "song_database.pkl"

def build_database(use_pairs=True, threshold_db=10):
    """Build database from songs_wav directory"""
    
    fingerprinter = MusicFingerprinter()
    database = {}
    
    if not os.path.exists(SONGS_DIR):
        print(f"❌ Songs directory '{SONGS_DIR}' not found!")
        return None
    
    wav_files = [f for f in os.listdir(SONGS_DIR) if f.endswith('.wav')]
    
    if not wav_files:
        print(f"❌ No WAV files found in '{SONGS_DIR}'")
        return None
    
    print(f"Building database for {len(wav_files)} songs...")
    
    for idx, filename in enumerate(wav_files, 1):
        filepath = os.path.join(SONGS_DIR, filename)
        song_name = os.path.splitext(filename)[0]
        
        try:
            # Load audio
            audio, sr = fingerprinter.load_audio(filepath)
            
            # Compute spectrogram
            frequencies, times, magnitude = fingerprinter.compute_spectrogram(audio, sr)
            
            # Find peaks
            peaks = fingerprinter.find_peaks(magnitude, frequencies, threshold_db)
            
            # Create fingerprints
            if use_pairs:
                fingerprints = fingerprinter.create_fingerprint_pairs(peaks, frequencies, times)
            else:
                fingerprints = fingerprinter.create_single_peak_fingerprints(peaks, frequencies, times)
            
            # Build hash map
            database[song_name] = defaultdict(list)
            for fp, anchor_time_sec in fingerprints:
                fp_hash = hash(fp) % (10 ** 9)
                database[song_name][fp_hash].append(anchor_time_sec)
            
            database[song_name] = dict(database[song_name])
            
            print(f"  [{idx:3d}/{len(wav_files)}] {song_name}: {len(fingerprints)} fingerprints")
            
        except Exception as e:
            print(f"  [ERROR] {song_name}: {e}")
    
    return database

def save_database(database, filepath=DATABASE_CACHE):
    """Save database to pickle file"""
    with open(filepath, 'wb') as f:
        pickle.dump(database, f)
    print(f"\n✅ Database saved to {filepath}")
    print(f"   Total songs: {len(database)}")
    total_fps = sum(len(fps) for fps in database.values())
    print(f"   Total fingerprints: {total_fps}")

def load_database(filepath=DATABASE_CACHE):
    """Load database from pickle file"""
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            return pickle.load(f)
    return None

if __name__ == "__main__":
    print("="*80)
    print("SONG DATABASE BUILDER")
    print("="*80)
    
    # Check if database already exists
    if os.path.exists(DATABASE_CACHE):
        print(f"Database cache already exists: {DATABASE_CACHE}")
        db = load_database(DATABASE_CACHE)
        if db:
            print(f"  Loaded {len(db)} songs")
            sys.exit(0)
    
    # Build fresh database
    database = build_database(use_pairs=True, threshold_db=10)
    
    if database:
        save_database(database)
        print("\n✅ Database ready for deployment!")
    else:
        print("\n❌ Failed to build database")
        sys.exit(1)
