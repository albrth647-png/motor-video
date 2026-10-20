#!/usr/bin/env python3
"""
scripts/gen_images.py — genera las imágenes nuevas con Cloudflare Workers AI (FLUX).

🛡️ Por qué corre AQUÍ (en CI) y no en el móvil:
   · AGENTS.md §4: "todo a la nube, cero teléfono". Generar 7 imágenes desde el
     móvil serían ~20 MB de datos (bajada + subida del dataset).
   · En el runner: **0 MB en el móvil**.

🔒 Fuente única: `scripts/video-01.json` → `images.prompts` (número de shot → prompt).
   · D-VM-04: **ningún texto en el encuadre** (la IA nunca dibuja texto). Los
     prompts lo dicen explícitamente ("no text, no letters").
   · La salida es JPEG porque el kernel hace `cv2.imread('shotNN.jpg')`.

Variables de entorno (Secrets del repo):
   CLOUDFLARE_ACCOUNT_ID · CLOUDFLARE_API_TOKEN

Uso:  python3 scripts/gen_images.py --spec scripts/video-01.json --out /tmp/media
"""
import argparse
import io
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

MODEL = "@cf/black-forest-labs/flux-1-schnell"
API = "https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{model}"


def generate(account: str, token: str, prompt: str, dst: Path, tries: int = 3) -> None:
    url = API.format(account=account, model=MODEL)
    # El endpoint de FLUX solo necesita `prompt` (AGENTS.md §7).
    body = json.dumps({"prompt": prompt}).encode("utf-8")
    last = ""
    for attempt in range(1, tries + 1):
        try:
            req = urllib.request.Request(
                url,
                data=body,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=240) as r:
                data = r.read()
            if len(data) < 1024:
                raise RuntimeError(f"respuesta demasiado corta ({len(data)} bytes)")
            # PNG -> JPEG (el kernel lee .jpg)
            from PIL import Image

            img = Image.open(io.BytesIO(data)).convert("RGB")
            img.save(dst, "JPEG", quality=92)
            print(f"  ✓ {dst.name} {img.size} {dst.stat().st_size} bytes")
            return
        except Exception as e:  # noqa: BLE001
            last = str(e)[:200]
            print(f"  · intento {attempt}/{tries} fallido: {last}")
            time.sleep(4 * attempt)
    raise SystemExit(f"❌ no se pudo generar {dst.name}: {last}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default="scripts/video-01.json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default="", help="solo estos shots (ej. 21,22)")
    a = ap.parse_args()

    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    if not account or not token:
        raise SystemExit("❌ faltan CLOUDFLARE_ACCOUNT_ID / CLOUDFLARE_API_TOKEN")

    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    prompts = spec["images"]["prompts"]
    wanted = {s.strip() for s in a.only.split(",") if s.strip()}
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    todo = {k: v for k, v in prompts.items() if not wanted or k in wanted}
    print(f"· imágenes a generar: {len(todo)} ({', '.join(sorted(todo, key=int))})")
    for num, prompt in sorted(todo.items(), key=lambda kv: int(kv[0])):
        dst = out / f"shot{int(num):02d}.jpg"
        if dst.exists() and dst.stat().st_size > 1024:
            print(f"  · {dst.name} ya existe → se reutiliza")
            continue
        generate(account, token, prompt, dst)
    print("· generación de imágenes OK")


if __name__ == "__main__":
    main()
