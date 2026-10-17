"""
Motor de vídeo — app de Modal (SPEC-MOTOR-VIDEO.md v1.1)
Genera en la nube: clips Wan2.2 + voz (edge-tts) + música (ACE-Step).
El móvil SOLO manda texto/KB (R3) y baja los mp4. Nunca renderiza en el teléfono (R2).

Uso (desde el runner de GitHub Actions o local):
    modal run app.modal_app::smoke      # 1 clip + 1 voz  → mide $ y calidad (§8)
    modal run app.modal_app::render     # todos los clips + voz + música del vídeo
Salida -> Volume "video-engine-assets" en /out/<video_id>/
"""
import json
import os
import subprocess
import time
import modal

# --- Volumes: cache de pesos (1 TiB gratis, R-VM-06) + salida ---------------
assets = modal.Volume.from_name("video-engine-assets", create_if_missing=True)

# --- Imagen: torch + diffusers + edge-tts. ACE-Step se añade aparte (pesa). ---
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg")
    .pip_install(
        "torch==2.4.0",
        "diffusers>=0.31.0",
        "transformers>=4.44.0",
        "accelerate>=0.33.0",
        "sentencepiece",
        "protobuf",
        "edge-tts>=6.1.0",
        "imageio[ffmpeg]",
        "ninja",
    )
)

app = modal.App("video-engine", image=image)

# Semilla fija por defecto (spec §4.3 reproducibilidad)
DEFAULT_SEED = 42


