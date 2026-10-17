"""
Voz (edge-tts) — app SIN GPU de Modal.
Separada de modal_app.py porque Modal exige método de pago para desplegar
cualquier app que contenga funciones GPU (bloqueo detectado 2026-10-17:
"Please add a payment method to use A10G GPU functions").

Uso:
    modal run app/voice_app.py::smoke_voice_only   # valida edge-tts ($0)
    modal run app/voice_app.py::gen                # TTS de todo el guion
"""
import asyncio
import os
import modal

assets = modal.Volume.from_name("video-engine-assets", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("edge-tts>=6.1.0")
)

app = modal.App("video-engine-voice", image=image)


@app.function(volumes={"/assets": assets}, timeout=600)
def gen_voice(segments: list, voice_id: str = "es-ES-ElviraNeural",
              rate: str = "+0%", video_id: str = "video-01") -> list:
    """TTS por segmento (ES). Devuelve rutas /assets/out/<id>/voice/seg_NN.mp3."""
    import edge_tts

    out_dir = f"/assets/out/{video_id}/voice"
    os.makedirs(out_dir, exist_ok=True)

    async def run_all():
        out = []
        for i, text in enumerate(segments):
            mp3 = f"{out_dir}/seg_{i:02d}.mp3"
            com = edge_tts.Communicate(text, voice_id, rate=rate)
            await com.save(mp3)
            out.append({"idx": i, "path": mp3,
                        "bytes": os.path.getsize(mp3)})
        return out

    res = asyncio.run(run_all())
    assets.commit()
    return res


@app.function(volumes={"/assets": assets}, timeout=300)
def smoke_voice(text: str, voice_id: str = "es-ES-ElviraNeural") -> dict:
    """Un TTS corto para oír la voz candidata (edge-tts, $0)."""
    import edge_tts

    out_dir = "/assets/out/smoke"
    os.makedirs(out_dir, exist_ok=True)
    path = f"{out_dir}/smoke_voice_{voice_id.split('-')[-1]}.mp3"

    async def run():
        com = edge_tts.Communicate(text, voice_id)
        await com.save(path)

    asyncio.run(run())
    assets.commit()
    return {"path": path, "bytes": os.path.getsize(path), "voice": voice_id}


@app.local_entrypoint()
def smoke_voice_only():
    """modal run app/voice_app.py::smoke_voice_only — valida Modal+edge-tts+Volume."""
    frase = ("Desarmé draw.io con IA gratis. Encontré treinta y cinco "
             "puertas traseras entre procesos.")
    for v in ("es-ES-ElviraNeural", "es-ES-AlvaroNeural"):
        print(smoke_voice.remote(frase, v))


@app.local_entrypoint()
def gen():
    """TTS del guion completo (lee scripts/video-01.json)."""
    import json
    spec_path = os.path.join(os.path.dirname(__file__), "..",
                             "scripts", "video-01.json")
    spec = json.load(open(spec_path))
    segs = [s["voice_es"] for s in spec["segments"]]
    v = spec.get("voice", {})
    print(gen_voice.remote(segs, v.get("voice_id", "es-ES-ElviraNeural"),
                           v.get("rate", "+0%"),
                           spec.get("id", "video-01")))
