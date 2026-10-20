import json
from pathlib import Path

cells = []
def md(s): cells.append({"cell_type":"markdown","metadata":{},"source":s.strip().splitlines(True)})
def code(s): cells.append({"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":s.strip().splitlines(True)})

# --- SPEC: scripts/video-01.json es la FUENTE UNICA de la voz y del texto ---
# Las 8 frases (phrases[].voice_es) se concatenan para formar el TEXTO que se
# sintetiza. build_nb.py (este fichero) y gen_voice.py (CI) leen el MISMO JSON:
# si el guion cambia, cambian los dos a la vez -> no se pueden desincronizar.
import json as _json
_ENGINE_DIR = Path(__file__).resolve().parent
_SPEC = _json.loads((_ENGINE_DIR / 'scripts' / 'video-01.json').read_text(encoding='utf-8'))
_VOICE = _SPEC['voice']['voice_id']
_RATE = _SPEC['voice']['rate']
_TEXT = ' '.join(p['voice_es'] for p in _SPEC['phrases'])
print('spec:', _VOICE, _RATE, '·', len(_TEXT.split()), 'palabras ·', len(_SPEC['phrases']), 'frases')

md("""# motor-video · Video 01 v10 — 16 planos, hook HONESTO (0 vulnerabilidades + lo que no se pudo saber)

**Las imagenes mandan**: cada plano es una imagen IA que ilustra lo que dice la voz en ese tramo.
16 planos (10 reutilizados del dataset + 7 nuevos shot21..shot27), cortes duros ~1.5-2.2s (ritmo Shorts),
narrativa de color: turquesa marca → verde = 0 activos → naranja = atencion → violeta = lo desconocido → turquesa = transparencia.
Tipografia REAL para intro/CTA en ASS (D-VM-04: la IA nunca dibuja texto) + animaciones ASS
(scrim, subrayado, entradas) y **lecho musical sintetizado en el runner** (numpy, sin descargas ni licencias)
mezclado con sidechain bajo la voz + cola final con fade.
Subtitulos **EN karaoke** palabra a palabra (el audio queda en espanol — SPEC D-VM-06).

Pipeline: 20 imagenes FLUX (dataset motor-media) → crop 9:16 → upscale x4 → Ken Burns sin temblor →
grading + vineta → scrim + intro animada (subrayado) + subtitulos EN + endcard CTA (placa) → voz Tomas (-12%) +
lecho musical procedural (numpy, sidechain) + cola con fade → QA gate → faststart. Sin GPU, sin internet, sin datos extra.
""")

