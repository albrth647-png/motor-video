# GUION — Vídeo #1 «Desarmé draw.io con IA gratis» · **v10**

> **Estado:** v10 = **hook honesto** · pendiente de render + veredicto del operador.
> **Por qué cambia desde v9:** el v9 afirmaba una vulnerabilidad que **nuestro propio
> informe refuta** (decía *"Descubrí una falla de seguridad"* y *"el modo de incognito
> no aísla las sesiones"*; el informe dice **"🟢 Sin hallazgos críticos"**, **0 CVEs**,
> y de *"modo de incognito"* **no aparece ni una vez** en sus 388 líneas). El v9 queda
> **archivado, no publicado**. Ver `investigacion/INFORME-REDES-2026.md` §6.
> **El look no cambia** (SPEC v1.4): mismo diseño, tipografía, colores, tiempos y mezcla.
>
> **Short vertical 1080×1920 · 30 fps · ≈48 s · faceless · voz ES + subs EN karaoke** · la imagen manda.
> Fuente de datos: **real** — `oferta/informe-muestra.md` (draw.io Desktop 32.4.1). **Cero cifras inventadas.**

---

## Regla que gobierna este guion

> **Cada frase tiene que poder rastrearse a una línea del informe.**
> Si el dato no está en `oferta/informe-muestra.md`, **no se dice en el vídeo**.

| ❌ Prohibido (v9) | ✅ v10 |
|---|---|
| "Descubrí una falla de seguridad en draw.io" | "Y **no encontramos ninguna vulnerabilidad**" |
| "el modo de incognito no aísla las sesiones" | ⚠️ **no se menciona**: la auditoría nunca lo examinó |
| "un atacante podría rastrear los diagramas" | "de cinco candidatas, **ninguna activa**" · "29 handlers, **solo dos** muestran validación" |

---

## Línea temporal — 8 frases (voz real de Tomás −12 %)

| Frase | Voz (ES) | Subs (EN karaoke) | Planos | `LASTW` |
|---|---|---|---|---|
| **F0** | Auditamos draw.io Desktop 32.4.1. Y no encontramos ninguna **vulnerabilidad**. | We audited draw.io Desktop 32.4.1. And found no vulnerability. | `shot19` (intro) · `shot14` (lupa) | `vulnerabilidad` |
| **F1** | Releimos 34 megabytes de JavaScript y mas de 3 millones de **nodos**. | We read 34 megabytes of JavaScript and over 3 million nodes. | `shot21` 🆕 grafo de nodos | `nodos` |
| **F2** | El inventario dio 82 paquetes. De cinco vulnerabilidades candidatas, ninguna **activa**. | The inventory gave 82 packages. Of five candidate vulnerabilities, none active. | `shot13` (versiones) · `shot23` 🆕 tarjetas de paquetes | `activa` |
| **F3** | Hay cinco ventanas. Una se construye con opciones dinamicas, y eso no se puede **verificar**. | There are five windows. One is built with dynamic options, and that can't be verified. | `shot22` 🆕 panel de código borroso | `verificar` |
| **F4** | Hay 29 handlers de IPC. Solo dos muestran validacion de **origen**. | There are 29 IPC handlers. Only two show sender validation. | `shot24` 🆕 red de nodos (2 vivos) | `origen` |
| **F5** | Pero lo importante es lo que no se pudo **saber**. | But what matters is what we couldn't know. | `shot25` 🆕 mar de puntos | `saber` |
| **F6** | 92.468 desconocidos registrados, cada uno con su ID. Y diez limites **declarados**. | 92,468 registered unknowns, each with its ID. And ten declared limits. | `shot26` 🆕 contadores · `shot16` (candado verde) · `shot17` (cubo) | `declarados` |
| **F7** | Si tu app es Electron y no sabes que lleva dentro, auditala. 48 horas, con **evidencia**. | If your app is Electron and you don't know what it ships, audit it. 48 hours, with evidence. | `shot20` (endcard) · `shot09` · `shot10` · `shot08` · `shot11` | `evidencia` |

- **16 planos** (10 reutilizados del dataset `motor-media` + 7 nuevos `shot21..shot27`).
- La pausa entre frases la sostiene el último plano de la frase anterior; la imagen nueva entra EXACTAMENTE con la primera palabra de su frase.
- **TOTAL ≈ 48 s** = voz (~46,5 s) + cola **TAIL** 1,5 s.
- Los marcadores `LASTW` son la **última palabra** de cada frase: el motor clava ahí los límites (`build_nb.py` → `LASTW` + `spans`).

### Imágenes retiradas del v9 (y por qué)

`shot01` candado roto · `shot02` laptop roja · `shot03` escudo agrietado · `shot04` máscara de incognito · `shot05` ventanas con fuga · `shot06` atacante · `shot07` ojo rastreador · `shot12` grieta · `shot15` rastro de luz · `shot18` play de luz.

> Representan **un ataque** o el *"modo de incognito"* que la auditoría **nunca examinó**.
> Con el guion honesto, esas imágenes **contradicen** lo que se dice. Se regeneran 7 nuevas
> (prompts en `video-01.json` → `images.prompts`; **sin texto en el encuadre**, D-VM-04).

---

## Tarjetas (tipografía real ASS — D-VM-04)

- **Intro** (sobre `shot19`): `AUDIT WITH PROOF` · subrayado turquesa · **`0 VULNERABILIDADES`** · `draw.io Desktop 32.4.1` · `y lo que no se pudo saber`
- **Endcard** (sobre `shot20`): `AUDIT WITH PROOF` · `¿TU APP ES ELECTRON?` · `Informe en 48 h · evidencia verificable` · `PARTE 2 · lo que no se pudo saber` · placa `LINK EN LA BIO` (crece al decir «Link») · fundido de vídeo final 0,7 s.

## Voz (TTS)
- **edge-tts** · `es-AR-TomasNeural` · **rate −12 %** · ~99 palabras (a medir en el render).
- La voz (`voz.mp3`) + `words.json` se **generan en CI** (edge-tts necesita internet y Kaggle no la tiene) y se suben al dataset `motor-media` → **0 MB en el móvil**.

## Música (v8 · procedural)
- Lecho **numpy en el runner** (seed fija) clavado a la narrativa · **sidechain ducking** bajo la voz · fade-out 1,2 s · mezcla final **−14 LUFS** (TP −1,4).
- Narrativa de color del v10: turquesa (marca) → **verde** (0 activos) → **naranja** (la ventana que no se puede verificar) → **índigo** (2 de 29) → **violeta** (lo desconocido) → turquesa (transparencia = CTA).

## Subs EN karaoke
- Poppins Bold 74 · borde negro 5 · `marginV 300` · palabra clave en color del tramo · tiempos reales de `words.json`.

## QA (bloqueante)
- 1080×1920 · 30 fps · dur == TOTAL ±0,5 · h264+aac 192k · faststart · **LUFS ∈ [−16,−13]** · revisión de fotogramas antes de entregar.

## Entrega y aprobación
- **Pendiente**: render en Kaggle (kernel v11) → QA-gate → **el operador lo ve y aprueba** → y solo entonces se publica.
- Mientras tanto: `status.publication.publishable = false` en `video-01.json`.
