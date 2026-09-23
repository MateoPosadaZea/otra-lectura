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
   lugares: [Colombia, Bangladés]
   cruce_mattriz: []
   seguimiento: [chaparral]
   nota: "opcional, se muestra bajo el título"
   ---
   ```

2. En el cuerpo, la plantilla reconoce estas marcas:

   | Markdown | Se muestra como |
   |---|---|
   | `# Radar · 23 de septiembre de 2026` | se omite (la cabecera sale del frontmatter) |
   | `## Carril 1: Radar`, `## Carril 2: Asombro`, `## Glosario` | divisor de carril |
   | `### 1. Nombre de la fricción` | título de fricción |
   | `### Seguimiento: tema` | nota corta de seguimiento |
   | `**Qué pasó.** texto` | subtítulo de la fricción |
   | `**Contrapeso.**` o `**Resultados y contrapeso.**` | recuadro azul |
   | `**Qué dice la historia.** *(Conocimiento general.)* …` | recuadro ámbar punteado (todo el párrafo) |
   | `… *(Conocimiento general:* texto *)*` a mitad de párrafo | solo ese tramo resaltado |
   | `**Sin salida conocida.**` | etiqueta roja |
   | `**Conflicto de interés declarado:**` | nota enmarcada |

   Una etiqueta es una negrita al inicio del párrafo que termina en punto o
   dos puntos. En el carril de Asombro esa negrita se muestra como título
   corrido.

3. Revisa el resultado con `./build.sh` y abre `site/index.html`.

## Desplegar

```sh
./deploy.sh "Edición del 23 de septiembre"   # el mensaje es opcional
```

El script hace build, commit (de `ediciones/` y `site/`) y push. Al llegar el
push a `main`, GitHub Actions (`.github/workflows/pages.yml`) publica `site/`
en GitHub Pages sin volver a construir. Como `site/` está en el repo, cualquier
hosting estático puede servirlo sin paso de build (por ejemplo, Cloudflare
Pages con directorio de salida `site` y sin comando de build).

## Estructura

```
ediciones/          fuente: una edición por archivo .md
prompt.md           formato editorial del radar
ESPECIFICACION.md   especificación técnica
plantilla/          base.html y estilo.css
scripts/build.py    frontmatter + markdown → HTML
build.sh            prepara .venv y ejecuta el build
deploy.sh           build + commit + push
site/               salida generada (se publica tal cual)
```
