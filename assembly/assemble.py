#!/usr/bin/env python3
"""
Ensamblado del vídeo (SPEC-MOTOR-VIDEO.md §4.3) — corre en el runner de GitHub Actions.
Entrada:  out/clip_*.mp4  +  out/voice/seg_*.mp3  +  scripts/video-01.json
Salida:   build/video-01.mp4  (1080x1920 · 30fps · H.264+AAC · -14 LUFS)

Qué hace (nada de texto IA — tipografía REAL, D-VM-04):
  1. por cada segmento: recorta/estira el clip AI a la duración del guion
  2. superpone titulares REALES (drawtext, fuente DejaVu) con estilo kinetic/typewriter
  3. quema subs EN karaoke (ASS) en zona segura
  4. convierte 24 -> 30 fps, upscale a 1080x1920, LUT de canal
  5. mezcla voz + música ducked y normaliza a -14 LUFS
Uso:  python3 assembly/assemble.py --spec scripts/video-01.json --in out --out build
"""
import argparse
import json
import os
import re
import subprocess
import sys

W, H, FPS = 1080, 1920, 30
SAFE_TOP, SAFE_BOT = 0.15, 0.85          # zona segura 85% central (§4.3)
FONT = "DejaVu Sans"
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def run(cmd, **kw):
    print("  $", " ".join(cmd)[:200])
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-4000:])
        raise SystemExit(f"ffmpeg falló ({r.returncode})")
    return r


def probe(path):
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", "-show_streams", path],
        capture_output=True, text=True)
    return json.loads(r.stdout or "{}")


def fit_clip(src, dur, tmp):
    """Escala el clip AI a 1080x1920, fija 30fps y lo ajusta a 'dur' segundos."""
    # scale con cover (mantiene ratio, centra) + crop a 1080x1920
    vf = (
        f"scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},fps={FPS},setsar=1,"
        # LUT de canal (ciber/teal-magenta) — fijo, reproducible
        f"eq=contrast=1.08:saturation=1.12:brightness=-0.02,"
        f"colorbalance=rs=-0.04:bs=0.06:rm=0.03:bm=-0.04"
    )
    # -stream_loop -1 buclea el clip si es más corto que 'dur' (ahorra GPU:
    # se generan clips de ~4s y se estiran por segmento); si es más largo, -t recorta.
    run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", src,
         "-vf", vf, "-t", str(dur), "-an",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-r", str(FPS), tmp])


def overlay_filter(text, size, y_pct, style, t_start, idx):
    """Construye drawtext con animación según estilo. y_pct = fracción de H."""
    px = {"xs": 34, "sm": 46, "md": 66, "lg": 96}[size]
    y = int(H * y_pct)
    color = "0x5EF1FF"          # teal ciber
    if style in ("mono", "typewriter"):
        color = "0x9BF5D6"
    if style == "endcard":
        color = "0xFFFFFF"

    # animación de entrada: fade+slide sencillo (kinetic)
    enable = f"between(t,{t_start:.3f},{t_start + 60:.3f})"
    parts = []
    # fondo sutil para legibilidad (caja semitransparente)
    draw = (
        f"drawtext=fontfile={FONT_PATH}:text='{text}':"
        f"fontsize={px}:fontcolor={color}:"
        f"borderw=3:bordercolor=black@0.7:"
        f"x=(w-text_w)/2:y={y}:"
        f"alpha='if(lt(t,{t_start}),0,if(lt(t,{t_start}+0.4),(t-{t_start})/0.4,1))':"
        f"enable='{enable}'"
    )
    parts.append(draw)
    return ",".join(parts)


def esc(text):
    """Escapa texto para drawtext/ASS."""
    t = text.replace("\\", "\\\\").replace("'", "’").replace(":", "\\:")
    t = t.replace("%", "\\%").replace(",", "\\,").replace("[", "\\[").replace("]", "\\]")
    return t


