#!/usr/bin/env python3
"""
Deployment helper: auto-load the pre-built song database on app startup.

This is what makes "the indexed song database ships with the deployed app
so it works immediately" (per the assignment's submission guidelines)
actually true: on first load we try a pickled, pre-indexed database
(song_database.pkl) that is committed alongside the code. Only if that's
missing do we fall back to indexing the raw song files from scratch
(which takes several minutes for a full 50-song library).
"""
import os
import pickle
import streamlit as st

DATABASE_CACHE = "song_database.pkl"
# The song library as provided (unmodified filenames, per assignment rules).
# Supports either an mp3 folder or a wav folder -- whichever is present.
SONGS_DIRS = ["songs_mp3", "songs_wav", "songs"]


@st.cache_resource
def load_or_build_database():
    """Load the pre-built database shipped with the app, or build it once."""

    # 1) Fast path: load the pre-built, pre-indexed database.
    if os.path.exists(DATABASE_CACHE):
        try:
            with open(DATABASE_CACHE, 'rb') as f:
                database = pickle.load(f)
            if database:
                st.sidebar.success(f"📦 Loaded pre-indexed database ({len(database)} songs)")
                return database
        except Exception as e:
            st.sidebar.warning(f"Could not load cached database ({e}); rebuilding...")

    # 2) Fallback: build from the raw song files shipped with the repo.
    #    (Only hit if song_database.pkl wasn't committed/found.)
    from project import MusicFingerprinter

    songs_dir = next((d for d in SONGS_DIRS if os.path.isdir(d) and os.listdir(d)), None)
    if songs_dir is None:
        st.error(
            "No pre-built database and no song folder found. Ship "
            f"'{DATABASE_CACHE}' (preferred) or one of {SONGS_DIRS} with the app."
        )
        return {}

    st.sidebar.warning(
        f"No '{DATABASE_CACHE}' found — indexing songs from '{songs_dir}/' now. "
        "This can take several minutes for a full library; consider committing "
        "the pre-built .pkl instead."
    )
    fingerprinter = MusicFingerprinter()
    database = fingerprinter.build_database(songs_dir, use_pairs=True)

    if database:
        try:
            with open(DATABASE_CACHE, 'wb') as f:
                pickle.dump(database, f)
        except Exception as e:
            st.sidebar.warning(f"Could not save database cache: {e}")
        st.sidebar.success(f"📦 Built database ({len(database)} songs)")
    else:
        st.sidebar.error(f"No songs indexed from '{songs_dir}/'.")

    return database