_CELL1 = """
import os, subprocess, sys, json, urllib.request, zipfile
WORK = Path('/content/motor-video'); OUT = WORK/'out'; FDIR = WORK/'fonts'
OUT.mkdir(parents=True, exist_ok=True); FDIR.mkdir(parents=True, exist_ok=True)

# --- datasets: ESTATICO (modelo ESRGAN + fuentes) + MEDIA (voz + palabras + imagenes v6) ---
KINP = Path('/kaggle/input')
STATIC = KINP/'motor-assets' if (KINP/'motor-assets').exists() else Path('/kaggle/working')
MEDIA  = KINP/'motor-media' if (KINP/'motor-media').exists() else STATIC
ASSETS = WORK/'assets'; ASSETS.mkdir(parents=True, exist_ok=True)
# descomprimir (una vez): modelo del estatico; imagenes del media (fallback: estatico)
for _src, _name in ((STATIC/'models.zip', 'models'), (MEDIA/'imgs.zip', 'imgs'), (STATIC/'imgs.zip', 'imgs_fb')):
    if not _src.exists(): continue
    _dst = ASSETS/_name
    if _dst.exists() and any(_dst.iterdir()): continue
    _dst.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(_src) as zf: zf.extractall(_dst)
    print('descomprimido', _src.name, '->', _dst)
FONTFILE = None
for _c in (STATIC/'fonts'/'Poppins-Bold.ttf', STATIC/'Poppins-Bold.ttf', MEDIA/'fonts'/'Poppins-Bold.ttf', MEDIA/'Poppins-Bold.ttf'):
    if _c.exists(): FONTFILE = _c; break
if FONTFILE is None:
    FONTFILE = FDIR/'Poppins-Bold.ttf'
    try:
        urllib.request.urlretrieve('https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Bold.ttf', FONTFILE)
        print('fuente Poppins Bold OK (descargada)')
    except Exception as e:
        FONTFILE = Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
        print('Poppins no disponible, fallback DejaVu:', str(e)[:80])
else:
    print('fuente Poppins empaquetada OK:', FONTFILE)
if not (FDIR/'Poppins-Bold.ttf').exists() and Path(FONTFILE).exists():
    import shutil as _sh
    _sh.copy(str(FONTFILE), str(FDIR/'Poppins-Bold.ttf'))
    print('fuente copiada a fontsdir (subtitulos):', FDIR/'Poppins-Bold.ttf')

IMGDIR = None
for _p in (ASSETS/'imgs', MEDIA/'imgs', STATIC/'imgs_fb', Path('/content/motor-video/imgs')):
    if _p.exists() and any(_p.glob('shot*.jpg')): IMGDIR = _p; break
if IMGDIR is None: raise SystemExit('FALTAN las imagenes IA (shot*.jpg)')
NIMG = len(list(IMGDIR.glob('shot*.jpg')))
print('imagenes IA:', NIMG, 'en', IMGDIR)

# --- PLAN de 16 planos (la imagen MANDA): (imagen, frase 0-7, peso del tramo) ---
# v10: hook HONESTO. Se reutilizan 10 imagenes del dataset motor-media y se anaden
#      7 nuevas (shot21..shot27) con otro significado. Las imagenes del v9 (candado
#      roto, escudo agrietado, mascara de incognito, atacante, ojo rastreador,
#      grieta) YA NO SE USAN: el v9 afirmaba una vulnerabilidad que el informe
#      refuta. Ver investigacion/INFORME-REDES-2026.md sec.6.
PLAN = [
  (19, 0, 1.00),  # intro (estudio + codigo holografico) "Auditamos draw.io"
  (14, 0, 0.90),  # lupa de auditoria             "...y no encontramos ninguna vulnerabilidad"
  (21, 1, 1.00),  # NUEVO grafo de nodos          "34 MB de JavaScript, 3M de nodos"
  (13, 2, 1.00),  # versiones en fila            "El inventario dio 82 paquetes"
  (23, 2, 0.90),  # NUEVO tarjetas de paquetes   "...de cinco candidatas, ninguna activa"
  (22, 3, 1.00),  # NUEVO panel de codigo borroso"5 ventanas, 1 dinamica: no verificable"
  (24, 4, 1.00),  # NUEVO red de nodos (2 vivos)  "29 handlers de IPC, solo 2 con validacion"
  (25, 5, 1.00),  # NUEVO mar de puntos          "lo que no se pudo saber"
  (26, 6, 1.00),  # NUEVO contadores              "92.468 desconocidos con su ID"
  (16, 6, 0.80),  # candado verde                 "...y diez limites declarados"
  (17, 6, 0.80),  # cubo protegido
  (20, 7, 1.00),  # endcard                       "Si tu app es Electron, auditala"
  ( 9, 7, 0.70),  # 3 ajustes
  (10, 7, 0.70),  # laptop segura
  ( 8, 7, 0.60),  # boveda turquesa
  (11, 7, 0.60),  # fondo CTA
]
_missing = [i for i,_s,_w in PLAN if not (IMGDIR/('shot%02d.jpg'%i)).exists()]
if _missing: raise SystemExit('faltan imagenes del plan: %s' % _missing)
print('PLAN OK ·', len(PLAN), 'planos para 8 frases')

VOZ = __VOZ__   # rioplatense (viene de scripts/video-01.json)
TEXTO = __TEXTO__
"""

code(_CELL1.replace('__VOZ__', repr(_VOICE)).replace('__TEXTO__', repr(_TEXT)))

# Exporta la especificacion de voz para que gen_voice.py (que corre en CI, donde
# SI hay internet) use EXACTAMENTE el mismo texto y la misma voz. Fuente unica:
# si el TEXTO cambia aqui, cambia tambien en el audio -> no se desincronizan.
import json as _json
_voice_spec = {"voice": _VOICE, "rate": _RATE, "text": _TEXT}
Path(str(_ENGINE_DIR / 'voice-spec.json')).write_text(_json.dumps(_voice_spec, ensure_ascii=False, indent=1))
print('voice-spec.json escrito (voz, rate, texto)')

