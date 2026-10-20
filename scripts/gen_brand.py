#!/usr/bin/env python3
"""
scripts/gen_brand.py — genera el sistema de identidad visual de "Audit with Proof".

🛡️ Por qué NO se genera con IA (FLUX):
   · D-VM-04: **la IA nunca dibuja texto**. Una marca necesita tipografía exacta.
   · Un logo tiene que ser **determinista** (el mismo byte cada vez), **nítido a
     cualquier tamaño** (de 32 px a 2560 px) y **reutilizable** (avatar, banner,
     favicon, cabecera del README, tarjeta de YouTube).
   · Se dibuja con **PIL** a 4× y se reduce (supersampling) → bordes limpios.

🎨 Paleta de la marca (la misma del vídeo):
   marca    #8FE3CF  (el turquesa de las tarjetas ASS)
   fondo    #0A121C  (navy profundo)
   texto    #FFFFFF
   detalle  #5C7186  (gris azulado, para lo secundario)

🖼️ Los 3 conceptos (el operador elige mirando la galería):
   A · EL SELLO   → check + rejilla de puntos (lo desconocido, con 1 verificado)
   B · EL LENTE   → lupa sobre líneas de datos + check
   C · LAS BARRAS → el informe en barras; la última, turquesa, es el hallazgo

Salida (por concepto):
   logo-<c>-{1024,512,256,128,64,32}.png   símbolo con fondo transparente
   wordmark-<c>-light.png / -dark.png       el texto con el símbolo (fondo transparente)
   og-<c>-1200x630.png                      tarjeta social (fondo navy)
   banner-<c>-2560x1440.png                 banner de YouTube

Uso:  python3 scripts/gen_brand.py --out /sdcard/Download/brand [--conceptos A,B,C]
"""
import argparse
import io
import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ── paleta ───────────────────────────────────────────────────────────────────
MARCA = (0x8F, 0xE3, 0xCF)
FONDO = (0x0A, 0x12, 0x1C)
TEXTO = (0xFF, 0xFF, 0xFF)
DETALLE = (0x5C, 0x71, 0x86)
SS = 4  # supersampling

HERE = Path(__file__).resolve().parent
FUENTES = [
    HERE.parent / "assets" / "fonts" / "Poppins-Bold.ttf",
    HERE.parent / "assets" / "Poppins-Bold.ttf",
    Path("/tmp/opencode/kag/fonts/Poppins-Bold.ttf"),
]


def fuente() -> str:
    for f in FUENTES:
        if f.exists():
            return str(f)
    raise SystemExit("no encuentro Poppins-Bold.ttf (miralo en assets/fonts/)")


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(fuente(), size)


def rgba(c, a=255):
    return (c[0], c[1], c[2], a)


# ── primitivas ───────────────────────────────────────────────────────────────
def lienzo(size: int, fondo=None) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (size * SS, size * SS), fondo or (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def badge(d, S, margen=0.055, radio=0.235, borde=0.022):
    """Rectángulo redondeado: el 'sello' de la marca."""
    m = int(S * margen)
    lado = S - 2 * m
    d.rounded_rectangle(
        [m, m, m + lado, m + lado],
        radius=int(lado * radio),
        fill=rgba(FONDO),
        outline=rgba(MARCA),
        width=max(2, int(S * borde)),
    )
    return m, lado


def check(d, S, cx, cy, r, color=MARCA, w=None):
    """Checkmark con trazo grueso y extremos redondeados."""
    w = w or int(S * 0.062)
    pts = [
        (cx - r * 0.78, cy + r * 0.04),
        (cx - r * 0.26, cy + r * 0.56),
        (cx + r * 0.80, cy - r * 0.62),
    ]
    d.line(pts, fill=rgba(color), width=w, joint="curve")
    for p in (pts[0], pts[2]):
        d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=rgba(color))


def puntos(d, S, x0, y0, paso, r, cols=3, rows=3, encendidos=((1, 1),)):
    """Rejilla de puntos: lo desconocido; solo uno verificado."""
    for j in range(rows):
        for i in range(cols):
            cx = x0 + i * paso
            cy = y0 + j * paso
            on = (i, j) in encendidos
            d.ellipse(
                [cx - r, cy - r, cx + r, cy + r],
                fill=rgba(MARCA if on else DETALLE, 255 if on else 150),
            )


def envolver(d, texto, x, y, fs, color, ancho_max, interlinea=1.45):
    """Escribe un texto adjustinglo al ancho maximo. Devuelve la y final."""
    f = font(fs)
    palabras = texto.split()
    linea, yy = [], y
    for w in palabras:
        prueba = " ".join(linea + [w])
        if d.textlength(prueba, font=f) > ancho_max and linea:
            d.text((x, yy), " ".join(linea), font=f, fill=rgba(color))
            yy += fs * interlinea
            linea = [w]
        else:
            linea.append(w)
    if linea:
        d.text((x, yy), " ".join(linea), font=f, fill=rgba(color))
        yy += fs * interlinea
    return yy


