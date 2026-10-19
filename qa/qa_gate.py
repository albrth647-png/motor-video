#!/usr/bin/env python3
"""
QA-gate bloqueante (SPEC-MOTOR-VIDEO.md §7 / R6).
Si CUALQUIER check falla -> exit 1 -> el workflow NO sube el mp4 a Artifacts.
Checks: resolución · fps · duración · codec · pixel format · LUFS · streams · faststart.

Uso:  python3 qa/qa_gate.py build/video-01.mp4 [duracion_esperada_s]
"""
import json
import re
import subprocess
import sys

MAX_DUR = 60
MIN_DUR = 20  # piso anti-truncado (short congelado v8 = 49,07 s; SPEC v1.2)
LUFS_TARGET = -14
LUFS_TOL = 1.0
W, H, FPS = 1080, 1920, 30


def probe(path):
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", "-show_streams", path],
        capture_output=True, text=True)
    return json.loads(r.stdout or "{}")


def measure_lufs(path):
    """ebur128 -> loudness integrado."""
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", path,
         "-map", "0:a:0", "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True)
    m = re.findall(r"I:\s+(-?\d+\.?\d*)\s*LUFS", r.stderr)
    if not m:
        return None
    return float(m[-1])


def moov_first(path):
    """faststart: el átomo moov debe ir antes que mdat."""
    with open(path, "rb") as f:
        head = f.read(64 * 1024)
    return head.find(b"moov") != -1 and (
        head.find(b"mdat") == -1 or head.find(b"moov") < head.find(b"mdat"))


def main():
    if len(sys.argv) not in (2, 3):
        raise SystemExit("uso: qa_gate.py <mp4> [duracion_esperada_s]")
    path = sys.argv[1]
    expected = float(sys.argv[2]) if len(sys.argv) > 2 else None
    p = probe(path)
    errors = []

    streams = p.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), None)
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)

    if not v:
        errors.append("sin stream de vídeo")
    if not a:
        errors.append("sin stream de audio")

    if v:
        w, h = int(v.get("width", 0)), int(v.get("height", 0))
        if (w, h) != (W, H):
            errors.append(f"resolución {w}x{h} != {W}x{H}")
        if v.get("codec_name") != "h264":
            errors.append(f"codec vídeo {v.get('codec_name')} != h264")
        if v.get("pix_fmt") != "yuv420p":
            errors.append(f"pix_fmt {v.get('pix_fmt')} != yuv420p")
        # fps: r_frame_rate o avg_frame_rate
        fr = v.get("avg_frame_rate") or v.get("r_frame_rate") or "0/1"
        num, den = fr.split("/")
        fps = float(num) / float(den or 1)
        if abs(fps - FPS) > 0.5:
            errors.append(f"fps {fps:.2f} != {FPS}")

    if a and a.get("codec_name") != "aac":
        errors.append(f"codec audio {a.get('codec_name')} != aac")

    dur = float(p.get("format", {}).get("duration", 0))
    if dur <= 0:
        errors.append("duración ilegible")
    elif dur > MAX_DUR:
        errors.append(f"duración {dur:.1f}s > {MAX_DUR}s")
    elif dur < MIN_DUR:
        errors.append(f"duración {dur:.1f}s < {MIN_DUR}s (video incompleto)")
    if expected is not None and abs(dur - expected) > 2.0:
        errors.append(f"duración {dur:.1f}s != esperada {expected:.1f}±2s")

    lufs = measure_lufs(path)
    if lufs is None:
        errors.append("no se pudo medir LUFS")
    elif abs(lufs - LUFS_TARGET) > LUFS_TOL:
        errors.append(f"LUFS {lufs:.1f} fuera de {LUFS_TARGET}±{LUFS_TOL}")

    if not moov_first(path):
        errors.append("sin faststart (moov tras mdat)")

    report = {
        "file": path,
        "duration_s": round(dur, 2),
        "lufs": lufs,
        "ok": not errors,
        "errors": errors,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if errors:
        print("\n❌ QA-GATE: BLOQUEADO", file=sys.stderr)
        sys.exit(1)
    print("\n✅ QA-GATE: OK")


if __name__ == "__main__":
    main()