code("""
import asyncio, subprocess
# voz + palabras (dataset media; fallback estatico; ultimo recurso: edge-tts online = Colab)
words = []; _emb = False
for _b in dict.fromkeys((MEDIA, STATIC)):
    if (_b/'voz.mp3').exists() and (_b/'words.json').exists():
        import shutil
        shutil.copy(str(_b/'voz.mp3'), str(OUT/'voz.mp3'))
        words = json.loads((_b/'words.json').read_text()); _emb = True; break
if not _emb:
    import edge_tts
    async def _g():
        c = edge_tts.Communicate(TEXTO, VOZ, rate='-12%', boundary='WordBoundary')
        with open(str(OUT/'voz.mp3'),'wb') as f:
            async for ch in c.stream():
                if ch['type']=='audio': f.write(ch['data'])
                elif ch['type']=='WordBoundary':
                    words.append({'w':ch['text'],'t0':ch['offset']/1e7,'t1':(ch['offset']+ch['duration'])/1e7})
    asyncio.run(_g())
V = float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(OUT/'voz.mp3')],capture_output=True,text=True).stdout.strip())
print('voz:', round(V,2), 's ·', len(words), 'palabras', '(embebida del dataset)' if _emb else '(edge-tts)')
TAIL = 1.5                      # v8: cola final — la musica respira y el video funde a negro
TOTAL = round(V + TAIL, 3)

# --- limites de frase derivados de la voz -> tramos (todo se clava a la voz real) ---
import unicodedata
def _norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    return ''.join(c for c in w if c.isalnum())
LASTW = ['vulnerabilidad','nodos','activa','verificar','origen','saber','declarados','evidencia']
bnd, _pos = [], 0
for _lw in LASTW:
    _f = next((i for i in range(_pos, len(words)) if _norm(words[i]['w'])==_lw), None)
    if _f is None: raise SystemExit('no encontre el limite de frase: '+_lw)
    bnd.append(_f); _pos = _f+1
spans, _a = [], 0
for _b in bnd:
    spans.append((words[_a]['t0'], words[_b]['t1'])); _a = _b+1
print('frases (s):', [(round(s,2), round(e,2)) for s,e in spans])
# tramos CONTIGUOS de 0 a fin: la pausa entre frases la sostiene el ULTIMO plano de la frase
# (la imagen nueva entra EXACTAMENTE cuando suena la primera palabra de la frase)
rng = []
for si in range(len(spans)):
    s0 = 0.0 if si == 0 else spans[si][0]
    s1 = spans[si+1][0] if si+1 < len(spans) else V
    rng.append((s0, s1))

# --- SHOTS: reparto del tramo de cada frase entre sus planos (por peso) ---
ZI = [1.12, 1.16, 1.14, 1.18]
SHOTS = []
for si in range(len(spans)):
    s0, s1 = rng[si]
    grp = [(i, w) for i, s, w in PLAN if s == si]
    WT = sum(w for _, w in grp); acc = s0
    for j, (img, w) in enumerate(grp):
        t1 = s0 + (s1 - s0) * sum(x[1] for x in grp[:j+1]) / WT
        SHOTS.append((img, round(acc,3), round(t1,3), 'in' if len(SHOTS)%2==0 else 'out', ZI[len(SHOTS)%4]))
        acc = t1
_last = list(SHOTS[-1]); _last[2] = round(TOTAL, 3); SHOTS[-1] = tuple(_last)
print('SHOTS:', len(SHOTS), 'planos · fin', SHOTS[-1][2], 's · duraciones', [round(t1-t0,2) for _,t0,t1,_,_ in SHOTS])
for _s in SHOTS: print('  img%02d %5.2f-%5.2f %s' % (_s[0], _s[1], _s[2], _s[3]))

# --- acento de color por tramo (narrativa rojo -> turquesa, alineada a las frases) ---
ACC = [(spans[0][1],'0x8fe3cf'), (spans[1][1],'0x8fe3cf'), (spans[2][1],'0x4ade80'), (spans[3][1],'0xff7a3a'), (spans[4][1],'0x9aa4ff'), (spans[5][1],'0xc9a0ff'), (spans[6][1],'0x8fe3cf'), (10**9,'0x8fe3cf')]

# --- subtitulos EN karaoke palabra a palabra (audio ES — SPEC D-VM-06) ---
EN = [
 ['We','audited','draw.io','Desktop.','And','found','no','vulnerability.'],
 ['34','megabytes','of','JavaScript.','Over','3','million','nodes.'],
 ['82','packages.','Five','candidate','vulnerabilities,','none','active.'],
 ['Five','windows.','One','is','dynamic','and',"can't",'be','verified.'],
 ['29','IPC','handlers.','Only','two','with','sender','validation.'],
 ['What','matters','is','what','we',"couldn't",'know.'],
 ['92,468','unknowns,','each','with','its','ID.','Ten','declared','limits.'],
 ['If','your','app','is','Electron,','audit','it.','48','hours,','with','evidence.'],
]
KW = ('34','MILLION','PACKAGES','VULNERABILITIES','ACTIVE','WINDOWS','DYNAMIC','VERIFIED','HANDLERS','TWO','SENDER','VALIDATION','COULDN','92,468','UNKNOWNS','LIMITS','EVIDENCE','AUDIT','ELECTRON','32.4.1')
def hex2ass(h):  # '0xRRGGBB' -> '&H00BBGGRR&' (BGR de ASS)
    r,g,b = h[2:4], h[4:6], h[6:8]
    return ('&H00%s%s%s&' % (b,g,r)).upper()
def ts(t):
    return '%d:%02d:%05.2f' % (int(t//3600), int(t%3600//60), t%60)
def accent_at(t):
    for tmax, a in ACC:
        if t < tmax: return a
    return ACC[-1][1]
ev = []
for si, (s0, s1) in enumerate(spans):
    toks = EN[si]; m = len(toks)
    for j, tk in enumerate(toks):
        t0 = s0 + (s1-s0)*j/m
        t1 = s0 + (s1-s0)*(j+1)/m if j < m-1 else (spans[si+1][0] if si+1 < len(spans) else V)
        up = tk.upper().strip('.,;:!?…')
        txt = up
        if any(up.startswith(k) for k in KW):
            txt = '{\\\\1c%s}%s{\\\\1c&H00FFFFFF&}' % (hex2ass(accent_at(t0)), up)
        ev.append('Dialogue: 0,%s,%s,Cap,,0,0,0,,%s' % (ts(t0), ts(t1), txt))
# --- v8: intro animada (scrim + subrayado + entradas) y endcard reforzado — tipografia REAL en ASS (D-VM-04) ---
BS = chr(92)
def _grp(*tags): return '{' + BS.join([''] + list(tags)) + '}'
def _d(t0, t1, st, txt): return 'Dialogue: 0,%s,%s,%s,,0,0,0,,%s' % (ts(t0), ts(t1), st, txt)
def _ov(txt, y, fad_in=450, fad_out=300):
    return _grp('fad(%d,%d)' % (fad_in, fad_out), 'pos(540,%d)' % y) + txt
def _scrim(a='BA', fi=400, fo=350):
    return _grp('p1','an7','pos(0,0)','bord0','shad0','1c&H000000&','alpha&H%s&' % a,'fad(%d,%d)' % (fi, fo)) + 'm 0 0 l 1080 0 l 1080 1920 l 0 1920' + _grp('p0')
ev_bg, ev_fg = [], []
_i_end = spans[0][1] + 0.30
ev_bg.append(_d(0.20, _i_end, 'Scrim', _scrim('BA', 400, 350)))
ev_fg.append(_d(0.62, _i_end, 'Bar', _grp('p1','an5','pos(540,700)','bord0','shad0','fad(160,230)') + 'm 0 0 l 320 0 l 320 7 l 0 7' + _grp('p0')))
ev_fg.append(_d(0.25, _i_end, 'Brand', _grp('fad(280,240)','move(540,678,540,650,0,420)') + 'AUDIT WITH PROOF'))
ev_fg.append(_d(0.50, _i_end, 'Title', _grp('fad(300,240)','pos(540,815)','fscx92','fscy92','t(0,460,'+BS+'fscx100'+BS+'fscy100)') + '0 VULNERABILIDADES'))
ev_fg.append(_d(0.80, _i_end, 'Sub', _grp('fad(320,240)','move(540,952,540,935,0,380)') + 'draw.io Desktop 32.4.1'))
ev_fg.append(_d(1.05, _i_end, 'Sub', _grp('fad(320,240)','move(540,1022,540,1005,0,380)') + 'y lo que no se pudo saber'))
_ei = [i for i, s in enumerate(SHOTS) if s[0] == 20]
_t_link = next((w['t0'] for w in words if _norm(w['w']) == 'link'), None)
if _ei:
    t_e = SHOTS[_ei[0]][1] + 0.15
    ev_bg.append(_d(t_e - 0.15, TOTAL, 'Scrim', _scrim('BA', 420, 320)))
    ev_fg.append(_d(t_e + 0.20, TOTAL, 'Brand', _grp('fad(280,400)','move(540,668,540,640,0,420)') + 'AUDIT WITH PROOF'))
    ev_fg.append(_d(t_e + 0.40, TOTAL, 'Title', _grp('fad(300,400)','pos(540,830)','fscx92','fscy92','t(0,460,'+BS+'fscx100'+BS+'fscy100)') + '¿TU APP ES ELECTRON?'))
    ev_fg.append(_d(t_e + 0.65, TOTAL, 'Sub', _ov('Informe en 48 h · evidencia verificable', 990, 420, 400)))
    ev_fg.append(_d(t_e + 0.85, TOTAL, 'Sub', _ov('PARTE 2 · lo que no se pudo saber', 1065, 420, 400)))
    t0l = max(t_e + 0.25, (_t_link - 0.20) if _t_link is not None else t_e + 1.1)
    ev_fg.append(_d(t0l - 0.15, TOTAL, 'Bar', _grp('p1','an5','pos(540,1300)','fad(160,420)','1c&H141414&','alpha&H28&','bord0','shad0') + 'm 0 0 l 520 0 l 520 112 l 0 112' + _grp('p0')))
    ev_fg.append(_d(t0l, TOTAL, 'Link', _grp('fad(300,420)','pos(540,1300)','t(160,700,'+BS+'fscx108'+BS+'fscy108)') + 'LINK EN LA BIO'))
ass_lines = ['[Script Info]', 'ScriptType: v4.00+', 'PlayResX: 1080', 'PlayResY: 1920',
 'WrapStyle: 2', 'ScaledBorderAndShadow: yes', '[V4+ Styles]',
 'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
 'Style: Cap,Poppins,74,&H00FFFFFF,&H00FFFFFF,&H00101010,&H96000000,-1,0,1,5,2,2,90,90,300,1',
 'Style: Brand,Poppins,38,&H00CFE38F,&H00CFE38F,&H00101010,&H96000000,-1,0,1,4,2,5,80,80,0,1',
 'Style: Title,Poppins,80,&H00FFFFFF,&H00FFFFFF,&H00101010,&H96000000,-1,0,1,6,3,5,80,80,0,1',
 'Style: Sub,Poppins,42,&H00FFFFFF,&H00FFFFFF,&H00101010,&H96000000,-1,0,1,4,2,5,80,80,0,1',
 'Style: Link,Poppins,60,&H00CFE38F,&H00CFE38F,&H00101010,&H96000000,-1,0,1,5,2,5,80,80,0,1',
 'Style: Scrim,Poppins,20,&H00FFFFFF,&H00FFFFFF,&H00FFFFFF,&H00000000,0,0,1,0,0,7,0,0,0,1',
 'Style: Bar,Poppins,20,&H00CFE38F,&H00CFE38F,&H00CFE38F,&H00000000,0,0,1,0,0,5,0,0,0,1',
 '[Events]', 'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
ev = ev_bg + ev + ev_fg   # scrims al fondo (detras de caps) · intro/CTA encima
ass = chr(10).join(ass_lines + ev) + chr(10)
(OUT/'cap.ass').write_text(ass)
print('cap.ass EN OK ·', len(ev), 'dialogos ·', len(spans), 'frases · v8 scrim+anims+placa · TOTAL', round(TOTAL,2), 's')
""")

