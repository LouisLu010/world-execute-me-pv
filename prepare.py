"""Prepare the supplied soundtrack and a measured, frame-addressable spectrum."""
from __future__ import annotations

import argparse
import json
import subprocess
import urllib.request
from pathlib import Path

import imageio_ffmpeg
import numpy as np

ROOT = Path(__file__).resolve().parent


def prepare(source: Path) -> None:
    for name in ("input", "data", "out"):
        (ROOT / name).mkdir(exist_ok=True)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    soundtrack = ROOT / "input/soundtrack.m4a"
    subprocess.run([ff, "-v", "error", "-y", "-i", str(source), "-map", "0:a:0", "-vn",
                    "-c:a", "copy", str(soundtrack)], check=True)
    raw = subprocess.check_output([ff, "-v", "error", "-i", str(soundtrack), "-ac", "1", "-ar", "22050",
                                   "-f", "f32le", "-"])
    pcm = np.frombuffer(raw, dtype="<f4")
    rate, sr, nfft = 48, 22050, 2048
    count = int(len(pcm) / sr * rate)
    pos = np.arange(count) * sr // rate
    padded = np.pad(pcm, (nfft // 2, nfft))
    windows = padded[pos[:, None] + np.arange(nfft)]
    rms = np.sqrt(np.mean(windows * windows, axis=1))
    spectrum = np.abs(np.fft.rfft(windows * np.hanning(nfft), axis=1))
    freq = np.fft.rfftfreq(nfft, 1 / sr)
    edges = np.geomspace(45, 10000, 33)
    masks = []
    for a, b in zip(edges[:-1], edges[1:]):
        mask = (freq >= a) & (freq < b)
        if not mask.any():
            mask[np.argmin(abs(freq - (a + b) / 2))] = True
        masks.append(mask)
    bands = np.stack([np.mean(spectrum[:, mask], axis=1) for mask in masks], axis=1)
    bands = np.clip(bands / np.maximum(np.quantile(bands, .97, axis=0), 1e-6), 0, 1)
    rms = np.clip(rms / np.quantile(rms, .98), 0, 1)
    onset = np.maximum(0, rms - np.r_[rms[0], rms[:-1]])
    onset = np.clip(onset / max(np.quantile(onset, .97), 1e-6), 0, 1)
    np.savez_compressed(ROOT / "data/audio_features.npz", rate=rate, rms=rms, bands=bands, onset=onset)
    info = {"source": str(source), "audio": "input/soundtrack.m4a", "audio_codec": "AAC (stream copy)",
            "duration": len(pcm) / sr, "feature_rate": rate, "music": "Mili — world.execute(me);",
            "note": "Original supplied audio, including its final notification sound; no added speech."}
    (ROOT / "data/source.json").write_text(json.dumps(info, ensure_ascii=False, indent=2))
    lyrics = ROOT / "data/lyrics.json"
    if not lyrics.exists():
        req = urllib.request.Request("https://lrclib.net/api/get/36914646", headers={"User-Agent": "gpt-pv/1.0"})
        with urllib.request.urlopen(req, timeout=40) as response:
            data = json.load(response)
        lyrics.write_text(json.dumps({"id": data["id"], "syncedLyrics": data["syncedLyrics"]}, ensure_ascii=False))
    print(json.dumps(info, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", type=Path)
    prepare(ap.parse_args().source)
