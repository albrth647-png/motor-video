#!/usr/bin/env python3
"""
B-roll PROCEDURAL (sustituye a los clips Wan de Modal cuando NO hay tarjeta en Modal).
Genera fondos cyber animados con ffmpeg puro -> $0, sin GPU, corre en el runner.

Capas: gradiente teal/magenta animado · rejilla synthwave · scanline barrido
       · hex flotante (tipografía real, DejaVu Mono) · grano · viñeta

Cuando haya tarjeta en Modal: sustituye este módulo por descarga de los clips
Wan del Volume (mismo esquema de nombres clip_A..clip_E) — el ensamblado no cambia.

Uso:  python3 assembly/broll.py --spec scripts/video-01.json --out out/
"""
import argparse
import json
import os
import subprocess
import sys

W, H, FPS = 1080, 1920, 30
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Paletas por segmento (variación sutil, misma familia ciber)
PALETTES = {
    "A": ("0x05060a", "0x083b4a", "0x12122a", "0x3a0f4a"),   # hook
    "B": ("0x04060c", "0x0a2f52", "0x0e1a33", "0x2a0a3e"),   # objetivo
    "C": ("0x060510", "0x0f3a52", "0x161436", "0x401046"),   # proceso
    "D": ("0x05070c", "0x0c4050", "0x141230", "0x360d4c"),   # hallazgo
    "E": ("0x06060a", "0x0a3040", "0x12122c", "0x2e0c40"),   # limites
}
HEXES = {
    "A": ["0x9b", "0xf1", "0xff", "0x35", "0x7a", "0x2c"],
    "B": ["0x2e", "0x8b", "0xf4", "0x1d", "0xa7", "0x53"],
    "C": ["0x3d", "0x9e", "0xc0", "0x71", "0x4a", "0xb2"],
    "D": ["0x1c", "0x6f", "0xe1", "0x88", "0x2b", "0x5d"],
    "E": ["0x4a", "0xd3", "0xf9", "0x09", "0x7e", "0x36"],
}


def run(cmd):
    print("  $", " ".join(cmd)[:220])
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-4000:])
        raise SystemExit(f"ffmpeg falló ({r.returncode})")


def hex_string(key, t):
    """Cadena hex decorativa para drawtext (cambia cada ~1.5s)."""
    cells = HEXES.get(key, HEXES["A"])
    step = int(t / 1.5)
    out = []
    for i in range(8):
        out.append(cells[(step + i * 3) % len(cells)])
    return " ".join(out) + "  " + " ".join(
        cells[(step + i * 2 + 1) % len(cells)] for i in range(4))


def make_bg(key, dur, seed, out):
    c0, c1, c2, c3 = PALETTES.get(key, PALETTES["A"])
    # hex decorativo (constante por clip; el "cambio" lo da el scanline y gradiente)
    sample = " ".join(hex_string(key, 0).split()[:8])

    # filtro base: gradiente animado + rejilla + viñeta + grano
    fc = (
        # 1) gradiente oscuro animado (radial, gira lento)
        f"gradients=s={W}x{H}:r={FPS}:d={dur}:"
        f"nb_colors=4:c0={c0}:c1={c1}:c2={c2}:c3={c3}:"
        f"speed=0.02:type=radial:seed={seed}[bg];"
        # 2) rejilla synthwave sutil
        f"[bg]drawgrid=w=120:h=120:t=1:c=0x5EF1FF@0.10[grid];"
        # 3) scanline: barra clara que barre hacia abajo (geq solo en banda estrecha
        #    -> barato: usamos drawbox animado con enable+expresión y)
        f"[grid]drawbox=x=0:y='mod(t*{H}*0.35,{H})':w={W}:h=60:"
        f"c=0x9BF5D6@0.06:t=fill[scan];"
        # 4) hex flotante real (tipografía mono) arriba, tenue
        f"[scan]drawtext=fontfile={MONO}:text='{sample}':"
        f"fontsize=30:fontcolor=0x5EF1FF@0.16:"
        f"x=40:y='mod(-t*40+{H}*0.2,{H})':"
        f"line_spacing=18[hex];"
        # 5) segunda capa hex en sentido contrario (profundidad)
        f"[hex]drawtext=fontfile={MONO}:text='{sample}':"
        f"fontsize=24:fontcolor=0x9BF5D6@0.12:"
        f"x='{W}-40-text_w':y='mod(t*30+{H}*0.55,{H})'[hex2];"
        # 6) grano temporal + viñeta + contraste
        f"[hex2]noise=alls=8:allf=t+u[n];"
        f"[n]vignette=PI/4.2,eq=contrast=1.12:saturation=1.15:brightness=-0.03[v]"
    )

    run([
        "ffmpeg", "-y",
        "-filter_complex", fc,
        "-map", "[v]",
        "-t", str(dur),
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", str(FPS),
        out,
    ])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    spec = json.load(open(args.spec))
    os.makedirs(args.out, exist_ok=True)

    for seg in spec["segments"]:
        key = seg["clip"]
        if key == "ENDCARD":
            continue  # end-card la hace assemble.py (estática, sin IA)
        dur = seg["t_end"] - seg["t_start"]
        seed = spec.get("clips", {}).get(key, {}).get("seed", 42)
        out = os.path.join(args.out, f"clip_{key}.mp4")
        print(f"[broll] {key} · {dur}s · seed {seed} -> {out}")
        make_bg(key, dur, seed, out)

    print("[broll] OK")


if __name__ == "__main__":
    main()