code("""
# --- v8: lecho musical 100% procedural en el runner (numpy): pad + bajo + pulso + whooshes ---
# Sin descargas ni licencias (R1/SPEC): se sintetiza aqui, clavado a la narrativa:
#   intro (pad suave) -> tension (Am-F-Dm-E) -> solucion (C-G-Am-F) -> cierre (C + fade).
import numpy as np, wave as _wv
_ei2 = [i for i, s in enumerate(SHOTS) if s[0] == 20]
t_e = SHOTS[_ei2[0]][1] + 0.15
SRM = 44100
NM = int(SRM * TOTAL)
_mix = np.zeros(NM)
def _osc(tt, f):
    return np.sin(2*np.pi*f*tt) + 0.45*np.sin(2*np.pi*f*1.004*tt) + 0.22*np.sin(2*np.pi*f*0.9968*tt)
def _note(buf, t0, dur, freqs, amp, atk=0.7, rel=0.9):
    i0 = max(0, int(t0*SRM)); i1 = min(NM, int((t0+dur)*SRM))
    if i1 <= i0: return
    tt = np.arange(i1-i0)/SRM
    e = np.clip(tt/atk, 0, 1)*np.clip((dur-tt)/rel, 0, 1)
    s = np.zeros(i1-i0)
    for f, a in freqs: s = s + a*_osc(tt, f)
    buf[i0:i1] += amp*e*s
def _kick(buf, t0, amp=1.0):
    dur = 0.34; i0 = max(0, int(t0*SRM)); i1 = min(NM, int((t0+dur)*SRM)); tt = np.arange(i1-i0)/SRM
    f = 47 + 40*np.exp(-tt/0.045)
    buf[i0:i1] += amp*np.sin(2*np.pi*np.cumsum(f)/SRM)*np.exp(-tt/0.14)
def _whoosh(buf, t0, dur=0.65, amp=1.0):
    i0 = max(0, int(t0*SRM)); i1 = min(NM, int((t0+dur)*SRM)); n = i1-i0
    if n <= 1: return
    x = np.random.default_rng(7).standard_normal(n)
    k = max(3, int(SRM*0.0011)); lp = np.convolve(x, np.ones(k)/k, 'same')
    s = 0.75*lp + 0.25*x; s = s/(np.max(np.abs(s))+1e-9)
    e = np.clip(np.sin(np.pi*np.arange(n)/max(1, n-1)), 0, 1)**1.6
    buf[i0:i1] += amp*e*s
CH = {'Am': (110.00, [220.00, 261.63, 329.63]), 'F': (87.31, [174.61, 220.00, 261.63]),
      'Dm': (73.42, [146.83, 174.61, 220.00]), 'E': (82.41, [164.81, 207.65, 246.94]),
      'C': (130.81, [261.63, 329.63, 392.00]), 'G': (98.00, [196.00, 246.94, 293.66])}
def _chord(name, t0, dur, gain=1.0):
    b, fs = CH[name]
    _note(_mix, t0, dur, [(b, 1.0)], 0.075*gain, 0.9, 1.0)
    _note(_mix, t0, dur, [(f, 1.0) for f in fs], 0.085*gain, 0.9, 1.0)
ARP = [0, 1, 2, 1, 0, 1, 2, 1]
def _timeline(t0, t1, cycle, gain=1.0, kick=True, arp=True):
    n = max(1, int(round((t1-t0)/2.4)))
    step = (t1-t0)/n
    for j in range(n):
        ch = cycle[j % len(cycle)]
        _chord(ch, t0+j*step, step*1.15, gain)
        if kick:
            _kick(_mix, t0+j*step, 0.10*gain); _kick(_mix, t0+j*step+step/2, 0.07*gain)
        if arp:
            fs = CH[ch][1]
            for k in range(8):
                _note(_mix, t0+j*step+k*0.3, 0.30, [(fs[ARP[k]]*2, 1.0)], 0.030*gain, 0.02, 0.22)
_sec_fix = spans[5][0]
_timeline(0.0, _i_end, ['Am', 'F'], gain=0.75, kick=False, arp=False)
_timeline(_i_end, _sec_fix, ['Am', 'F', 'Dm', 'E'], gain=1.0, kick=True, arp=True)
_timeline(_sec_fix, t_e, ['C', 'G', 'Am', 'F'], gain=1.0, kick=True, arp=True)
_chord('C', t_e, TOTAL-t_e+0.1, gain=0.85)
_whoosh(_mix, 0.12, 0.75, 0.20)
_whoosh(_mix, t_e-0.10, 0.55, 0.16)
_kick(_mix, t_e+0.02, 0.10)
_envg = np.ones(NM)
_fi = int(0.6*SRM); _envg[:_fi] = np.linspace(0, 1, _fi)
_fo = int(1.6*SRM); _envg[-_fo:] = _envg[-_fo:]*np.linspace(1, 0, _fo)
_mix = _mix*_envg
_mix = np.nan_to_num(_mix)   # guarda anti-NaN (power sobre bordes negativos)
_mix = _mix/(np.max(np.abs(_mix))+1e-9)*0.9*0.095   # 0.095: lecho ~13.5 dB bajo la voz (medido local)
_st = np.stack([_mix, _mix], axis=1)
_pcm = np.clip(_st*32767, -32768, 32767).astype('<i2')
with _wv.open(str(OUT/'bed.wav'), 'wb') as _f:
    _f.setnchannels(2); _f.setsampwidth(2); _f.setframerate(SRM); _f.writeframes(_pcm.tobytes())
print('bed.wav OK ·', round(NM/SRM, 2), 's · pico', round(20*np.log10(np.max(np.abs(_mix))+1e-9), 1), 'dBFS')
""")

