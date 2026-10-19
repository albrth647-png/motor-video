# GUION — Vídeo #1 «Desarmé draw.io con IA gratis»

> **Short vertical 1080×1920 · 30 fps · 49,068 s · faceless · voz ES + subs EN karaoke** · la imagen manda.
> Fuente de datos: **real** — `oferta/informe-muestra.md` (draw.io Desktop 32.4.1). **Cero cifras inventadas.**
> Plantilla: PLAN.md §10.5 (hook → objetivo → proceso → hallazgo → límites → CTA) — adaptada a la narrativa de **8 frases** del corte final.
> **Estado: CONGELADO v8** — veredicto del operador (2026-10-19): «v8 perfecta» = **100 %** → receta congelada en `SPEC-MOTOR-VIDEO.md` **v1.2** (D-VM-09; **v1.3** = backend real, sin GPU).
> Fuente de verdad técnica: `build_nb.py` (genera `kernel.ipynb` / `render.ipynb`). Bitácora: `ITERACIONES.md`.

---

## Línea temporal — 8 frases (voz real: 47,57 s · total con cola: 49,068 s)

| Frase | t (s) | Voz (ES · Tomás −12 %) | Subs (EN karaoke) | Visual (`shotNN`) |
|---|---|---|---|---|
| F0 | 0,10 – 4,91 | REA expert services. Auditoria real, con evidencia. | REA expert services. A real audit, with evidence. | `shot19` + **tarjeta intro** (ASS) |
| F1 | 5,98 – 8,91 | Descubri una falla de seguridad en draw.io. | I found a security flaw in draw.io | `shot01` candado roto · `shot12` grieta |
| F2 | 9,99 – 14,56 | Y lo peor es que afecta a la version 32.4.1, la actual. | And the worst part it affects version 32.4.1 the current one | `shot02` laptop roja · `shot13` versiones |
| F3 | 15,60 – 20,36 | En mi auditoria encontre que el modo de incognito no aisla las sesiones como deberia. | In my audit I found incognito mode doesn't isolate sessions like it should | `shot14` lupa · `shot03` escudo · `shot04` máscara · `shot05` ventanas |
| F4 | 21,41 – 26,69 | Un atacante podria rastrear los diagramas que abres incluso cuando crees que estas protegido. | An attacker could track the diagrams you open even when you think you're protected | `shot06` atacante · `shot15` rastro · `shot07` ojo |
| F5 | 27,74 – 28,76 | Pero hay solucion. | But there's a fix | `shot08` bóveda |
| F6 | 29,82 – 35,67 | Con tres ajustes de configuracion podes cerrar esa puerta y dejar tu draw.io realmente seguro. | Three config tweaks close that door and keep your draw.io truly secure | `shot09` 3 ajustes · `shot16` candado verde · `shot10` laptop · `shot17` cubo |
| F7 | 36,70 – 46,46 | En la parte dos te muestro los tres ajustes. ¿Tu app es Electron? Te la audito con esta misma evidencia. Link en la bio. | Part two shows the three tweaks. Building an Electron app? I'll audit yours with this same evidence. Link in bio. | `shot18` play · `shot11` fondo CTA · `shot20` **endcard** |

- La pausa entre frases la sostiene el último plano de la frase anterior; la imagen nueva entra EXACTAMENTE con la primera palabra de su frase (sincronía imagen↔voz).
- **TOTAL = 49,068 s** = voz 47,57 s + cola (**TAIL**) 1,5 s para que respire la música y funda el cierre.

---

## Tarjetas (tipografía real ASS — D-VM-04)

- **Intro** (sobre `shot19`, ~0,25–5,21 s): `REA EXPERT SERVICES` · subrayado turquesa · `AUDITORÍA REAL` · `draw.io Desktop 32.4.1` · `con evidencia verificable`.
- **Endcard** (sobre `shot20`, desde ~42,6 s): `REA EXPERT SERVICES` · `¿TU APP ES ELECTRON?` · `Informe en 48 h · evidencia verificable` · `PARTE 2 · los 3 ajustes` · placa `LINK EN LA BIO` (crece al decir «Link») · fundido de vídeo final 0,7 s.

## Voz (TTS)
- **edge-tts** · `es-AR-TomasNeural` · **rate −12 %** · 97 palabras · 47,57 s. (La voz va embebida en el dataset `motor-media`; solo se regenera online.)
- Marcas de límite de frase (`LASTW`): evidencia · drawio · actual · deberia · protegido · solucion · seguro · bio.

## Música (v8 · procedural)
- Lecho **numpy en el runner** (seed fija) clavado a la narrativa (intro → tensión → solución → cierre + whooshes) · **sidechain ducking** bajo la voz · fade-out 1,2 s · mezcla final **−14,8 LUFS** (TP −1,4).
- Nube: la pieza prevista es ACE-Step (SPEC D-VM-05); si el procedural se mantiene, se registra como cambio de receta.

## Subs EN karaoke
- Poppins Bold 74 · borde negro 5 · `marginV 300` · palabra clave en color del tramo · tiempos reales de `words.json`.

## QA (bloqueante)
- 1080×1920 · 30 fps · dur == TOTAL ±0,5 · h264+aac 192k · faststart · **LUFS ∈ [−16,−13]** (medido −14,8 · TP −1,4) · revisión de fotogramas antes de entregar.

## Entrega y aprobación
- **Entregado**: `/sdcard/Download/video-01-v8.mp4` · 14.811.679 B · md5 `af45df6da8795c0f120c1646362f1055` · kernel v9 con `QA: PASS`.
- **Aprobado**: veredicto «perfecta» = **100 %** (2026-10-19) → look congelado (SPEC v1.2; v1.3 = backend CPU real, sin GPU ni tarjeta).
