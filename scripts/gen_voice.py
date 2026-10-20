#!/usr/bin/env python3
"""
scripts/gen_voice.py — genera la voz (voz.mp3) y las marcas de palabra (words.json).

🛡️ Por qué existe y por qué corre AQUÍ (en CI) y no en el kernel:
   · Kaggle **no tiene internet** en esta cuenta → edge-tts no puede correr allí.
   · En GitHub Actions sí hay internet → la voz se sintetiza en el runner y se
     sube al dataset `motor-media`. El móvil **no gasta un byte**.

🔒 Fuente única: `scripts/video-01.json`
   · el texto = las 8 frases `phrases[].voice_es` concatenadas
   · la voz y el rate = `voice.voice_id` / `voice.rate`
   · build_nb.py (que genera el notebook) lee EL MISMO JSON → el audio y el
     subtitulado no se pueden desincronizar.

Uso:  python3 scripts/gen_voice.py --spec scripts/video-01.json --out /tmp/media
"""
import argparse
import asyncio
import json
import unicodedata
from pathlib import Path

import edge_tts


def norm(w: str) -> str:
    """Misma normalización que el motor (build_nb.py): sin acentos ni puntuación."""
    w = unicodedata.normalize("NFD", w.lower())
    return "".join(c for c in w if c.isalnum())


async def run(spec_path: str, out_dir: str) -> None:
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    text = " ".join(p["voice_es"] for p in spec["phrases"])
    voice = spec["voice"]["voice_id"]
    rate = spec["voice"]["rate"]

    words: list[dict] = []
    mp3 = out / "voz.mp3"
    comm = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    with open(mp3, "wb") as f:
        async for ch in comm.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                words.append(
                    {
                        "w": ch["text"],
                        "t0": ch["offset"] / 1e7,
                        "t1": (ch["offset"] + ch["duration"]) / 1e7,
                    }
                )

    (out / "words.json").write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")

    print(f"· voz: {voice} {rate} · {mp3.stat().st_size} bytes · {len(words)} palabras")
    print(f"· texto: {len(text.split())} palabras · {len(spec['phrases'])} frases")

    # Verificación: los marcadores de fin de frase tienen que estar EN el audio,
    # en orden. Si no, el motor no puede clavar los tramos y el vídeo sale mal.
    flat = [norm(w["w"]) for w in words]
    pos = 0
    faltan: list[str] = []
    for lw in spec["voice"]["marks_lastw"]:
        try:
            pos = flat.index(norm(lw), pos) + 1
        except ValueError:
            faltan.append(lw)
    if faltan:
        raise SystemExit(f"❌ marcadores de frase ausentes en el audio: {faltan}")
    print("· marcadores LASTW: todos presentes y en orden ✓")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default="scripts/video-01.json")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    asyncio.run(run(a.spec, a.out))


if __name__ == "__main__":
    main()
