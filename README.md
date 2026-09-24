# Otra lectura

Archivo estático de las ediciones del radar de noticias. El contenido vive en
`ediciones/*.md`; `site/` es HTML generado a partir de ahí y no se edita a mano.

Requisitos: `bash`, `git` y `python3` (3.9 o más). El único conversor de
markdown es Python-Markdown, con la versión fijada en `requirements.txt`.
`build.sh` lo instala en `.venv/` la primera vez.

## Agregar una edición

El formato editorial está en `prompt.md` y el técnico en `ESPECIFICACION.md`.

1. Crea `ediciones/AAAA-MM-DD-radar.md`. Si hay dos el mismo día, usa los
   sufijos `-01` y `-02`. El frontmatter:

   ```yaml
   ---
   fecha: 2026-09-24                 # obligatorio, AAAA-MM-DD
   edicion: 4                        # obligatorio, entero
   titulo: "..."                     # obligatorio
   temas: [calor-salud, presupuesto-2027]
   categorias: [salud, economia]     # claves de CATEGORIAS (scripts/build.py)
   lugares: [Colombia, India]
   cruce_mattriz: [alerta de calor legible]
   seguimiento: [presupuesto-2027]   # temas de ediciones anteriores
   nota: "opcional, se muestra bajo el título"
   fuentes:
     - medio: "CEPAL"
       titulo: "Panorama Fiscal 2026"
       url: "https://..."            # obligatoria
   actualizaciones:                  # se agregan después de publicar
     - fecha: 2026-10-02
       friccion: "presupuesto-2027"  # opcional: slug de la fricción
       texto: "El Congreso aprobó el presupuesto el 1 de octubre..."
   correcciones:                     # se agregan después de publicar
     - fecha: 2026-09-30
       texto: "Se corrigió la cifra de ... : la fuente reporta ..."
   ---
   ```

   - `temas` es libre y específico; `categorias` agrupa el archivo en
     páginas navegables.
   - `seguimiento` se muestra como enlaces a las ediciones anteriores que
     tienen ese slug en `temas`.
   - `fuentes` sale como lista numerada al cierre (antes del glosario).
   - `actualizaciones` con `friccion` aparece al pie de esa fricción; sin
     `friccion`, al final de la edición. `correcciones` va siempre al final.
     **El texto original nunca se edita: la corrección se agrega.** El
     índice y la cabecera marcan las ediciones revisadas con la fecha del
     cambio más reciente.
   - Textos largos entre comillas pueden seguir en la línea siguiente,
     con más sangría.

2. En el cuerpo, la plantilla reconoce estas marcas:

   | Markdown | Se muestra como |
   |---|---|
   | `# Radar · 24 de septiembre de 2026` | se omite (la cabecera sale del frontmatter) |
   | `## Carril 1: Radar`, `## Carril 2: Asombro`, `## Descartes`, `## Glosario` | divisor de carril |
   | `### 1. Nombre de la fricción {#slug}` | fricción; `{#slug}` es opcional y es lo que usa `actualizaciones.friccion` (sin él, el slug sale del título) |
   | `### Seguimiento: tema` | nota corta de seguimiento |
   | `**Qué ocurrió.** texto` | subtítulo de la fricción |
   | `**Contrapeso.**` | tarjeta con doble borde |
   | `**Antecedente histórico.** *(Conocimiento general.)* …` | sello rojo y fondo rayado (todo el párrafo) |
   | `… *(Conocimiento general:* texto *)*` a mitad de párrafo | solo ese tramo resaltado |
   | `**Sin salida conocida.**` | etiqueta en rojo |
   | `**Conflicto de interés declarado:**` | nota enmarcada |
   | `## Glosario` con `- **Término:** definición` | además, glosario flotante a la derecha (en móvil, botón "Glosario") |

   Una etiqueta es una negrita al inicio del párrafo que termina en punto o
   dos puntos. En el carril de Asombro esa negrita se muestra como título
   corrido.

3. Revisa el resultado con `./build.sh` y abre `site/index.html`.

## Verificación

`./build.sh` se detiene, sin publicar nada, y dice archivo, campo y motivo si:

