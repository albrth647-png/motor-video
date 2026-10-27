#!/usr/bin/env python3
"""
scripts/reveal.py — modo `reveal`: la pantalla NO cambia; los elementos entran con la voz.

🛡️ Por qué existe (prueba del 2026-10-27, caso #2):
   El referente visual no corta de pantalla en pantalla: mantiene UNA escena (fondo +
   título) y dentro de ella van apareciendo tarjetas, flechas y etiquetas **cuando la
   voz dice su palabra**. Este módulo es esa pieza: convierte `cue` (una palabra del
   guion) en un instante exacto usando el `words.json` de edge-tts, y monta el vídeo
   con overlays de alfa (fade), sin `concat` de planos estáticos.

🔒 Fuente única: `build_nb.py` inyecta ESTE FICHERO tal cual en la celda del kernel y
   `scripts/preview_reveal.py` lo importa en local. Una función, dos consumidores:
   el preview y el render de Kaggle no se pueden desincronizar.

Solo stdlib (el kernel de Kaggle no tiene internet ni dependencias extra).
"""
import subprocess
import unicodedata
from pathlib import Path

FADE_IN = 0.28      # el elemento entra en 0,28 s (el "pop" suave del referente)
FADE_OUT = 0.30     # y se va en 0,30 s al cambiar de escena (fundido, nunca corte)


def norm(w: str) -> str:
    """Misma normalización que el motor: sin acentos ni puntuación."""
    w = unicodedata.normalize("NFD", w.lower())
    return "".join(c for c in w if c.isalnum())


def reveal_plan(words, escenas, total):
    """Resuelve cada `cue` a un tiempo real y reparte las escenas.

    Devuelve (elems, esc_t, t_end):
      elems  [(escena, png, t_in, t_out)]   el PNG ya con su ventana de vida
      esc_t  [(escena, t0, t1)]             tramos contiguos que cubren todo el vídeo
      t_end  inicio de la última escena (la placa del endcard)
    """
    flat = [norm(w["w"]) for w in words]
    ptr = 0
    cues = []
    for sc in escenas:
        for el in sc["elementos"]:
            k = norm(el["cue"])
            f = next((i for i in range(ptr, len(words)) if flat[i] == k), None)
            if f is None:
                raise SystemExit(
                    "cue %r no encontrado (escena %s, elemento %s) · las siguientes palabras son %r"
                    % (el["cue"], sc["id"], el["id"], [w["w"] for w in words[ptr:ptr + 8]])
                )
            cues.append((sc["id"], el["id"], words[f]["t0"], float(el.get("d", 0.0))))
            ptr = f

    starts = []
    for sc in escenas:
        ts = [c[2] + c[3] for c in cues if c[0] == sc["id"]]
        starts.append(min(ts))
    for a, b in zip(starts, starts[1:]):
        if b <= a:
            raise SystemExit("escenas desordenadas: %r no puede empezar antes que la anterior" % (b,))

    esc_t = []
    for i, sc in enumerate(escenas):
        t0 = round(starts[i], 3)
        t1 = round(starts[i + 1], 3) if i + 1 < len(escenas) else round(total, 3)
        esc_t.append((sc["id"], t0, t1))

    elems = []
    for sid, eid, t, d in cues:
        t1 = next(e[2] for e in esc_t if e[0] == sid)
        elems.append((sid, "el_%s.png" % eid, round(t + d, 3), t1))
    return elems, esc_t, esc_t[-1][1]


def build_filter(items, t0):
    """Filtro de UNA escena: base fija + un overlay con fade alfa por elemento.

    `items` = [(png, t_in_abs, t_out_abs)] · `t0` = inicio de la escena (los tiempos
    de los inputs empiezan en 0). Sin `enable` ni cortes: el alfa hace la entrada.
    """
    parts = ["[0:v]format=yuv420p,setsar=1[base]"]
    prev = "base"
    for i, (png, tin, tout) in enumerate(items, start=1):
        fi = FADE_IN
        fo = min(FADE_OUT, max(0.10, (tout - tin) - 0.05))
        st_out = max(0.0, (tout - t0) - fo)
        parts.append(
            "[%d:v]format=rgba,fade=t=in:st=%.3f:d=%.2f:alpha=1,fade=t=out:st=%.3f:d=%.2f:alpha=1[e%d]"
            % (i, max(0.0, tin - t0), fi, st_out, fo, i)
        )
        parts.append("[%s][e%d]overlay=0:0:format=auto[v%d]" % (prev, i, i))
        prev = "v%d" % i
    return ";".join(parts), prev


def reveal_montage(out_dir, base_img, elems, esc_t, img_dir=None, fps=30, crf=19, preset="medium", quiet=True):
    """Un mp4 por escena (fondo fijo + sus overlays) y concat sin recodificar.

    Ventaja frente a `concat` de planos: el fondo NO cambia entre escenas, así que
    el ojo no ve cortes; solo ve entrar y salir elementos.

    `img_dir` = donde están los PNG (el dataset, solo lectura) · `out_dir` = donde se
    escriben los mp4 (siempre escribible).
    """
    out = Path(out_dir)
    img = Path(img_dir) if img_dir else out
    segs = []
    # el tramo del intro (0 -> primera escena) va SIN elementos: lo dibuja el ASS
    tramos = list(esc_t)
    if tramos and tramos[0][1] > 0.01:
        tramos = [("_intro", 0.0, tramos[0][1])] + tramos
    for si, (sid, t0, t1) in enumerate(tramos):
        dur = round(t1 - t0, 3)
        if dur <= 0:
            continue
        mine = [e for e in elems if e[0] == sid]
        cmd = ["ffmpeg", "-y", "-loop", "1", "-framerate", str(fps), "-t", str(dur),
               "-i", str(img / base_img)]
        for (_sid, png, _ti, _to) in mine:
            cmd += ["-loop", "1", "-framerate", str(fps), "-t", str(dur), "-i", str(img / png)]
        filt, last = build_filter([(p, ti, to) for (_s, p, ti, to) in mine], t0)
        dst = out / ("rv_%02d.mp4" % si)
        cmd += ["-filter_complex", filt, "-map", "[%s]" % last, "-t", str(dur),
                "-r", str(fps), "-c:v", "libx264", "-crf", str(crf), "-preset", preset,
                "-pix_fmt", "yuv420p", "-an", str(dst)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit("fallo escena %s: %s" % (sid, r.stderr[-400:]))
        segs.append(dst)
        print("  escena %s %6.2f-%6.2f s · %d elementos · %s" % (sid, t0, t1, len(mine), dst.name))

    lst = out / "rv.txt"
    lst.write_text("".join("file '%s'\n" % p for p in segs))
    r = subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                        "-c", "copy", str(out / "video.mp4")], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("fallo concat: %s" % r.stderr[-400:])
    print("  montaje reveal: %d escenas -> video.mp4" % len(segs))
    return out / "video.mp4"