code("""
# --- imagenes IA -> 9:16 -> Real-ESRGAN x4 (modelo del dataset, CPU del runner) ---
import time, cv2, numpy as np
MODEL = None
for _p in (ASSETS/'models'/'Real-ESRGAN-x4plus.onnx', STATIC/'models'/'Real-ESRGAN-x4plus.onnx', MEDIA/'models'/'Real-ESRGAN-x4plus.onnx', Path('/content/motor-video/Real-ESRGAN-x4plus.onnx')):
    if _p.exists(): MODEL = str(_p); break
sess = None
if MODEL:
    try:
        import onnxruntime as ort
        so = ort.SessionOptions(); so.intra_op_num_threads = max(2, (os.cpu_count() or 4)//2)
        sess = ort.InferenceSession(MODEL, so, providers=['CPUExecutionProvider'])
        print('Real-ESRGAN x4 listo ·', round(os.path.getsize(MODEL)/1e6,1), 'MB · hilos', so.intra_op_num_threads)
    except Exception as e:
        print('onnxruntime no disponible -> fallback Lanczos:', str(e)[:100])
else:
    print('modelo ESRGAN no encontrado -> fallback Lanczos')

MEAN = np.array((0.4488, 0.4371, 0.4040), dtype=np.float32).reshape(1, 3, 1, 1)
def esrgan_x4(bgr):
    h, w = bgr.shape[:2]
    tile, pad = 256, 16
    out = np.zeros((h*4, w*4, 3), dtype=np.float32)
    for y in range(0, h, tile):
        for x in range(0, w, tile):
            y1, x1 = min(y+tile, h), min(x+tile, w)
            ys, xs = max(0, y-pad), max(0, x-pad)
            ye, xe = min(h, y1+pad), min(w, x1+pad)
            t = bgr[ys:ye, xs:xe].astype(np.float32) / 255.0
            t = cv2.cvtColor(t, cv2.COLOR_BGR2RGB)
            t = np.transpose(t, (2, 0, 1))[None] - MEAN
            o = sess.run(None, {sess.get_inputs()[0].name: t})[0] + MEAN
            o = np.clip(o[0].transpose(1, 2, 0), 0.0, 1.0) * 255.0
            out[y*4:y1*4, x*4:x1*4] = o[(y-ys)*4:(y-ys)*4+(y1-y)*4, (x-xs)*4:(x-xs)*4+(x1-x)*4]
    return out.astype(np.uint8)
def crop916(img):  # cuadrado 1024 -> 9:16 central (576x1024)
    h, w = img.shape[:2]
    cw = int(h * 9 / 16); x0 = (w - cw) // 2
    return img[:, x0:x0+cw]

t_all = time.time()
for idx in sorted({s[0] for s in SHOTS}):
    dst = OUT / ('up_%02d.png' % idx)
    if dst.exists(): continue
    img = cv2.imread(str(IMGDIR / ('shot%02d.jpg' % idx)))
    if img is None: raise SystemExit('imagen ilegible: shot%02d.jpg' % idx)
    c = crop916(img)
    t0 = time.time()
    if sess is not None:
        big = esrgan_x4(c)                       # 576x1024 -> 2304x4096
    else:
        big = cv2.resize(c, None, fx=4, fy=4, interpolation=cv2.INTER_LANCZOS4)
    fin = cv2.resize(big, (2160, 3840), interpolation=cv2.INTER_AREA)
    cv2.imwrite(str(dst), fin)
    print('up %02d: %s -> 2160x3840 · %.1fs (%s)' % (idx, c.shape[:2], time.time()-t0, 'ESRGAN' if sess else 'lanczos'))
print('upscale total: %.1fs' % (time.time()-t_all))
""")