- el frontmatter es inválido: falta `fecha`, `edicion` o `titulo`, una
  fecha no existe, hay un campo desconocido, una categoría no existe, o la
  sintaxis está mal (comillas sin cerrar, sangría inesperada);
- una fuente no tiene `url` (o no es http/https);
- un slug de `seguimiento` no aparece en `temas` de ninguna edición
  anterior;
- una actualización apunta a una fricción que no existe en esa edición;
- `candidatas.md` tiene un estado inválido.

## Candidatas

`site/candidatas.html` reúne las ideas del campo `cruce_mattriz` de todas
las ediciones, con la edición de origen, la fecha y el estado. El estado se
lleva a mano en `candidatas.md` (tabla `| Candidata | Estado |`): `pendiente`,
`evaluada`, `descartada` o `activa`. Si una candidata no está en la tabla,
se muestra como `pendiente`. La página se enlaza desde el pie del sitio.

## Indexación

Mientras el proyecto está en calibración, el sitio pide no ser indexado:
`site/robots.txt` con `Disallow: /` y `<meta name="robots" content="noindex,
nofollow">` en todas las páginas. Ambos salen de una sola constante: para
abrirlo a buscadores, cambia `INDEXAR = False` a `True` en
`scripts/build.py` y publica.

## Desplegar

```sh
./deploy.sh "Edición del 23 de septiembre"   # el mensaje es opcional
```

El script hace build, commit (de `ediciones/`, `site/`, `candidatas.md` y
`AJUSTES.md`) y push. Si la verificación falla, no publica nada. Cloudflare
Workers detecta el push y ejecuta `npx wrangler deploy`, que publica `site/`
tal cual según `wrangler.jsonc`. No hay build en Cloudflare: el HTML ya viene
generado.

El sitio es público. Si algún día se quiere privado, se pone Cloudflare
Access delante del Worker; no hay que tocar el código.

## Ajustes

Cada página tiene al final "Sugerir un ajuste". El formulario lo recibe el
Worker (`src/worker.js`), que valida la clave familiar y lo guarda como
issue `[Ajuste] …` en GitHub. Cada hora, de 6 a. m. a 10 p. m. (Colombia),
Claude revisa esos issues:

- corrección de contenido → se agrega en `correcciones` de la edición
  (el texto original no se edita);
- regla de estilo o tono → se agrega a `AJUSTES.md` y rige desde la
  edición siguiente;
- cambio de diseño o funciones del sitio → se implementa en la plantilla,
  el CSS o el build, se prueba y se publica, siempre que sea acotado y
  respete los principios (costo cero, sin frameworks, contenido en
  markdown).

Los cambios grandes o riesgosos (secretos, despliegue, rutinas, borrar
contenido, servicios externos) no se aplican solos: quedan abiertos con
una propuesta para que Mateo decida. Tras cada ajuste aplicado, Claude
comenta en el issue qué cambió y lo cierra.

Configuración, una sola vez, en Cloudflare → Worker `otra-lectura` →
Settings → Runtime variables and secrets (tipo Secret; no en la sección
Build, que solo existe durante el build):

- `GITHUB_TOKEN`: token fine-grained de GitHub, solo para este repo, con
  permiso *Issues: Read and write*.
- `CLAVE_FAMILIA`: la clave que se escribe en el formulario.

## Estructura

```
ediciones/          fuente: una edición por archivo .md
prompt.md           formato editorial del radar
RUTINA.md           instrucciones de la edición diaria automática (5:00 a. m. Colombia)
ESPECIFICACION.md   especificación técnica
plantilla/          base.html, estilo.css y fuentes/ (Instrument Serif, UnifrakturMaguntia y Manrope, OFL)
scripts/build.py    markdown → HTML, verificación, candidatas
scripts/frontmatter.py  lector del frontmatter (subconjunto de YAML, sin dependencias)
candidatas.md       estado de las candidatas (editable a mano)
build.sh            prepara .venv y ejecuta el build
deploy.sh           build + commit + push
site/               salida generada (se publica tal cual)
wrangler.jsonc      Cloudflare Workers: site/ como estáticos y /api/* al Worker
src/worker.js       recibe el formulario de ajustes y crea el issue en GitHub
AJUSTES.md          reglas de estilo acumuladas a partir de los ajustes
```
