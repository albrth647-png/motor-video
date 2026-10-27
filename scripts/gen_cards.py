#!/usr/bin/env python3
"""
scripts/gen_cards.py — tarjetas de evidencia 1080x1920 para un short (modo `cards`).

🛡️ Por qué existe: la IA **nunca dibuja texto** (D-VM-04). Toda tarjeta se dibuja con
   PIL + Poppins Bold a 2x y se reduce → nítida y **reproducible byte a byte**.
   Mismo sistema que `gen_brand.py` (misma paleta, misma fuente) → el vídeo y la marca
   son una sola cosa.

Uso:
    python3 scripts/gen_cards.py --spec scripts/video-s01.json --out ../../socialcore/assets/video-s01

Salida: shotNN.jpg 1080x1920 (JPEG q92) en `--out`. El motor los consume desde el dataset
`motor-media` (la copia al runner la hace el workflow).

Sistema de composición (el mismo en las 9 tarjetas → el vídeo se lee como una sola pieza):
    y    0– 230  barra de marca (logo + wordmark + regla turquesa)
    y  286– 320  eyebrow (mono, tracking)
    y  344– 600  titular (88 px)
    y  620–1220  contenido
    y 1236–1284  pie de tarjeta (hairline + mono 26)  ← aire hasta el karaoke
    y 1380–1470  ZONA LIBRE: aquí caen los subtítulos EN (margin_v 450)
"""

import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

# --- paleta (identidad/BRAND.md — concepto C "las barras") -----------------------------
NAVY = "#0A121C"
PANEL = "#111C28"
LINE = "#1D2B3A"
TURQ = "#8FE3CF"
WHITE = "#FFFFFF"
DETAIL = "#5C7186"
SOFT = "#C9D6E2"
ORANGE = "#FF7A3A"

W, H = 1080, 1920
SS = 2                     # superescala: se dibuja a 2x y se reduce (nítido)
BODY_BOTTOM = 1220         # el contenido NO baja de aquí

_HERE = Path(__file__).resolve().parent
_FONTS = [
    _HERE.parent / "assets" / "fonts" / "Poppins-Bold.ttf",
    _HERE.parent / "assets" / "Poppins-Bold.ttf",
    Path("/tmp/opencode/kag/fonts/Poppins-Bold.ttf"),
]
_MONO = [
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"),
    Path("/usr/share/fonts/dejavu/DejaVuSansMono-Bold.ttf"),
]
_LOGO = [
    _HERE.parent.parent.parent / "identidad" / "assets" / "logo-C-512.png",
    _HERE.parent / "assets" / "logo-C-512.png",
]


def _first(paths):
    for p in paths:
        if p.exists():
            return p
    return None


_F = _first(_FONTS)
_M = _first(_MONO)
if _F is None:
    raise SystemExit("no encuentro Poppins-Bold.ttf")
if _M is None:
    raise SystemExit("no encuentro DejaVuSansMono-Bold.ttf")

_CACHE = {}


def font(size: int) -> ImageFont.FreeTypeFont:
    k = int(size * SS)
    if k not in _CACHE:
        _CACHE[k] = ImageFont.truetype(str(_F), k)
    return _CACHE[k]


def mono(size: int) -> ImageFont.FreeTypeFont:
    k = ("m", int(size * SS))
    if k not in _CACHE:
        _CACHE[k] = ImageFont.truetype(str(_M), int(size * SS))
    return _CACHE[k]


# --- fondo de marca (una sola vez, cacheado) --------------------------------------------
_BG = {}