code("""
# --- plano a plano: Ken Burns sin temblor (buffer 2160x3840) + grading + cortes duros ---
import subprocess
W,H,FPS=1080,1920,30
def shot(idx, ds, Z, mode, name):
    N = max(int(round(ds*FPS)), 2)
    ease = '(1-cos(PI*on/%d))/2' % (N-1)
    zexpr = ('1+%s*%s' % (round(Z-1,4), ease)) if mode=='in' else ('%s-%s*%s' % (Z, round(Z-1,4), ease))
    filt = ("zoompan=z='%s':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=%dx%d:fps=30,"
            'format=yuv420p,eq=contrast=1.05:saturation=1.10:brightness=0.004,vignette=PI/4.8') % (zexpr, W, H)
    r = subprocess.run(['ffmpeg','-y','-loop','1','-framerate','30','-i',str(OUT/('up_%02d.png'%idx)),
        '-filter_complex',filt,'-t',str(ds),'-r','30','-c:v','libx264','-crf','19','-preset','medium',
        '-pix_fmt','yuv420p','-an',str(OUT/('s_%s.mp4'%name))],capture_output=True,text=True)
    if r.returncode != 0: raise SystemExit('fallo plano %s: %s' % (name, r.stderr[-300:]))
    print('plano', name, 'img%02d'%idx, mode, ds, 's')

for i,(idx,t0,t1,mode,Z) in enumerate(SHOTS):
    shot(idx, round(t1-t0,3), Z, mode, '%02d'%i)

lst = OUT/'shots.txt'; lst.write_text(''.join("file '%s'\\n" % (OUT/('s_%02d.mp4'%i)) for i in range(len(SHOTS))))
subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i',str(lst),'-c','copy',str(OUT/'video.mp4')],check=True)
print('montaje:', len(SHOTS), 'planos ->', round(sum(t1-t0 for _,t0,t1,_,_ in SHOTS),2), 's')
""")