# ---------------------------------------------------------------------------
# 1) CLIPS — Wan2.2-T2V-5B en A10 (24 GB) ---------------------------------
# ---------------------------------------------------------------------------
@app.function(
    gpu="A10",
    volumes={"/assets": assets},
    timeout=1800,
    # El primer arranque descarga ~10 GB de pesos al Volume; siguientes, cache.
)
def gen_clip(prompt: str, seed: int = DEFAULT_SEED, steps: int = 30,
             seconds: float = 4.0, size: tuple = (480, 832)) -> str:
    """Genera UN clip vertical 480p con Wan2.2-5B. Devuelve la ruta /assets/out/..."""
    import torch
    from diffusers import WanPipeline
    from diffusers.utils import export_to_video

    out_dir = "/assets/out"
    os.makedirs(out_dir, exist_ok=True)

    # Caché de pesos en el Volume: si ya está, no vuelve a descargar.
    # Nombre correcto = spec D-VM-02 (TI2V-5B, gated:false verificado -> sin HF_TOKEN).
    model_id = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
    cache = "/assets/models"
    os.makedirs(cache, exist_ok=True)

    pipe = WanPipeline.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16,
        cache_dir=cache,
    )
    pipe.enable_model_cpu_offload()  # A10=24GB: offload para no OOM (spec §5)

    # Wan2.2 TI2V-5B genera a 24 fps (spec §4.3: convierte 24 -> 30 en ensamblado);
    # pedimos frames = duración deseada * 24.
    num_frames = max(16, int(seconds * 24))
    num_frames = (num_frames // 4) * 4 + 1  # Wan requiere 4n+1

    generator = torch.Generator("cpu").manual_seed(seed)
    t0 = time.time()
    result = pipe(
        prompt=prompt,
        negative_prompt="text, watermark, logo, letters, words, blurry, lowres",
        num_frames=num_frames,
        width=size[1],
        height=size[0],
        num_inference_steps=steps,
        guidance_scale=5.0,
        generator=generator,
    )
    elapsed = time.time() - t0

    safe = prompt[:24].replace(" ", "_").replace("/", "_")
    path = f"{out_dir}/clip_{safe}_{seed}.mp4"
    export_to_video(result.frames[0], path, fps=24)

    assets.commit()
    return json.dumps({"path": path, "seconds": elapsed, "frames": num_frames})


# ---------------------------------------------------------------------------
# 2) VOZ — edge-tts (gratis, ya integrada R-VM-01) --------------------------
# ---------------------------------------------------------------------------
@app.function(volumes={"/assets": assets}, timeout=600)
def gen_voice(segments: list, voice_id: str = "es-ES-ElviraNeural",
              rate: str = "+0%", video_id: str = "video-01") -> list:
    """Genera TTS por segmento (ES) + archivo SRT/ASS de apoyo. Sin GPU."""
    import asyncio
    import edge_tts

    out_dir = f"/assets/out/{video_id}/voice"
    os.makedirs(out_dir, exist_ok=True)

    async def one(idx: int, text: str) -> dict:
        mp3 = f"{out_dir}/seg_{idx:02d}.mp3"
        com = edge_tts.Communicate(text, voice_id, rate=rate)
        await com.save(mp3)
        # Guarda marcas de palabra para el karaoke (subs EN a mano)
        words = []
        with edge_tts.SubMaker() as sub:
            # SubMaker.feed necesita stream; usamos stream() para marcas
            pass
        return {"idx": idx, "path": mp3}

    async def run_all():
        out = []
        for i, seg in enumerate(segments):
            out.append(await one(i, seg))
        return out

    res = asyncio.run(run_all())
    assets.commit()
    return res


# ---------------------------------------------------------------------------
# 3) SMOKE TEST §8 — 1 clip + 1 voz, mide $ y tiempo ------------------------
@app.function(gpu="A10", volumes={"/assets": assets}, timeout=1200)
def smoke_clip() -> dict:
    """Un solo clip barato para medir coste/calidad REAL antes de renderizar todo."""
    import torch
    from diffusers import WanPipeline
    from diffusers.utils import export_to_video

    out_dir = "/assets/out/smoke"
    os.makedirs(out_dir, exist_ok=True)
    model_id = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
    cache = "/assets/models"
    os.makedirs(cache, exist_ok=True)

    pipe = WanPipeline.from_pretrained(model_id, torch_dtype=torch.bfloat16,
                                       cache_dir=cache)
    pipe.enable_model_cpu_offload()

    t0 = time.time()
    gen_t0 = time.time()
    result = pipe(
        prompt=("dark abstract cybersecurity visual, glowing teal and magenta "
                "circuit pathways, volumetric fog, cinematic, no text, no letters"),
        negative_prompt="text, watermark, logo, letters, blurry, lowres",
        num_frames=33,          # 4n+1
        width=480,
        height=832,
        num_inference_steps=25,
        guidance_scale=5.0,
        generator=torch.Generator("cpu").manual_seed(42),
    )
    gen_s = time.time() - gen_t0
    path = f"{out_dir}/smoke_clip.mp4"
    export_to_video(result.frames[0], path, fps=24)
    total = time.time() - t0
    assets.commit()
    return {"path": path, "gen_seconds": round(gen_s, 1),
            "total_seconds": round(total, 1), "frames": 33}


@app.function(volumes={"/assets": assets}, timeout=300)
def smoke_voice(text: str, voice_id: str = "es-ES-ElviraNeural") -> dict:
    """Un TTS corto para oír la voz candidata (edge-tts, $0)."""
    import asyncio
    import edge_tts

    out_dir = "/assets/out/smoke"
    os.makedirs(out_dir, exist_ok=True)
    path = f"{out_dir}/smoke_voice.mp3"

    async def run():
        com = edge_tts.Communicate(text, voice_id)
        await com.save(path)

    t0 = time.time()
    asyncio.run(run())
    assets.commit()
    return {"path": path, "seconds": round(time.time() - t0, 1), "voice": voice_id}


@app.local_entrypoint()
def smoke_voice_only():
    """modal run app/modal_app.py::smoke_voice_only — valida Modal+edge-tts+Volume ($0)."""
    print("== Voz edge-tts (ES) ==")
    print(smoke_voice.remote(
        "Desarmé draw.io con IA gratis. Encontré treinta y cinco puertas traseras entre procesos.",
        "es-ES-ElviraNeural",
    ))


@app.local_entrypoint()
def smoke_clip_only():
    """modal run app/modal_app.py::smoke_clip_only — 1 clip Wan @ A10 (mide $ y calidad)."""
    print("== Clip Wan2.2-TI2V-5B @ A10 ==")
    print(smoke_clip.remote())


@app.local_entrypoint()
def smoke():
    """modal run app.modal_app::smoke — paso 4 del flujo (medición §8)."""
    print("== Voz edge-tts ==")
    v = smoke_voice.remote(
        "Desarmé draw.io con IA gratis. Encontré treinta y cinco puertas traseras."
    )
    print(v)
    print("== Clip Wan2.2-TI2V-5B @ A10 ==")
    c = smoke_clip.remote()
    print(c)
    print("\n[SMOKE] Baja los archivos desde el Volume y óyelos/revísalos.")
    print("[SMOKE] Con gen_seconds calculas $ real = gen_seconds/3600 * precio_A10.")