def background(tone: float = 1.0) -> Image.Image:
    """Degradado + focos suaves + rejilla de puntos: el fondo de TODAS las tarjetas.
    tone < 1 = más oscuro (tarjetas de contenido), 1 = el del CTA."""
    if tone in _BG:
        return _BG[tone].copy()
    grad = Image.new("RGB", (1, H * SS))
    gp = grad.load()
    for y in range(H * SS):
        t = y / float(H * SS)
        gp[0, y] = (int(10 + 3 * t * tone), int(18 + 8 * t * tone), int(28 + 12 * t * tone))
    im = grad.resize((W * SS, H * SS))
    glow = Image.new("RGB", (W * SS, H * SS), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    focos = [(0.16, 0.08, 560, (14, 34, 50)), (0.90, 0.22, 470, (12, 30, 46)),
             (0.62, 0.62, 700, (10, 26, 38)), (0.10, 0.86, 520, (13, 32, 46)),
             (0.55, 0.98, 620, (18, 48, 64))]
    for cx, cy, r, col in focos:
        col = tuple(int(c * tone) for c in col)
        gd.ellipse([(cx * W - r) * SS, (cy * H - r) * SS,
                    (cx * W + r) * SS, (cy * H + r) * SS], fill=col)
    glow = glow.filter(ImageFilter.GaussianBlur(170))
    im = ImageChops.screen(im, glow)
    d = ImageDraw.Draw(im)
    for y in range(120, H - 110, 52):
        for x in range(56, W - 36, 52):
            d.ellipse([x * SS, y * SS, (x + 3) * SS, (y + 3) * SS], fill="#16242F")
    _BG[tone] = im
    return im.copy()


def canvas(tone: float = 0.78) -> tuple:
    im = background(tone)
    return im, ImageDraw.Draw(im)


def rr(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle([box[0] * SS, box[1] * SS, box[2] * SS, box[3] * SS],
                        radius=r * SS, fill=fill, outline=outline, width=width * SS)


def txt(d, xy, s, f, fill=WHITE, anchor="la"):
    d.text((xy[0] * SS, xy[1] * SS), s, font=f, fill=fill, anchor=anchor)


def track(d, xy, s, f, fill=DETAIL, tr=2.6):
    """Texto con tracking (eyebrows y pies): letra a letra, aire medido."""
    x, y = xy
    for ch in s:
        txt(d, (x, y), ch, f, fill)
        x += d.textlength(ch, font=f) / SS + tr
    return x


def wrap(d, s, f, max_w):
    """Ajuste de línea por medida real (no por caracteres)."""
    out, linea = [], ""
    for w in s.split():
        prueba = (linea + " " + w).strip()
        if d.textlength(prueba, font=f) > max_w * SS and linea:
            out.append(linea)
            linea = w
        else:
            linea = prueba
    if linea:
        out.append(linea)
    return out


def block(d, x, y, s, size, color=WHITE, max_w=W - 140, lh=1.32, f=None):
    f = f or font(size)
    for para in s.split("\n"):
        for line in wrap(d, para, f, max_w):
            txt(d, (x, y), line, f, color)
            y += size * lh
    return y


def brandbar(im, d):
    """logo + wordmark, medido (el wordmark NO se pisa con el logo)."""
    lg = _first(_LOGO)
    if lg:
        s = Image.open(lg).convert("RGBA")
        s = s.resize((96 * SS, 96 * SS), Image.LANCZOS)
        im.paste(s, (70 * SS, 96 * SS), s)
    x = 70 + 96 + 30
    txt(d, (x, 118), "AUDIT", font(42), WHITE)
    x += d.textlength("AUDIT", font=font(42)) / SS + 14
    txt(d, (x, 118), "WITH PROOF", font(42), TURQ)
    d.rectangle([70 * SS, 226 * SS, 330 * SS, 232 * SS], fill=TURQ)


def header(im, d, eyebrow, title=None, color=TURQ):
    brandbar(im, d)
    if eyebrow:
        track(d, (70, 288), eyebrow.upper(), mono(30), color, tr=3.2)
    if title:
        return block(d, 70, 344, title, 88, WHITE, max_w=W - 140, lh=1.12)
    return 344


def foot(d, left, right=None):
    """Pie de tarjeta: hairline + mono. Cierra la composición y deja aire al karaoke."""
    d.rectangle([70 * SS, 1236 * SS, (W - 70) * SS, 1238 * SS], fill="#20303F")
    track(d, (70, 1254), left.upper(), mono(25), "#48606F", tr=2.0)
    if right:
        f, tr = mono(25), 2.0
        wpx = sum(d.textlength(c, font=f) / SS + tr for c in right.upper()) - tr
        track(d, (W - 70 - wpx, 1254), right.upper(), f, "#48606F", tr=tr)


def pill(d, cx, y, s, color=TURQ, fs=34, padx=44, h=86, fill="#0F2A2A"):
    """placa redondeada con el texto centrado (la medida se hace con la fuente real)."""
    f, tr = font(fs), 1.2
    wpx = sum(d.textlength(c, font=f) / SS + tr for c in s) - tr
    tw = wpx + padx * 2
    rr(d, (cx - tw / 2, y, cx + tw / 2, y + h), h / 2, fill=fill, outline=color, width=2)
    txt(d, (cx - wpx / 2, y + (h - fs * 1.38) / 2 + 2), s, f, color)
    return tw


def finish(im, name, outdir):
    im = im.resize((W, H), Image.LANCZOS)
    p = Path(outdir) / name
    im.save(p, "JPEG", quality=92, optimize=True, subsampling=0)
    print("·", p.name, im.size)


# --- tarjetas --------------------------------------------------------------------------

def c49_cover(outdir):
    """fondo del INTRO (sin texto: el ASS dibuja el gancho encima)."""
    im, d = canvas(0.85)
    brandbar(im, d)
    d.rectangle([(W - 300) // 2 * SS, 1104 * SS, (W + 300) // 2 * SS, 1106 * SS], fill=TURQ)
    f = mono(27)
    s = "CASO 2 · EVIDENCIA VERIFICABLE · 26-OCT-2026"
    wpx = sum(d.textlength(c, font=f) / SS + 3.0 for c in s) - 3.0
    track(d, ((W - wpx) / 2, 1148), s, f, "#6C8398", tr=3.0)
    finish(im, "shot49.jpg", outdir)


def c50_gancho(outdir):
    """lo que hay detrás del hecho (el gancho ya lo dice el intro: sandbox: false)"""
    im, d = canvas(0.72)
    header(im, d, "por qué importa", "Lo que\nhay detrás", color=ORANGE)
    block(d, 70, 620, "credenciales de producción", 62, TURQ, max_w=W - 150, lh=1.18)
    d.rectangle([70 * SS, 790 * SS, 470 * SS, 797 * SS], fill=ORANGE)
    block(d, 70, 848,
          "Si el renderer se compromete, lo que hay detrás no es una cuenta de red social: "
          "son las bases de datos de la empresa.",
          44, SOFT, max_w=W - 150, lh=1.36)
    txt(d, (70, 1064), "PostgreSQL · MySQL · SQLite · SQL Server · MongoDB · Redis",
        mono(24), "#48606F")
    d.rectangle([70 * SS, 1032 * SS, 470 * SS, 1034 * SS], fill=LINE)
    foot(d, "1.603 paquetes · 130 directas", "v6.1.6")
    finish(im, "shot50.jpg", outdir)


def c51_fuente(outdir):
    """el fragmento real, con la línea 57 resaltada"""
    im, d = canvas(0.72)
    header(im, d, "fuente · tag v6.1.6", "Está en la\nlínea 57")
    rr(d, (60, 626, W - 60, 1094), 26, fill=PANEL, outline=LINE, width=2)
    txt(d, (94, 662), "apps/studio/src/background/WindowBuilder.ts", mono(25), TURQ)
    d.rectangle([94 * SS, 706 * SS, (W - 94) * SS, 708 * SS], fill=LINE)
    lineas = [
        ("53", "  preload: preloadPath,", False),
        ("54", "  nodeIntegration: false,", False),
        ("55", "  contextIsolation: true,", False),
        ("56", "  spellcheck: false,", False),
        ("57", "  sandbox: false,", True),
    ]
    y = 730
    for n, s, hot in lineas:
        if hot:
            rr(d, (80, y - 10, W - 80, y + 58), 12, fill="#16283A")
            d.rectangle([80 * SS, (y - 10) * SS, 87 * SS, (y + 58) * SS], fill=TURQ)
        txt(d, (108, y), n, mono(27), TURQ if hot else "#3F5566")
        txt(d, (186, y), s, mono(27), WHITE if hot else SOFT)
        y += 68
    block(d, 70, 1112,
          "webPreferences de la ventana principal: la línea existe en el tag público.",
          33, DETAIL, max_w=W - 150, lh=1.3)
    foot(d, "windowbuilder.ts", "sin parchear")
    finish(im, "shot51.jpg", outdir)


def c52_tres_fuentes(outdir):
    """tres fuentes independientes, el mismo resultado"""
    im, d = canvas(0.72)
    header(im, d, "verificación", "Tres fuentes,\nel mismo resultado")
    filas = [
        ("FUENTE", "WindowBuilder.ts:57", "sandbox: false"),
        ("ARTEFACTO", "dist/main.js · AST", "literal false"),
        ("BYTES", "bundle del .deb", "sandbox: false"),
    ]
    y = 620
    for tag, src, val in filas:
        rr(d, (60, y, W - 60, y + 140), 20, fill=PANEL, outline=LINE, width=2)
        track(d, (92, y + 24), tag, mono(25), TURQ, tr=3.0)
        txt(d, (92, y + 72), src, mono(28), SOFT)
        txt(d, (W - 92, y + 84), val, mono(29), WHITE, anchor="ra")
        y += 154
    rr(d, (60, y + 10, W - 60, y + 116), 20, fill="#0F2A2A", outline=TURQ, width=2)
    txt(d, (92, y + 44), "las tres coinciden", font(40), TURQ)
    foot(d, "regla: ningún dato con una sola fuente", "3/3")
    finish(im, "shot52.jpg", outdir)


def c53_procedencia(outdir):
    """el binario es el que ellos publicaron"""
    im, d = canvas(0.72)
    header(im, d, "procedencia", "El binario\nes el suyo")
    rr(d, (60, 620, W - 60, 1108), 24, fill=PANEL, outline=LINE, width=2)
    txt(d, (92, 652), "beekeeper-studio_6.1.6_amd64.deb", mono(26), WHITE)
    txt(d, (92, 694), "281.298.876 B · release oficial", font(28), DETAIL)
    d.rectangle([92 * SS, 748 * SS, (W - 92) * SS, 750 * SS], fill=LINE)
    txt(d, (92, 774), "sha256 medido en CI", mono(25), DETAIL)
    txt(d, (92, 808), "750e2923…1302b3c", mono(31), WHITE)
    txt(d, (92, 868), "sha256 del release", mono(25), DETAIL)
    txt(d, (92, 902), "750e2923…1302b3c", mono(31), TURQ)
    pill(d, W / 2, 976, "idénticos", TURQ, fs=32, h=76)
    block(d, 70, 1128,
          "Sin coincidencia de hash no hay análisis: el artefacto es el que reparte el fabricante.",
          31, DETAIL, max_w=W - 150, lh=1.32)
    foot(d, "sha256 en los dos lados")
    finish(im, "shot53.jpg", outdir)


def c54_no_vuln(outdir):
    """lo que NO es"""
    im, d = canvas(0.72)
    header(im, d, "lectura correcta", "No es una\nvulnerabilidad")
    block(d, 70, 664,
          "Es una decisión de arquitectura, escrita a propósito en el fuente y "
          "confirmada en los bytes del binario.",
          46, SOFT, max_w=W - 150, lh=1.36)
    rr(d, (60, 880, W - 60, 1140), 22, fill=PANEL, outline=LINE, width=2)
    txt(d, (92, 918), "contextIsolation", mono(31), DETAIL)
    txt(d, (W - 92, 914), "true", font(38), TURQ, anchor="ra")
    d.rectangle([92 * SS, 990 * SS, (W - 92) * SS, 991 * SS], fill=LINE)
    txt(d, (92, 1018), "nodeIntegration", mono(31), DETAIL)
    txt(d, (W - 92, 1014), "false", font(38), TURQ, anchor="ra")
    block(d, 70, 1178, "El renderer no obtiene Node por su cuenta.", 32, DETAIL, max_w=W - 150)
    foot(d, "sin vulnerabilidad explotada")
    finish(im, "shot54.jpg", outdir)


def c56_que_significa(outdir):
    """diagrama: dónde queda el renderer con sandbox: false"""
    im, d = canvas(0.72)
    header(im, d, "qué significa", "El renderer queda\nfuera del sandbox")
    d.rounded_rectangle([60 * SS, 676 * SS, (W - 60) * SS, 1152 * SS], radius=26 * SS,
                        outline="#2A3D4E", width=2 * SS)
    track(d, (92, 702), "sandbox del sistema operativo", mono(25), DETAIL, tr=2.4)
    rr(d, (128, 762, W - 128, 1024), 22, fill=PANEL, outline=TURQ, width=3)
    txt(d, (W // 2, 820), "renderer", font(52), WHITE, anchor="ma")
    txt(d, (W // 2, 892), "ventana de la app · web", font(32), DETAIL, anchor="ma")
    txt(d, (W // 2, 944), "no aislado", font(32), ORANGE, anchor="ma")
    pill(d, W / 2, 1048, "sandbox: false", ORANGE, fs=30, h=72, fill="#241A12")
    block(d, 70, 1178, "No lo convierte por sí solo en ejecución de código.", 31, DETAIL,
          max_w=W - 150)
    foot(d, "aislamiento del so ≠ aislamiento del renderer")
    finish(im, "shot56.jpg", outdir)


def c57_limite(outdir):
    """lo que NO se pudo ver"""
    im, d = canvas(0.72)
    header(im, d, "límite declarado", "Análisis\nestático", color=ORANGE)
    block(d, 70, 664,
          "La app no se ejecutó. Nada de lo que sigue se midió: está declarado, no supuesto.",
          44, SOFT, max_w=W - 150, lh=1.36)
    items = ["no se ejecutó la app", "sin escaneo de CVEs", "sin escaneo de secretos"]
    y = 880
    for it in items:
        d.ellipse([70 * SS, (y + 12) * SS, (82 * SS), (y + 24) * SS], fill=ORANGE)
        txt(d, (108, y), it, mono(31), WHITE)
        y += 66
    rr(d, (60, y + 20, W - 60, y + 118), 18, fill="#241A12", outline=ORANGE, width=2)
    txt(d, (92, y + 48), "todo eso vive en §6 de la ficha", font(38), ORANGE)
    foot(d, "lo no medido, declarado")
    finish(im, "shot57.jpg", outdir)


def c58_ficha(outdir):
    """evidencia verificable + réplica"""
    im, d = canvas(0.72)
    header(im, d, "evidencia", "Cada dato\nse puede recomputar")
    rr(d, (60, 664, W - 60, 1128), 22, fill=PANEL, outline=LINE, width=2)
    txt(d, (92, 700), "evidence_id", mono(27), DETAIL)
    txt(d, (92, 740), "ev_dc211c4b…a168a2cc2", mono(32), TURQ)
    d.rectangle([92 * SS, 806 * SS, (W - 92) * SS, 807 * SS], fill=LINE)
    txt(d, (92, 834), "run de CI", mono(27), DETAIL)
    txt(d, (92, 874), "40365009151 · albrth647-png/Ghidra", mono(27), SOFT)
    d.rectangle([92 * SS, 938 * SS, (W - 92) * SS, 939 * SS], fill=LINE)
    txt(d, (92, 966), "ficha fechada", mono(27), DETAIL)
    txt(d, (92, 1006), "2026-10-26 · con §6 de límites", mono(29), WHITE)
    block(d, 70, 1150,
          "Derecho de réplica ofrecido al equipo: si corrigen, publicamos su respuesta.",
          31, DETAIL, max_w=W - 150, lh=1.3)
    foot(d, "audit with proof", "verificable")
    finish(im, "shot58.jpg", outdir)


def c55_endcard(outdir):
    """fondo del CTA (el ASS dibuja el texto y la placa LINK EN EL PERFIL)"""
    im, d = canvas(1.0)
    d.rectangle([92 * SS, 1436 * SS, (W - 92) * SS, 1438 * SS], fill="#1C3542")
    finish(im, "shot55.jpg", outdir)


CARDS = {
    49: c49_cover, 50: c50_gancho, 51: c51_fuente, 52: c52_tres_fuentes,
    53: c53_procedencia, 54: c54_no_vuln, 55: c55_endcard, 56: c56_que_significa,
    57: c57_limite, 58: c58_ficha,
}


# --- modo REVEAL: un PNG transparente por elemento ------------------------------------
# La pantalla NO cambia: shot00.jpg es el fondo fijo (rejilla + marca) de todo el vídeo y
# cada el_<id>.png se superpone con fade cuando la voz dice su palabra (scripts/reveal.py).

def _rgba(c, a=255):
    """'0xRRGGBB' (spec) o '#RRGGBB' (paleta) -> tupla RGBA."""
    if isinstance(c, tuple):
        return c
    h = str(c).strip()
    h = h[2:] if h.lower().startswith("0x") else h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def icon(d, kind, x, y, s, col, a=255):
    """Iconos geométricos (sin IA, D-VM-04): se dibujan con primitivas a 2x."""
    c = _rgba(col, a)
    S = SS
    def rec(x0, y0, x1, y1, fill=None, outline=None, w=0, r=0):
        if r:
            d.rounded_rectangle([x0*S, y0*S, x1*S, y1*S], radius=r*S, fill=fill,
                                outline=outline, width=int(w*S))
        else:
            d.rectangle([x0*S, y0*S, x1*S, y1*S], fill=fill, outline=outline, width=int(w*S))
    def ell(x0, y0, x1, y1, fill=None, outline=None, w=0):
        d.ellipse([x0*S, y0*S, x1*S, y1*S], fill=fill, outline=outline, width=int(w*S))
    def lin(pts, fill=None, w=5):
        d.line([(px*S, py*S) for px, py in pts], fill=fill, width=int(w*S), joint="curve")
    if kind == "base":                       # cilindro de base de datos
        rec(x, y + s*0.14, x + s, y + s*0.82, fill=c)
        ell(x, y, x + s, y + s*0.30, fill=c)
        ell(x, y + s*0.66, x + s, y + s*0.96, fill=c)
        ell(x + s*0.10, y + s*0.74, x + s*0.90, y + s*0.88, fill=(0, 0, 0, 0))
    elif kind == "llave":
        ell(x, y, x + s*0.44, y + s*0.44, outline=c, w=9)
        lin([(x + s*0.33, y + s*0.33), (x + s*0.96, y + s*0.96)], fill=c, w=9)
        lin([(x + s*0.70, y + s*0.70), (x + s*0.86, y + s*0.54)], fill=c, w=9)
        lin([(x + s*0.82, y + s*0.82), (x + s*0.98, y + s*0.66)], fill=c, w=9)
    elif kind == "escudo":
        d.polygon([(x*S, (y + s*0.10)*S), ((x + s)*S, (y + s*0.10)*S), ((x + s)*S, (y + s*0.52)*S),
                   ((x + s*0.5)*S, (y + s)*S), (x*S, (y + s*0.52)*S)], fill=c)
    elif kind == "alerta":
        d.polygon([((x + s*0.5)*S, y*S), ((x + s)*S, (y + s)*S), (x*S, (y + s)*S)], fill=c)
        rec(x + s*0.455, y + s*0.36, x + s*0.545, y + s*0.66, fill=(0, 0, 0, 0))
        ell(x + s*0.44, y + s*0.72, x + s*0.56, y + s*0.84, fill=(0, 0, 0, 0))
    elif kind == "codigo":
        lin([(x + s*0.40, y + s*0.10), (x + s*0.06, y + s*0.50), (x + s*0.40, y + s*0.90)], fill=c, w=10)
        lin([(x + s*0.60, y + s*0.10), (x + s*0.94, y + s*0.50), (x + s*0.60, y + s*0.90)], fill=c, w=10)


def _el_eyebrow(im, d, e):
    track(d, (e.get("x", 70), e.get("y", 300)), e["texto"].upper(), mono(e.get("size", 28)),
          e.get("color", TURQ), tr=3.2)


def _el_titulo(im, d, e):
    size = int(e.get("size", 76)); x = e.get("x", 70); y = e.get("y", 356)
    lh = float(e.get("lh", 1.14)); f = font(size); maxw = int(e.get("max_w", 960))
    for linea in e["lineas"]:
        cx = x
        for run in linea:
            txt(d, (cx, y), run[0], f, run[1])
            cx += d.textlength(run[0], font=f) / SS
        if cx - x > maxw:
            print("  ⚠ titular demasiado ancho (%d px > %d): %s" % (cx - x, maxw, linea))
        y += size * lh


def _el_panel(im, d, e):
    x, y, w, h = e["x"], e["y"], e["w"], e["h"]
    rr(d, (x, y, x + w, y + h), int(e.get("r", 24)), fill=_rgba(e.get("fill", PANEL)),
       outline=_rgba(e.get("color", LINE)), width=2)
    if e.get("label"):
        track(d, (x + 36, y + 32), e["label"].upper(), mono(25), e.get("color", TURQ), tr=3.0)


def _el_chips(im, d, e):
    x, y = e["x"], e["y"]; h = int(e.get("h", 64)); fs = int(e.get("size", 30))
    pad = int(e.get("padx", 26)); gap = int(e.get("gap", 14)); maxw = int(e.get("max_w", 1012))
    f = font(fs); cx = x
    for it in e["items"]:
        wpx = d.textlength(it, font=f) / SS + 2 * pad
        if cx + wpx > maxw and cx > x:
            cx = x; y += h + gap
        rr(d, (cx, y, cx + wpx, y + h), h / 2, fill=_rgba(e.get("fill", "#12222E")),
           outline=_rgba(e.get("color", TURQ)), width=2)
        txt(d, (cx + pad, y + (h - fs * 1.36) / 2 + 2), it, f, e.get("color", TURQ))
        cx += wpx + gap


def _el_nota(im, d, e):
    txt(d, (e["x"], e["y"]), e["texto"], font(int(e.get("size", 36))), e.get("color", DETAIL))


def _el_fila(im, d, e):
    x, y, w, h = e["x"], e["y"], e["w"], e["h"]; fs = int(e.get("size", 30))
    rr(d, (x, y, x + w, y + h), 20, fill=_rgba(PANEL), outline=_rgba(LINE), width=2)
    d.rectangle([x*SS, y*SS, (x + 7)*SS, (y + h)*SS], fill=_rgba(e.get("color", TURQ)))
    track(d, (x + 36, y + 24), e["tag"].upper(), mono(24), e.get("color", TURQ), tr=2.8)
    txt(d, (x + 36, y + 64), e["src"], mono(fs), SOFT)
    txt(d, (x + w - 36, y + 54), e["val"], mono(fs), WHITE, anchor="ra")


def _el_codigo(im, d, e):
    x, y, w = e["x"], e["y"], e["w"]; n = len(e["lineas"])
    rr(d, (x, y, x + w, y + 124 + n * 58), 24, fill=_rgba(PANEL), outline=_rgba(LINE), width=2)
    txt(d, (x + 34, y + 30), e["path"], mono(24), TURQ)
    d.rectangle([(x + 34)*SS, (y + 72)*SS, (x + w - 34)*SS, (y + 73)*SS], fill=_rgba(LINE))
    yy = y + 96
    for num, code in e["lineas"]:
        txt(d, (x + 40, yy), num, mono(26), "#3F5566")
        txt(d, (x + 112, yy), code, mono(26), SOFT)
        yy += 58


def _el_codigo_hot(im, d, e):
    x, y, w = e["x"], e["y"], e["w"]; yy = y + 96 + int(e.get("linea", 0)) * 58
    rr(d, (x + 18, yy - 8, x + w - 18, yy + 50), 12, fill=_rgba("#16283A"))
    d.rectangle([(x + 18)*SS, (yy - 8)*SS, (x + 25)*SS, (yy + 50)*SS], fill=_rgba(e.get("color", ORANGE)))
    txt(d, (x + 40, yy), e["num"], mono(26), e.get("color", ORANGE))
    txt(d, (x + 112, yy), e["code"], mono(26), WHITE)


def _el_pill(im, d, e):
    pill(d, e.get("cx", W / 2), e["y"], e["texto"], e.get("color", TURQ),
         fs=int(e.get("size", 34)), h=int(e.get("h", 86)), fill=_rgba(e.get("fill", "#0F2A2A")))


def _el_item(im, d, e):
    x, y = e["x"], e["y"]; c = e.get("color", ORANGE)
    d.ellipse([x*SS, (y + 12)*SS, (x + 13)*SS, (y + 25)*SS], fill=_rgba(c))
    txt(d, (x + 38, y), e["texto"], font(int(e.get("size", 40))), WHITE)


def _el_tarjeta(im, d, e):
    x, y, w, h = e["x"], e["y"], e["w"], e["h"]
    rr(d, (x, y, x + w, y + h), 22, fill=_rgba(PANEL), outline=_rgba(e.get("color", LINE)), width=2)
    txt(d, (x + 36, y + 22), e["titulo"], font(int(e.get("size", 40))), e.get("color", WHITE))
    if e.get("sub"):
        txt(d, (x + 36, y + 72), e["sub"], font(int(e.get("size2", 27))), DETAIL)


def _el_placa(im, d, e):
    im.paste(background(1.0).convert("RGBA"), (0, 0))
    d2 = ImageDraw.Draw(im)
    brandbar(im, d2)
    d2.rectangle([92*SS, 1436*SS, (W - 92)*SS, 1438*SS], fill=_rgba("#1C3542"))


def _el_marca(im, d, e):
    icon(d, e.get("icono", "escudo"), e.get("x", 690), e.get("y", 1120), int(e.get("size", 260)),
         e.get("color", TURQ), a=int(e.get("alpha", 40)))


ELEMS = {
    "eyebrow": _el_eyebrow, "titulo": _el_titulo, "panel": _el_panel, "chips": _el_chips,
    "nota": _el_nota, "fila": _el_fila, "codigo": _el_codigo, "codigo_hot": _el_codigo_hot,
    "pill": _el_pill, "item": _el_item, "tarjeta": _el_tarjeta, "placa": _el_placa,
    "marca": _el_marca,
}


def render_reveal(spec, outdir):
    """shot00.jpg (fondo fijo) + un el_<id>.png transparente por elemento."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    # el spec usa '0xRRGGBB' (como las tarjetas); PIL quiere '#RRGGBB'
    for sc in spec["escenas"]:
        for el in sc["elementos"]:
            for k in ("color", "fill"):
                if isinstance(el.get(k), str) and el[k].lower().startswith("0x"):
                    el[k] = "#" + el[k][2:]
            for ln in (el.get("lineas") or []):
                for run in ln:
                    if len(run) > 1 and isinstance(run[1], str) and run[1].lower().startswith("0x"):
                        run[1] = "#" + run[1][2:]
    im = background(0.72).convert("RGBA")
    d = ImageDraw.Draw(im)
    brandbar(im, d)
    im.resize((W, H), Image.LANCZOS).convert("RGB").save(
        outdir / "shot00.jpg", "JPEG", quality=94, optimize=True, subsampling=0)
    print("· shot00.jpg (fondo fijo 1080x1920)")
    n = 0
    for sc in spec["escenas"]:
        for el in sc["elementos"]:
            fn = ELEMS.get(el["tipo"])
            if fn is None:
                raise SystemExit("tipo de elemento desconocido: %r (%s)" % (el["tipo"], el["id"]))
            lienzo = Image.new("RGBA", (W*SS, H*SS), (0, 0, 0, 0))
            fn(lienzo, ImageDraw.Draw(lienzo), el)
            p = outdir / ("el_%s.png" % el["id"])
            lienzo.resize((W, H), Image.LANCZOS).save(p, "PNG", optimize=True)
            n += 1
            print("  · %-16s %s" % (p.name, el["tipo"]))
    print("· %d elementos + shot00.jpg en %s" % (n, outdir))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default=str(_HERE / "video-s01.json"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--solo", nargs="*", type=int, help="solo estas tarjetas (modo cards)")
    a = ap.parse_args()
    outdir = Path(a.out)
    outdir.mkdir(parents=True, exist_ok=True)

    sp = json.loads(Path(a.spec).read_text(encoding="utf-8")) if Path(a.spec).exists() else {}
    if (sp.get("images") or {}).get("mode") == "reveal":
        render_reveal(sp, outdir)
        return 0

    if a.solo:
        usadas = a.solo
    elif sp:
        usadas = sorted({int(p[0]) for p in (sp.get("plan") or [])})
    else:
        usadas = sorted(CARDS)

    falta = [n for n in usadas if n not in CARDS]
    if falta:
        raise SystemExit("no hay generador para: %s" % falta)
    for n in usadas:
        CARDS[n](outdir)
    print("· %d tarjetas listas en %s" % (len(usadas), outdir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
