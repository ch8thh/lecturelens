"""Standalone check that transcription works, with no API code involved.

Run from the backend/ folder:
    python scripts/test_whisper.py path/to/sample.mp3
"""
import sys
import time
from pathlib import Path

# Make `app` importable when running this file directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.whisper_service import transcribe  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/test_whisper.py <audio-file>")
        return 1
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"File not found: {path}")
        return 1

    print("Loading model + transcribing (first run downloads ~140 MB)...")
    start = time.time()
    text = transcribe(str(path))
    print(f"\nDone in {time.time() - start:.1f}s")
    print("-" * 40)
    print(text or "(empty transcript: no speech detected)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