code("""
# --- subtitulos quemados (fade final) + voz + musica con sidechain + faststart ---
import subprocess
video = OUT/'video.mp4'
cap = OUT/'video_cap.mp4'
vf = 'ass=%s:fontsdir=%s,fade=t=out:st=%.2f:d=0.7' % (OUT/'cap.ass', FDIR, TOTAL-0.7)
r = subprocess.run(['ffmpeg','-y','-i',str(video),'-vf',vf,'-c:v','libx264','-crf','19','-preset','medium','-pix_fmt','yuv420p','-an',str(cap)],capture_output=True,text=True)
if r.returncode != 0:
    print('ass no disponible, video sin subtitulos:', r.stderr[-150:]); cap = video
bed = OUT/'bed.wav'; mixw = OUT/'mix.wav'
_duck = ('[0:a]apad=pad_dur=%.2f,atrim=0:%.2f[va];[va]asplit=2[va1][vak];'
         '[1:a]volume=1.0[mu];[mu][vak]sidechaincompress=threshold=0.03:ratio=4:attack=25:release=350[md];'
         '[va1][md]amix=inputs=2:duration=first:normalize=0[mx]') % (TAIL+0.5, TOTAL)
r = subprocess.run(['ffmpeg','-y','-i',str(OUT/'voz.mp3'),'-i',str(bed),'-filter_complex',_duck,'-map','[mx]','-c:a','pcm_s16le',str(mixw)],capture_output=True,text=True)
if r.returncode != 0:
    print('sidechain no disponible, mezcla simple:', r.stderr[-200:])
    _duck = ('[0:a]apad=pad_dur=%.2f,atrim=0:%.2f[va];[va][1:a]amix=inputs=2:duration=first:normalize=0[mx]') % (TAIL+0.5, TOTAL)
    subprocess.run(['ffmpeg','-y','-i',str(OUT/'voz.mp3'),'-i',str(bed),'-filter_complex',_duck,'-map','[mx]','-c:a','pcm_s16le',str(mixw)],check=True)
# loudnorm 2-pases (exacto -14 LUFS): analisis JSON -> pase lineal (sin bombeo dinamico)
_an = subprocess.run(['ffmpeg','-i',str(mixw),'-af','loudnorm=I=-14:TP=-1.5:print_format=json','-f','null','-'],capture_output=True,text=True).stderr
_M = json.loads(_an[_an.rfind('{'):_an.rfind('}')+1])
_ln = ('loudnorm=I=-14:TP=-1.5:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true' %
       (_M['input_i'], _M['input_tp'], _M['input_lra'], _M['input_thresh'], _M['target_offset']))
r = subprocess.run(['ffmpeg','-y','-i',str(cap),'-i',str(mixw),'-filter_complex','[1:a]%s,afade=t=out:st=%.2f:d=1.2[a]' % (_ln, TOTAL-1.4),'-map','0:v:0','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-t',str(TOTAL),'-movflags','+faststart',str(OUT/'video-01.mp4')],capture_output=True,text=True)
if r.returncode != 0:
    print('loudnorm 2-pase fallo, fallback 1-pase:', r.stderr[-200:])
    subprocess.run(['ffmpeg','-y','-i',str(cap),'-i',str(mixw),'-filter_complex','[1:a]loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=out:st=%.2f:d=1.2[a]' % (TOTAL-1.4),'-map','0:v:0','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-t',str(TOTAL),'-movflags','+faststart',str(OUT/'video-01.mp4')],check=True)
print('video-01.mp4 listo ·', round(TOTAL,2), 's · voz + musica (sidechain) + loudnorm 2-pases + faststart')
""")