def build_ass(spec, segments, total_dur, path):
    """Genera subs EN karaoke en ASS, dentro de zona segura."""
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Kara,{FONT},54,&H00FFFFFF,&H005EF1FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,2,60,60,{int(H*0.08)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [head]
    for seg in segments:
        t0, t1 = seg["t_start"], seg["t_end"]
        words = seg["sub_en"].split()
        # karaoke: cada palabra iluminada proporcionalmente dentro del rango
        n = max(1, len(words))
        per = (t1 - t0) / n
        # Emitimos la frase entera con tags \k (centésimas de seg) por palabra
        kparts = []
        for w in words:
            kparts.append(f"{{\\k{int(per*100)}}}{w} ")
        txt = "".join(kparts)
        lines.append(
            f"Dialogue: 0,{fmt_t(t0)},{fmt_t(t1)},Kara,,0,0,0,,{txt}"
        )
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def fmt_t(s):
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = s % 60
    return f"{h}:{m:02d}:{sec:05.2f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--in", dest="indir", required=True)
    ap.add_argument("--out", dest="outdir", required=True)
    ap.add_argument("--voice-dir", default=None,
                    help="dir con seg_*.mp3 (si no, sin audio IA)")
    ap.add_argument("--music", default=None, help="lecho musical (mp3/wav)")
    args = ap.parse_args()

    spec = json.load(open(args.spec))
    segs = spec["segments"]
    os.makedirs(args.outdir, exist_ok=True)

    # --- localizar clips por id de segmento (clip A..E / ENDCARD) ------------
    clip_of = {}
    for seg in segs:
        key = seg["clip"]
        if key == "ENDCARD":
            clip_of[key] = None
            continue
        cands = [f for f in os.listdir(args.indir)
                 if f.startswith("clip_") and f.endswith(".mp4")]
        # emparejar por semilla/orden: usamos orden alfabético de salida
        clip_of[key] = None
    print("[assemble] segmentos:", len(segs))

    # Mapa simple: los clips se generan en orden A,B,C,D,E -> clip_00..clip_04
    # El workflow nombra los clips como clip_<seq>_<seed>.md5; aquí resolvemos
    # por posición de la lista out/clip_*.mp4 ordenada.
    clips = sorted(f for f in os.listdir(args.indir)
                   if f.startswith("clip_") and f.endswith(".mp4"))
    print("[assemble] clips encontrados:", clips)

    seg_clips = []   # (segment, ruta_clip_o_None)
    ci = 0
    for seg in segs:
        if seg["clip"] == "ENDCARD":
            seg_clips.append((seg, None))
        else:
            ruta = os.path.join(args.indir, clips[ci]) if ci < len(clips) else None
            seg_clips.append((seg, ruta))
            ci += 1

    # --- 1) preparar cada segmento (video solo, sin audio) -------------------
    part_files = []
    for i, (seg, clip) in enumerate(seg_clips):
        dur = seg["t_end"] - seg["t_start"]
        part = os.path.join(args.outdir, f"part_{i:02d}.mp4")
        if clip is None:
            # end-card estática generada por ffmpeg (sin IA, D-VM-04)
            gen_endcard(seg, dur, part)
        else:
            fit_clip(clip, dur, part)
        part_files.append((part, seg))

    # --- 2) concatenar con titulares + subs ---------------------------------
    concat = os.path.join(args.outdir, "concat.mp4")
    inputs = []
    for p, _ in part_files:
        inputs += ["-i", p]

    # construir filter_complex: concat + drawtext por segmento
    fc = []
    n = len(part_files)
    concat_in = "".join(f"[{i}:v]" for i in range(n))
    fc.append(f"{concat_in}concat=n={n}:v=1:a=0[vcat]")

    # drawtext: añadimos los overlays encima de vcat con tiempos absolutos
    draw_streams = []
    last = "vcat"
    idx = 0
    for i, (part, seg) in enumerate(part_files):
        for ov in seg.get("overlay", []):
            t = seg["t_start"]
            px = {"xs": 34, "sm": 46, "md": 66, "lg": 96}[ov["size"]]
            y = int(H * ov["y"])
            color = {"kinetic": "0x5EF1FF", "counter": "0x5EF1FF",
                     "typewriter": "0x9BF5D6", "mono": "0x9BF5D6",
                     "endcard": "0xFFFFFF"}.get(ov["style"], "0x5EF1FF")
            text = esc(ov["text"])
            dur = seg["t_end"] - seg["t_start"]
            f = (
                f"[{last}]drawtext=fontfile={FONT_PATH}:text='{text}':"
                f"fontsize={px}:fontcolor={color}:borderw=4:bordercolor=black@0.8:"
                f"x=(w-text_w)/2:y={y}:"
                f"enable='between(t,{seg['t_start']},{seg['t_end']})':"
                f"alpha='if(lt(t,{seg['t_start']}),0,if(lt(t,{seg['t_start']}+0.35),"
                f"(t-{seg['t_start']})/0.35,1))'"
                f"[v{idx}]"
            )
            draw_streams.append(f)
            last = f"v{idx}"
            idx += 1

    if draw_streams:
        fc.extend(draw_streams)
        final_video = f"[{last}]"
    else:
        final_video = "[vcat]"

    # --- 3) audio: voz por segmento + música ducked -------------------------
    have_voice = args.voice_dir and os.path.isdir(args.voice_dir)
    if have_voice:
        vfiles = sorted(f for f in os.listdir(args.voice_dir)
                        if f.startswith("seg_") and f.endswith((".mp3", ".wav")))
    else:
        vfiles = []

    build_inputs = inputs[:]
    if have_voice:
        for vf in vfiles:
            build_inputs += ["-i", os.path.join(args.voice_dir, vf)]

    if have_voice and len(vfiles) > 0:
        # delay de cada voz al inicio de su segmento + concat
        delays = []
        for i, (part, seg) in enumerate(part_files):
            if i < len(vfiles):
                delays.append(f"[{n + i}:a]adelay={int(seg['t_start']*1000)}"
                              f"|{int(seg['t_start']*1000)}[a{i}]")
        if delays:
            fc.extend(delays)
            aconcat_in = "".join(f"[a{i}]" for i in range(len(delays)))
            fc.append(f"{aconcat_in}concat=n={len(delays)}:v=0:a=1[voc]")
            audio_src = "[voc]"
        else:
            audio_src = None
    else:
        audio_src = None

    if args.music:
        build_inputs += ["-i", args.music]
        # música ducked bajo la voz (sidechain) o simplemente atenuada
        if audio_src:
            mi = len(build_inputs) - 1
            fc.append(f"[{mi}:a]volume=0.16[mus]")
            fc.append(f"{audio_src}[mus]amix=inputs=2:duration=first:"
                      f"dropout_transition=0:normalize=0[aout]")
        else:
            mi = len(build_inputs) - 1
            fc.append(f"[{mi}:a]volume=0.35[aout]")
    elif audio_src:
        fc.append(f"{audio_src}anull[aout]")

    total_dur = segs[-1]["t_end"]

    ass_path = os.path.join(args.outdir, "subs.ass")
    build_ass(spec, segs, total_dur, ass_path)

    out_final = os.path.join(args.outdir, "video-01-raw.mp4")

    cmd = ["ffmpeg", "-y"] + build_inputs
    cmd += ["-filter_complex", ";".join(fc)]
    if audio_src or args.music:
        cmd += ["-map", final_video, "-map", "[aout]"]
    else:
        cmd += ["-map", final_video]
    cmd += ["-t", str(total_dur),
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-pix_fmt", "yuv420p", "-r", str(FPS),
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart",
            out_final]
    run(cmd)

    # --- 4) quemar subs ASS + normalizar -14 LUFS ---------------------------
    out_final2 = os.path.join(args.outdir, "video-01-subbed.mp4")
    run(["ffmpeg", "-y", "-i", out_final,
         "-vf", f"ass={ass_path}",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-r", str(FPS),
         "-c:a", "copy", "-movflags", "+faststart", out_final2])

    final = os.path.join(args.outdir, "video-01.mp4")
    run(["ffmpeg", "-y", "-i", out_final2,
         "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", final])

    print("[assemble] OK ->", final)


def gen_endcard(seg, dur, out):
    """End-card estática 1080x1920 con drawtext (sin IA)."""
    txt = seg["overlay"][0]["text"] if seg.get("overlay") else "FIN"
    sub = seg["overlay"][1]["text"] if len(seg.get("overlay", [])) > 1 else ""
    f = (
        f"color=c=0x05060a:s={W}x{H}:d={dur}:r={FPS}[bg];"
        f"[bg]drawtext=fontfile={FONT_PATH}:text='{esc(txt)}':"
        f"fontsize=88:fontcolor=white:x=(w-text_w)/2:y={int(H*0.40)}"
        f"[t1];"
        f"[t1]drawtext=fontfile={FONT_PATH}:text='{esc(sub)}':"
        f"fontsize=40:fontcolor=0x5EF1FF:x=(w-text_w)/2:y={int(H*0.50)}[v]"
    )
    run(["ffmpeg", "-y", "-filter_complex", f, "-map", "[v]",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-t", str(dur), out])


if __name__ == "__main__":
    main()