# ── conceptos ────────────────────────────────────────────────────────────────
def simbolo(concepto: str, S: int) -> Image.Image:
    img, d = lienzo(S)
    if S <= 64:
        # MODO FAVICON: a 32 px el borde se come los pixeles y el navy se
        # pierde contra un fondo oscuro -> relleno turquesa + check navy, sin borde.
        m = int(S * 0.06)
        lado = S - 2 * m
        d.rounded_rectangle([m, m, m + lado, m + lado], radius=int(lado * 0.26),
                            fill=rgba(MARCA))
        if concepto == "A":
            check(d, S, S * 0.50, S * 0.52, S * 0.26, color=FONDO, w=int(S * 0.105))
        elif concepto == "B":
            cx, cy, r = S * 0.44, S * 0.42, S * 0.22
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=rgba(FONDO), width=int(S * 0.085))
            d.line([(cx + r * 0.70, cy + r * 0.70), (cx + r * 1.32, cy + r * 1.32)],
                   fill=rgba(FONDO), width=int(S * 0.090))
            check(d, S, S * 0.60, S * 0.755, S * 0.19, color=FONDO, w=int(S * 0.100))
        else:  # C
            x, y, w, gap = S * 0.20, S * 0.26, S * 0.60, S * 0.10
            for i, frac in enumerate((0.86, 0.66, 0.94)):
                d.rounded_rectangle([x, y + i * gap, x + w * frac, y + i * gap + S * 0.058],
                                    radius=int(S * 0.029), fill=rgba(FONDO, 150))
            d.rounded_rectangle([x, y + 3 * gap, x + w, y + 3 * gap + S * 0.058],
                                radius=int(S * 0.029), fill=rgba(FONDO))
            check(d, S, S * 0.755, S * 0.665, S * 0.16, color=FONDO, w=int(S * 0.095))
        return img.resize((S, S), Image.LANCZOS)

    m, lado = badge(d, S)

    if concepto == "A":
        # EL SELLO: check limpio + rejilla de lo desconocido (1 punto encendido)
        check(d, S, S * 0.435, S * 0.575, S * 0.30)
        puntos(d, S, S * 0.635, S * 0.205, S * 0.093, S * 0.027,
               encendidos=((1, 1),))

    elif concepto == "B":
        # EL LENTE: una lupa sobre tres lineas de datos + check
        cx, cy, r = S * 0.44, S * 0.42, S * 0.225
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=rgba(MARCA), width=int(S * 0.045))
        # mango
        d.line([(cx + r * 0.70, cy + r * 0.70), (cx + r * 1.30, cy + r * 1.30)],
               fill=rgba(MARCA), width=int(S * 0.050))
        # lineas de "informe" dentro de la lupa
        for i, largo in enumerate((0.95, 0.72, 0.50)):
            y = cy - r * 0.42 + i * r * 0.44
            d.line([(cx - r * 0.55, y), (cx - r * 0.55 + r * 1.05 * largo, y)],
                   fill=rgba(DETALLE, 210), width=int(S * 0.022))
        # el check va en el hueco de abajo-derecha, sin pisar el mango
        check(d, S, S * 0.60, S * 0.745, S * 0.185)

    elif concepto == "C":
        # LAS BARRAS: el informe; la ultima barra turquesa es el hallazgo
        x = S * 0.20
        y = S * 0.30
        w = S * 0.60
        gap = S * 0.085
        anchos = (0.86, 0.66, 0.94, 0.54)
        for i, frac in enumerate(anchos):
            d.rounded_rectangle(
                [x, y + i * gap, x + w * frac, y + i * gap + S * 0.048],
                radius=int(S * 0.024), fill=rgba(DETALLE, 190))
        # el hallazgo
        d.rounded_rectangle(
            [x, y + 4 * gap, x + w, y + 4 * gap + S * 0.048],
            radius=int(S * 0.024), fill=rgba(MARCA))
        check(d, S, S * 0.74, S * 0.735, S * 0.135)
    else:
        raise SystemExit("concepto desconocido: " + concepto)

    return img.resize((S, S), Image.LANCZOS)


def texto_marca(d, x, y, size, color, tracking=0.02):
    """Escribe texto con tracking manual (el look del vídeo)."""
    f = font(size)
    for ch in texto_marca.actual:
        d.text((x, y), ch, font=f, fill=rgba(color))
        x += d.textlength(ch, font=f) + size * tracking
    return x