code("""
import subprocess, json, re
p=str(OUT/'video-01.mp4')
info=json.loads(subprocess.run(['ffprobe','-v','error','-show_entries','stream=width,height,codec_type:format=duration','-of','json',p],capture_output=True,text=True).stdout)
dur=float(info['format']['duration']); st={s['codec_type']:s for s in info['streams']}
w,h=st['video']['width'],st['video']['height']; audio='audio' in st
faststart=b'moov' in open(p,'rb').read(262144)
sync=abs(dur - TOTAL) <= 0.5
_ls = subprocess.run(['ffmpeg','-i',p,'-af','ebur128','-f','null','-'],capture_output=True,text=True).stderr
_ms = re.findall(r'I:\\s+(-?[\\d.]+) LUFS', _ls); lufs = float(_ms[-1]) if _ms else None  # ultimo match = resumen ebur128 (los primeros son lineas de progreso)
ok=(w,h)==(1080,1920) and dur<=60 and audio and faststart and sync and (lufs is not None) and (-16 <= lufs <= -13)
qa={'res':f'{w}x{h}','dur':round(dur,2),'voz':round(V,2),'total':round(TOTAL,2),'lufs':lufs,'audio':audio,'faststart':faststart,'sync':sync,'QA':'PASS' if ok else 'FAIL','version':'v9','brand':'AUDIT WITH PROOF'}
print(json.dumps(qa))
# El veredicto también queda como fichero: se descarga en KB (no el mp4 de 15 MB)
try:
    Path('/kaggle/working/qa-video-01.json').write_text(json.dumps(qa, indent=1))
except Exception as _e:
    pass
assert ok, 'QA FAIL'
""")

code("""
# en Colab se descarga solo; en Kaggle lo copia al output del kernel
try:
    from google.colab import files
    files.download(str(OUT/'video-01.mp4'))
except ImportError:
    import shutil
    shutil.copy(str(OUT/'video-01.mp4'), '/kaggle/working/video-01.mp4')
    print('video-01.mp4 copiado a /kaggle/working (output del kernel)')
""")

nb={"cells":cells,"metadata":{"colab":{"provenance":[]},"kernelspec":{"name":"python3","display_name":"Python 3"},"language_info":{"name":"python"}},"nbformat":4,"nbformat_minor":4}

# render.ipynb (Colab, rutas /content) y kernel.ipynb (Kaggle, rutas /kaggle/working)
src = json.dumps(nb, ensure_ascii=False, indent=1)
# Rutas relativas al propio script: el mismo build_nb.py sirve en local y en CI.
import os as _os
_ENG = Path(_os.environ.get('ENGINE_DIR', _os.path.dirname(_os.path.abspath(__file__))))
_ENG.mkdir(parents=True, exist_ok=True)
Path(str(_ENG / 'render.ipynb')).write_text(src)
kag = src.replace('/content/motor-video', '/kaggle/working/motor-video')
# La ruta de salida del kernel es configurable: en CI no es /tmp/opencode.
import os as _os
_KOUT = _os.environ.get('KERNEL_OUT_DIR', '/tmp/opencode/kag')
Path(_KOUT).mkdir(parents=True, exist_ok=True)
Path(_KOUT + '/kernel.ipynb').write_text(kag)
print('kernel.ipynb ->', _KOUT + '/kernel.ipynb')

# validar: JSON + cada celda compila
for name, txt in (('render.ipynb', src), ('kernel.ipynb', kag)):
    n = json.loads(txt)
    for i, c in enumerate(n['cells']):
        if c['cell_type'] == 'code' and not ''.join(c['source']).lstrip().startswith('%'):
            body = '\n'.join(l for l in ''.join(c['source']).splitlines() if not l.strip().startswith('%'))
            compile(body, f'cell{i}', 'exec')
    print(name, 'OK · celdas:', len(n['cells']))
print('escrito: render.ipynb (Colab) + kernel.ipynb (Kaggle)')
