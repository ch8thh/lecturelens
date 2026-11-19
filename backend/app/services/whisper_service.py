"""Speech-to-text using faster-whisper (runs locally, no API key needed).

The model is big (~140 MB on disk, loaded into RAM), so we load it ONCE the
first time transcribe() is called and reuse it for every later request.
"""
import threading

from faster_whisper import WhisperModel

MODEL_SIZE = "base"
DEVICE = "cpu"
COMPUTE_TYPE = "int8"  # int8 = smaller + faster on CPU, tiny accuracy loss

_model: WhisperModel | None = None
_lock = threading.Lock()  # stops two simultaneous requests loading it twice


def _get_model() -> WhisperModel:
    """Lazy singleton: load on first use, then return the same object."""
    global _model
    if _model is None:
        with _lock:
            if _model is None:  # re-check: another thread may have loaded it
                _model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
    return _model


def transcribe(file_path: str) -> str:
    """Transcribe an audio file and return the plain text.

    Returns "" if no speech was found (the route turns that into a 400).
    The language is auto-detected. Decoding mp3/wav/m4a is handled by PyAV,
    which ships with faster-whisper, so no separate ffmpeg install is needed.
    """
    model = _get_model()
    # vad_filter skips silence, which also reduces made-up text on quiet audio.
    # `segments` is a lazy generator: the actual work happens as we iterate.
    segments, _info = model.transcribe(file_path, vad_filter=True)
    return " ".join(seg.text.strip() for seg in segments).strip()
