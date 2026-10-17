# GUION — Vídeo #1 (muestra de estilo · video-cero)

> Formato: **Short vertical 1080×1920 · ≤60 s · faceless · ES voz + subs EN karaoke**
> Fuente de datos: **real** — `oferta/informe-muestra.md` (draw.io Desktop 32.4.1). **Cero cifras inventadas.**
> Plantilla: PLAN.md §10.5 (hook → objetivo → proceso → hallazgo → límites → CTA)
> Tema: §4.3 #1 (miedo→click) + #3 (prueba). Estilo §4.2 A+C (investigación + typewriter).
> Motor: SPEC-MOTOR-VIDEO.md v1.1. **Este vídeo NO se publica** — es para aprobación del operador.

---

## Línea temporal (voz ES · ~58 s)

| T | Bloque | Voz (ES) | Subs (EN) | Visual (clip AI + tipografía) |
|---|---|---|---|---|
| **0-4s** | **HOOK** | "Desarmé draw.io con IA gratis. Encontré 35 puertas traseras entre procesos." | *"I took draw.io apart with free AI. I found 35 back-doors between processes."* | Clip A (cyber B-roll) + tipografía kinetic: **35 puertas IPC** |
| **4-12s** | **OBJETIVO** | "draw.io Desktop 32.4.1. Lo descargué, verifiqué su hash contra el oficial, y lo audité en la nube sin gastar un euro." | *"draw.io Desktop 32.4.1. I downloaded it, verified its hash, and audited it in the cloud for zero euros."* | Clip B (server room) + tipografía typewriter: hash `f4455b3b…` ✅ |
| **12-30s** | **PROCESO** | "Recorrí 1.292 ficheros y 34 megas de código. 3.267.398 nodos de código. 3.246 hallazgos. Cero errores de parseo. Todo con huella criptográfica." | *"I went through 1,292 files and 34 MB of code. 3,267,398 AST nodes. 3,246 findings. Zero parse errors. Every result cryptographically stamped."* | Clip C (chip macro) + contador kinetic: 1.292 → 3.267.398 → 3.246 |
| **30-44s** | **HALLAZGO** | "28 canales de comunicación entre procesos. 5 ventanas. La buena noticia: 5 vulnerabilidades cruzadas, 0 activas. La higiene es buena." | *"28 IPC channels. 5 windows. Good news: 5 cross-checked CVEs, 0 active. The hygiene is good."* | Clip D (data nodes) + tipografía: **28 canales · 5 CVEs → 0 activos** |
| **44-53s** | **LÍMITES** | "Y esto es lo que no verás en otros informes: REA declara qué NO pudo saber. 7 límites, con su evidencia." | *"And this is what you won't see in other reports: REA declares what it could NOT determine. 7 limitations, each with its evidence."* | Clip E (hologram doc) + tipografía: **7 límites declarados** + `limitations` |
| **53-58s** | **CTA** | "¿Software de escritorio? Te audito el tuyo con la misma evidencia. Link en la bio." | *"Desktop software? I'll audit yours with the same evidence. Link in bio."* | End-card estático: logo + "AUDITORÍA CON EVIDENCIA" + flecha ↗ |

---

## Elementos no-narrados (pantalla)

- **`evidence_id`** visible al menos 1 vez: `ev_f0e4202c…` (diferenciador §10.5).
- **Zona segura**: texto dentro del 85% central (spec §4.3). Nada en los 150px superiores/inferiores.
- **Subs EN**: karaoke palabra-a-palabra (ASS, `\\k`), dentro de zona segura, sin tapar tipografía principal.

---

## Prompts de clips AI (semillas fijas · estética cyber/código · SIN texto en encuadre)

> Regla §4.2: **NO** stock genérico de Pexels. Semillas fijas para reproducibilidad (spec §4.3).

| Clip | Secuencia | Prompt (EN, para Wan) | Seed | Dur |
|---|---|---|---|---|
| **A** | HOOK | `dark abstract cybersecurity visual, glowing teal and magenta circuit pathways converging, floating hexagonal nodes, volumetric fog, cinematic rim light, ultra detailed, moody, no text, no letters` | 42 | 4s |
| **B** | OBJETIVO | `vast dark server room, rows of racks with tiny blue and magenta LEDs, slow dolly forward, atmospheric haze, cold cinematic lighting, high detail, no text, no letters` | 1337 | 8s |
| **C** | PROCESO | `extreme macro of a silicon microchip, teal and magenta light tracing the die pathways, shallow depth of field, bokeh, cinematic, hyperdetailed, no text, no letters` | 777 | 18s |
| **D** | HALLAZGO | `abstract network of glowing nodes connected by arcing teal lines on a dark void, data flowing as light pulses, slow rotation, cinematic, no text, no letters` | 2024 | 14s |
| **E** | LÍMITES | `a translucent holographic document floating in dark space, scanning laser line sweeping across it, magenta and teal edge glow, cinematic, mysterious, no text, no letters` | 9001 | 9s |

> **Nota**: los clips se generan en **480p** (Wan-5B en A10) y se **upscalean a 1080×1920** en el ensamblado (spec §4.3, ahorra GPU). La duración de cada clip se estira/recorta con `tpad`+`trim` en ffmpeg para cuadrar la línea temporal; las cifras reales de fps/coste se miden en el smoke test (§8).

---

## Voz (TTS)

- **Idioma**: ES. Voces candidatas: **edge-tts `es-ES-ElviraNeural`** (ya integrada, gratis) vs **Chatterbox** (MIT, GPU). → decisión en smoke test §8 con $ reales.
- **Velocidad**: 1.0× (natural). Si no cabe en 58 s, subir a 1.05× (nunca >1.1× — suena a robot).
- **Música**: ACE-Step, lecho cyber bajo (−22 LUFS bajo la voz), o silencio si ACE-Step no convence. → smoke test.

---

## Estado de aprobación

- [ ] Guion aprobado por el operador (bloqueante antes de gastar GPU — spec R5)
- [ ] Modelo y voz elegidos (smoke test §8)
- [ ] Muestra renderizada y aprobada → se congela el "look" en la spec
