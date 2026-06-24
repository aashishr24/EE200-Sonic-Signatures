"""
Convert MP3 files to WAV format using librosa.
"""

import os
import sys
import librosa
from scipy.io import wavfile
import numpy as np

def convert_mp3_to_wav(mp3_path, wav_path, sr=22050):
    """Convert MP3 to WAV using librosa."""
    try:
        # Load audio with librosa
        audio, sr_loaded = librosa.load(mp3_path, sr=sr, mono=True)
        
        # Convert to int16
        audio_int16 = np.int16(audio / np.max(np.abs(audio)) * 32767)
        
        # Save as WAV
        wavfile.write(wav_path, sr, audio_int16)
        return True
    except Exception as e:
        print(f"    Error: {e}")
        return False

def main():
    songs_dir = "/workspaces/EE200/songs"
    wav_dir = "/workspaces/EE200/songs_wav"
    
    # Create output directory
    os.makedirs(wav_dir, exist_ok=True)
    
    # Get all MP3 files
    mp3_files = [f for f in os.listdir(songs_dir) if f.endswith('.mp3')]
    mp3_files.sort()
    
    print(f"\n{'='*70}")
    print(f"Converting {len(mp3_files)} MP3 files to WAV format")
    print(f"{'='*70}\n")
    
    successful = 0
    failed = 0
    skipped = 0
    
    for idx, mp3_file in enumerate(mp3_files, 1):
        mp3_path = os.path.join(songs_dir, mp3_file)
        wav_file = mp3_file.replace('.mp3', '.wav')
        wav_path = os.path.join(wav_dir, wav_file)
        
        # Skip if already converted
        if os.path.exists(wav_path):
            print(f"[{idx:2d}/{len(mp3_files)}] {mp3_file:45s} ✓ (exists)")
            skipped += 1
            continue
        
        # Convert
        print(f"[{idx:2d}/{len(mp3_files)}] {mp3_file:45s}", end=' ')
        
        if convert_mp3_to_wav(mp3_path, wav_path):
            print(f"✓")
            successful += 1
        else:
            print(f"✗")
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"Conversion Summary:")
    print(f"  ✓ Converted: {successful}")
    print(f"  ✓ Already existed: {skipped}")
    print(f"  ✗ Failed: {failed}")
    print(f"  Total: {successful + skipped + failed}/{len(mp3_files)}")
    print(f"  Output directory: {wav_dir}")
    print(f"{'='*70}\n")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
