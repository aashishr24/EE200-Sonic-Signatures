# Fixes applied to this project

This documents every change made from the originally-submitted version, and why.

## 1. Core bug: offset/alignment tracking was hardcoded to 0 (`project.py`)

**Before:** `build_database()` stored `time_offset = 0` for every fingerprint,
and `match_query()` always incremented `offset_histogram[0]`, regardless of
where in a song a match actually occurred. This meant matching was really
just "count of raw hash collisions" — there was no way to check that matching
hashes agreed on a single, consistent time alignment, which is the entire
point of Shazam-style fingerprinting.

**Impact (measured against the real 50-song database):** the identifier
started failing at ~25 dB SNR (very mild noise) and, worse, failed
*confidently wrong* rather than becoming uncertain, because there was no
alignment-consensus filter to reject coincidental collisions.

**Fix:**
- `create_fingerprint_pairs()` / `create_single_peak_fingerprints()` now
  return `(fingerprint, anchor_time_seconds)` pairs instead of bare
  fingerprints, so the real time of each occurrence is preserved.
- `build_database()` stores the real anchor time for every fingerprint
  occurrence.
- `match_query()` computes `offset = db_time - query_time` for every
  matching hash, buckets these into a real offset histogram (0.2s bins),
  and the **score is the height of the tallest bin** (i.e. how many hashes
  agree on one alignment), not the total collision count.

**Verified after the fix** (real songs, real noise):
- Clean 10s clip from t=60s of "Yesterday": best_offset correctly comes back
  as `60.0`, score 1877 vs. next-best score of 6 (previously: score 2079 vs.
  651 — a much weaker margin, using the broken metric).
- Noise robustness: correct identification 3/3 trials down to 0 dB SNR
  (previously: wrong 3/3 trials at 25 dB and below).
- Offset histogram shape now matches what the assignment describes: a
  correct match produces one sharp spike at the true offset; a wrong song
  produces small, scattered bars across many offsets (see
  `offset_histogram_fixed_comparison.png`).
- Pitch shift is still fragile (as expected/correctly explained in the
  original report) since it changes the frequency values themselves, not
  just the alignment — that's inherent to peak-based fingerprinting, not a
  bug.

Same bug (`.append(0)` / `offset_histogram[0] += 1`-equivalent) was also
present, independently duplicated, in `ss.py`, `build_database.py`,
`demo.py`, `fast_analysis.py`, and `minimal_analysis.py`. All fixed the
same way.

## 2. MP3 support (`project.py`)

`load_audio()` only handled `.wav`. The actual provided song database is
`.mp3`. Added a pydub/ffmpeg-based path for `.mp3` (and other compressed
formats), with automatic resampling to a consistent target sample rate.

## 3. App didn't ship a pre-built database (`ss.py`, `db_loader.py`)

The submission guidelines require the deployed app to work immediately with
the indexed database already shipped. Previously, `db_loader.py` (which
does exactly this) existed but was never imported/used by `ss.py` — the app
required a human to manually re-upload and rebuild the database every
session, which also only accepted `.wav` (not the provided `.mp3` files).

**Fix:** `ss.py` now calls `db_loader.load_or_build_database()` on startup,
which loads the pre-built `song_database.pkl` shipped alongside the app.
All three file uploaders (build/query/batch) now accept both `.wav` and
`.mp3`.

## 4. Fabricated fallback numbers (`generate_plots.py`)

Removed hardcoded "realistic" scores (92, 24) that were used as a silent
fallback if the real score computation failed. Real computation should
either work or fail loudly — never fake the numbers.

## 5. Pairing based on time order, not list order (`project.py`)

`create_fingerprint_pairs()` paired each peak with the next few entries in
whatever order `find_peaks()` happened to emit them, not the next few
peaks in time. Peaks are now sorted by time before pairing, so "nearby
peaks" genuinely means temporally nearby.

## Not fixed (flagged, not changed)
- `find_peaks()` is still a nested Python double-loop (~9-13s per song).
  Works correctly, just slow (~15 min to index all 50 songs). Since the
  fix ships a pre-built `song_database.pkl`, this doesn't block the
  deployed app working immediately — it would only matter if you rebuild
  the database from scratch.
