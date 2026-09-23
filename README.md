# Otra lectura

Archivo estático de las ediciones del radar de noticias. El contenido vive en
`ediciones/*.md`; `site/` es HTML generado a partir de ahí y no se edita a mano.

Requisitos: `bash`, `git` y `python3` (3.9 o más). El único conversor de
markdown es Python-Markdown, con la versión fijada en `requirements.txt`.
`build.sh` lo instala en `.venv/` la primera vez.

## Agregar una edición

1. Crea `ediciones/AAAA-MM-DD-nombre.md` con frontmatter:

   ```markdown
   ---
   titulo: Radar del 23 de septiembre
   fecha: 2026-09-23
   temas: [energía, agua]
   ---

   ## Fricción 1: …

   ### Qué pasó
   ### Quién lo está resolviendo
   ### Contrapeso
   ### Qué dice la historia (conocimiento general, no verificado)
   ### Cruce con Mattriz
   ```

   - `slug` es opcional: por defecto se usa el nombre del archivo.
   - Si falta `fecha`, se toma del nombre del archivo.
   - Si falta `titulo`, se usa el primer `# Título` del cuerpo.
   - `temas` acepta `[a, b]`, una lista con `- a` o `a, b`.

2. `##` es el título de cada fricción y `###` sus subtítulos.
   - Un subtítulo que diga "Contrapeso" se muestra como bloque azul.
   - Uno que diga "no verificado" se muestra como bloque ámbar punteado.
   - Un párrafo suelto que empiece con **Contrapeso:** o que contenga "no
     verificado" recibe el mismo trato.
   - Para marcar un bloque a mano, usa
     `<div class="contrapeso" markdown="1">…</div>`.

3. Revisa el resultado con `./build.sh` y abre `site/index.html`.

## Desplegar

```sh
./deploy.sh "Edición del 23 de septiembre"   # el mensaje es opcional
```

El script hace build, commit (de `ediciones/` y `site/`) y push. Al llegar el
push a `main`, GitHub Actions (`.github/workflows/pages.yml`) publica `site/`
en GitHub Pages sin volver a construir.

## Estructura

```
ediciones/          fuente: una edición por archivo .md
plantilla/          base.html y estilo.css
scripts/build.py    frontmatter + markdown → HTML
build.sh            prepara .venv y ejecuta el build
deploy.sh           build + commit + push
site/               salida generada (se publica tal cual)
```
