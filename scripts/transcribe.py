#!/usr/bin/env python3
"""Transcribe audio with faster-whisper. Usage: transcribe.py <audio.wav> <project-dir> [model]"""
import json, sys, wave
import numpy as np
from pathlib import Path
from faster_whisper import WhisperModel

if len(sys.argv) < 3:
    sys.exit("usage: transcribe.py <audio.wav (16 kHz mono)> <project-dir> [model, default small.en]")
audio, proj = sys.argv[1], Path(sys.argv[2])
model = WhisperModel(sys.argv[3] if len(sys.argv) > 3 else "small.en", device="auto", compute_type="int8")
# Read the 16 kHz mono WAV directly (avoids PyAV version issues in faster-whisper's decoder).
with wave.open(audio) as w:
    pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
segs, info = model.transcribe(pcm, word_timestamps=True, vad_filter=True)
out = []
for s in segs:
    out.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip(),
                "avg_logprob": round(s.avg_logprob, 3), "no_speech_prob": round(s.no_speech_prob, 3)})
(proj / "transcript.json").write_text(json.dumps({"language": info.language, "language_probability": info.language_probability, "segments": out}, ensure_ascii=False, indent=1))
(proj / "transcript.txt").write_text("\n".join(f"[{s['start']:.1f}-{s['end']:.1f}] {s['text']}" for s in out))
print(f"{len(out)} segments, language={info.language}")
