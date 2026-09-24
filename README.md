# Otra lectura

Archivo estático de las ediciones del radar de noticias. El contenido vive en
`ediciones/*.md`; `site/` es HTML generado a partir de ahí y no se edita a mano.

Requisitos: `bash`, `git` y `python3` (3.9 o más). El único conversor de
markdown es Python-Markdown, con la versión fijada en `requirements.txt`.
`build.sh` lo instala en `.venv/` la primera vez.

## Agregar una edición

El formato editorial está en `prompt.md` y el técnico en `ESPECIFICACION.md`.

1. Crea `ediciones/AAAA-MM-DD-radar.md`. Si hay dos el mismo día, usa los
   sufijos `-01` y `-02`. El frontmatter va así:

   ```yaml
   ---
   fecha: 2026-09-23
   edicion: 3
   titulo: "..."
   temas: [fiscal-subsidios, clima-adaptacion]
   categorias: [economia, ambiente]
   lugares: [Colombia, Bangladés]
   cruce_mattriz: []
   seguimiento: [chaparral]
   nota: "opcional, se muestra bajo el título"
   ---
   ```

   `categorias` agrupa las ediciones en páginas navegables. Las claves
   válidas están en `CATEGORIAS` (`scripts/build.py`) y en `RUTINA.md`;
   `temas` es libre y más específico.

2. En el cuerpo, la plantilla reconoce estas marcas:

   | Markdown | Se muestra como |
   |---|---|
   | `# Radar · 23 de septiembre de 2026` | se omite (la cabecera sale del frontmatter) |
   | `## Carril 1: Radar`, `## Carril 2: Asombro`, `## Glosario` | divisor de carril |
   | `### 1. Nombre de la fricción` | título de fricción |
   | `### Seguimiento: tema` | nota corta de seguimiento |
   | `**Qué pasó.** texto` | subtítulo de la fricción |
   | `**Contrapeso.**` o `**Resultados y contrapeso.**` | tarjeta con doble borde |
   | `**Qué dice la historia.** *(Conocimiento general.)* …` | sello rojo y fondo rayado (todo el párrafo) |
   | `… *(Conocimiento general:* texto *)*` a mitad de párrafo | solo ese tramo resaltado |
   | `**Sin salida conocida.**` | etiqueta en rojo |
   | `**Conflicto de interés declarado:**` | nota enmarcada |

   Una etiqueta es una negrita al inicio del párrafo que termina en punto o
   dos puntos. En el carril de Asombro esa negrita se muestra como título
   corrido.

3. Revisa el resultado con `./build.sh` y abre `site/index.html`.

## Desplegar

```sh
./deploy.sh "Edición del 23 de septiembre"   # el mensaje es opcional
```

El script hace build, commit (de `ediciones/` y `site/`) y push. Cloudflare
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

- corrección de contenido → se aplica a la edición indicada;
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
Settings → Variables and Secrets (tipo Secret):

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
scripts/build.py    frontmatter + markdown → HTML
build.sh            prepara .venv y ejecuta el build
deploy.sh           build + commit + push
site/               salida generada (se publica tal cual)
wrangler.jsonc      Cloudflare Workers: site/ como estáticos y /api/* al Worker
src/worker.js       recibe el formulario de ajustes y crea el issue en GitHub
AJUSTES.md          reglas de estilo acumuladas a partir de los ajustes
```