def _wordmark(concepto: str, S: int, claro: bool) -> Image.Image:
    """El lockup: simbolo + AUDIT / WITH PROOF + la barra (la del vídeo)."""
    fg_texto = TEXTO if claro else (0x0A, 0x12, 0x1C)
    fg_marca = MARCA
    img = Image.new("RGBA", (S * SS, int(S * 0.42) * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    alto = int(S * 0.42)
    # simbolo
    sym = simbolo(concepto, int(alto * SS))
    img.alpha_composite(sym, (0, 0))
    # texto
    fs = int(alto * 0.30)
    f = font(fs)
    x = alto * SS + int(S * 0.05) * SS
    y = int(alto * 0.24) * SS
    texto_marca.actual = "AUDIT"
    x = texto_marca(d, x, y, fs, fg_texto)
    texto_marca.actual = " WITH PROOF"
    texto_marca(d, x, y, fs, fg_marca)
    # la barra: justo bajo el texto, como en la tarjeta del vídeo
    by = int(alto * 0.520) * SS
    _x0 = alto * SS + int(S * 0.05) * SS
    d.rounded_rectangle(
        [_x0, by, _x0 + int(S * 0.20) * SS, by + int(S * 0.016) * SS],
        radius=int(S * 0.008) * SS, fill=rgba(fg_marca))
    img = img.resize((S, int(S * 0.42)), Image.LANCZOS)
    # recorta al contenido real (sin aire muerto)
    bbox = img.getbbox()
    return img.crop(bbox) if bbox else img


def _og(concepto: str) -> Image.Image:
    W, H = 1200, 630
    img = Image.new("RGBA", (W, H), rgba(FONDO))
    d = ImageDraw.Draw(img)
    for j in range(14):
        for i in range(24):
            d.ellipse([40 + i * 48, 40 + j * 42, 46 + i * 48, 46 + j * 42],
                       fill=rgba(DETALLE, 55))
    sym = simbolo(concepto, 300)
    img.alpha_composite(sym, (90, 165))

    x = 450
    texto_marca.actual = "AUDIT"
    texto_marca(d, x, 150, 78, TEXTO, 0.03)
    texto_marca.actual = "WITH PROOF"
    texto_marca(d, x, 240, 78, MARCA, 0.03)
    d.rounded_rectangle([x, 340, x + 250, 348], radius=4, fill=rgba(MARCA))
    envolver(d, "Informes de auditoria con evidencia verificable y limites declarados.",
             x, 385, 25, DETALLE, 660)
    return img.convert("RGB")


def _banner(concepto: str) -> Image.Image:
    W, H = 2560, 1440
    img = Image.new("RGBA", (W, H), rgba(FONDO))
    d = ImageDraw.Draw(img)
    for j in range(20):
        for i in range(40):
            d.ellipse([70 + i * 62, 60 + j * 66, 78 + i * 62, 68 + j * 66],
                       fill=rgba(DETALLE, 50))
    sym = simbolo(concepto, 520)
    img.alpha_composite(sym, (280, 460))

    x = 920
    texto_marca.actual = "AUDIT"
    texto_marca(d, x, 545, 150, TEXTO, 0.03)
    texto_marca.actual = "WITH PROOF"
    texto_marca(d, x, 715, 150, MARCA, 0.03)
    d.rounded_rectangle([x, 895, x + 480, 911], radius=8, fill=rgba(MARCA))
    envolver(d, "Evidencia verificable. Limites declarados. Auditoria de apps Electron/JS.",
             x, 960, 44, DETALLE, 1180)
    return img.convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/sdcard/Download/brand")
    ap.add_argument("--conceptos", default="A,B,C")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    for c in a.conceptos.split(","):
        c = c.strip().upper()
        for S in (1024, 512, 256, 128, 64, 32):
            p = out / f"logo-{c}-{S}.png"
            simbolo(c, S).save(p)
            print("·", p.name, p.stat().st_size, "B")
        p = out / f"wordmark-{c}-light.png"
        _wordmark(c, 1200, claro=True).save(p)
        print("·", p.name, p.stat().st_size, "B")
        p = out / f"wordmark-{c}-dark.png"
        _wordmark(c, 1200, claro=False).save(p)
        print("·", p.name, p.stat().st_size, "B")
        p = out / f"og-{c}-1200x630.png"
        _og(c).save(p, quality=95)
        print("·", p.name, p.stat().st_size, "B")
        p = out / f"banner-{c}-2560x1440.png"
        _banner(c).save(p, quality=95)
        print("·", p.name, p.stat().st_size, "B")
    print("\n✅ Identidad generada en", out)


if __name__ == "__main__":
    main()
