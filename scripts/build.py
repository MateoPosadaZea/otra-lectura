#!/usr/bin/env python3
"""Genera site/ a partir de ediciones/*.md.

El markdown es la fuente; todo lo que hay en site/ es salida y se puede
borrar y regenerar. Única dependencia externa: Python-Markdown (ver
requirements.txt).
"""

import html
import re
import shutil
import sys
from datetime import date
from pathlib import Path
from string import Template

import markdown

RAIZ = Path(__file__).resolve().parent.parent
EDICIONES = RAIZ / "ediciones"
PLANTILLA = RAIZ / "plantilla"
SITE = RAIZ / "site"

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

# Texto que marca un bloque como contrapeso o como no verificado.
RE_CONTRAPESO = re.compile(r"contrapeso", re.I)
RE_NO_VERIFICADO = re.compile(r"no\s+verificad[oa]s?", re.I)
RE_FRICCION = re.compile(r"fricci[oó]n", re.I)


# --- Frontmatter -----------------------------------------------------------

def _valor(crudo):
    crudo = crudo.strip()
    if crudo.startswith("[") and crudo.endswith("]"):
        return [_valor(x) for x in crudo[1:-1].split(",") if x.strip()]
    if len(crudo) >= 2 and crudo[0] == crudo[-1] and crudo[0] in "\"'":
        return crudo[1:-1]
    return crudo


def parsear_frontmatter(texto):
    """Subconjunto de YAML: `clave: valor`, listas `[a, b]` y listas con `- item`."""
    if not texto.startswith("---"):
        return {}, texto
    lineas = texto.split("\n")
    try:
        fin = next(i for i, l in enumerate(lineas[1:], 1) if l.strip() in ("---", "..."))
    except StopIteration:
        return {}, texto
    meta, clave = {}, None
    for linea in lineas[1:fin]:
        if not linea.strip() or linea.lstrip().startswith("#"):
            continue
        m = re.match(r"^\s+-\s+(.*)$", linea)
        if m and clave:
            if not isinstance(meta.get(clave), list):
                meta[clave] = []
            meta[clave].append(_valor(m.group(1)))
            continue
        m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", linea)
        if m:
            clave = m.group(1).lower()
            meta[clave] = _valor(m.group(2)) if m.group(2).strip() else []
    return meta, "\n".join(lineas[fin + 1:])


def primero(meta, *claves, defecto=None):
    for c in claves:
        if meta.get(c) not in (None, "", []):
            return meta[c]
    return defecto


def como_lista(v):
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x) for x in v if str(x).strip()]
    return [x.strip() for x in str(v).split(",") if x.strip()]


def fecha_legible(iso):
    try:
        d = date.fromisoformat(iso)
    except ValueError:
        return iso
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


# --- Marcado de bloques ------------------------------------------------------

RE_HEADING = re.compile(r"<h([1-6])([^>]*)>(.*?)</h\1>", re.S)


def texto_plano(fragmento):
    return html.unescape(re.sub(r"<[^>]+>", "", fragmento))


def envolver_secciones(cuerpo):
    """Envuelve cada sección de título en <section> con clases según su tema.

    Una sección va desde su título hasta el siguiente título de nivel igual
    o superior. Las secciones de contrapeso o "no verificado" reciben una
    clase propia para distinguirlas del cuerpo.
    """
    salida, pila, pos = [], [], 0
    for m in RE_HEADING.finditer(cuerpo):
        nivel, texto = int(m.group(1)), texto_plano(m.group(3))
        salida.append(cuerpo[pos:m.start()])
        while pila and pila[-1] >= nivel:
            salida.append("</section>\n")
            pila.pop()
        clases = []
        if nivel == 2:
            clases.append("seccion")
            if RE_FRICCION.search(texto):
                clases.append("friccion")
        if nivel >= 3:
            clases.append("apartado")
        if RE_CONTRAPESO.search(texto):
            clases.append("contrapeso")
        if RE_NO_VERIFICADO.search(texto):
            clases.append("no-verificado")
        if clases:
            salida.append(f'<section class="{" ".join(clases)}">\n')
            pila.append(nivel)
        salida.append(m.group(0))
        pos = m.end()
    salida.append(cuerpo[pos:])
    salida.extend("</section>\n" for _ in pila)
    return "".join(salida)


def _anadir_clase(etiqueta_apertura, clase):
    if 'class="' in etiqueta_apertura:
        return etiqueta_apertura.replace('class="', f'class="{clase} ', 1)
    return etiqueta_apertura[:-1] + f' class="{clase}">'


def marcar_parrafos(cuerpo):
    """Marca párrafos, ítems de lista sin sublistas y citas sueltas."""
    def marcar(m):
        apertura, interior = m.group(1), m.group(2)
        if "<li" in interior or "<blockquote" in interior:
            return m.group(0)
        plano = texto_plano(interior)
        if RE_NO_VERIFICADO.search(plano):
            apertura = _anadir_clase(apertura, "no-verificado")
        elif RE_CONTRAPESO.match(plano.strip()):
            # Párrafo que empieza con "Contrapeso:" (estilo etiqueta en negrita).
            apertura = _anadir_clase(apertura, "contrapeso")
        return apertura + interior + m.group(3)

    for tag in ("p", "li", "blockquote"):
        cuerpo = re.sub(rf"(<{tag}(?:\s[^>]*)?>)(.*?)(</{tag}>)", marcar, cuerpo, flags=re.S)
    return cuerpo


# --- Build -------------------------------------------------------------------

def convertir(md_texto):
    return markdown.markdown(
        md_texto,
        extensions=["extra", "sane_lists"],
        output_format="html",
    )


def leer_edicion(ruta):
    meta, cuerpo_md = parsear_frontmatter(ruta.read_text(encoding="utf-8"))
    cuerpo = convertir(cuerpo_md).strip()

    # Si el cuerpo abre con un <h1>, lo usamos como título en vez de repetirlo.
    titulo = primero(meta, "titulo", "título", "title")
    m = re.match(r"<h1[^>]*>(.*?)</h1>\s*", cuerpo, re.S)
    if m:
        titulo = titulo or texto_plano(m.group(1))
        cuerpo = cuerpo[m.end():]

    m_fecha = re.match(r"(\d{4}-\d{2}-\d{2})", ruta.stem)
    fecha = str(primero(meta, "fecha", "date", defecto=m_fecha.group(1) if m_fecha else ""))

    return {
        "slug": str(primero(meta, "slug", defecto=ruta.stem)),
        "titulo": str(titulo or ruta.stem),
        "fecha": fecha,
        "temas": como_lista(primero(meta, "temas", "tags", "etiquetas")),
        "resumen": str(primero(meta, "resumen", "descripcion", "descripción", "description", defecto="")),
        "cuerpo": marcar_parrafos(envolver_secciones(cuerpo)),
        "origen": ruta.name,
    }


def html_temas(temas):
    if not temas:
        return ""
    items = "".join(f"<li>{html.escape(t)}</li>" for t in temas)
    return f'<ul class="temas" aria-label="Temas">{items}</ul>'


def main():
    base = Template((PLANTILLA / "base.html").read_text(encoding="utf-8"))
    ediciones = [leer_edicion(p) for p in sorted(EDICIONES.glob("*.md"))]

    slugs = [e["slug"] for e in ediciones]
    repetidos = {s for s in slugs if slugs.count(s) > 1}
    if repetidos:
        sys.exit(f"error: slugs repetidos: {', '.join(sorted(repetidos))}")

    # Cronológico inverso; a igual fecha, el slug mayor primero (radar-02 antes que radar-01).
    ediciones.sort(key=lambda e: (e["fecha"], e["slug"]), reverse=True)

    # site/ es salida: se regenera entero.
    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "ediciones").mkdir(parents=True)
    shutil.copy(PLANTILLA / "estilo.css", SITE / "estilo.css")

    for i, e in enumerate(ediciones):
        nav = []
        if i + 1 < len(ediciones):
            ant = ediciones[i + 1]
            nav.append(f'<a rel="prev" href="{ant["slug"]}.html">← {html.escape(ant["titulo"])}</a>')
        if i > 0:
            sig = ediciones[i - 1]
            nav.append(f'<a rel="next" href="{sig["slug"]}.html">{html.escape(sig["titulo"])} →</a>')
        contenido = f"""<article class="edicion">
<header class="cabecera">
<p class="fecha"><time datetime="{html.escape(e['fecha'])}">{fecha_legible(e['fecha'])}</time></p>
<h1>{html.escape(e['titulo'])}</h1>
{html_temas(e['temas'])}
</header>
{e['cuerpo']}
</article>
<nav class="entre-ediciones" aria-label="Otras ediciones">{''.join(nav)}</nav>"""
        pagina = base.substitute(
            titulo=html.escape(f"{e['titulo']} · Otra lectura"),
            descripcion=html.escape(e["resumen"] or e["titulo"]),
            raiz="../",
            contenido=contenido,
        )
        (SITE / "ediciones" / f"{e['slug']}.html").write_text(pagina, encoding="utf-8")

    filas = []
    for e in ediciones:
        filas.append(f"""<li>
<time datetime="{html.escape(e['fecha'])}">{fecha_legible(e['fecha'])}</time>
<a href="ediciones/{e['slug']}.html">{html.escape(e['titulo'])}</a>
{html_temas(e['temas'])}
</li>""")
    lista = "\n".join(filas) if filas else "<li>Todavía no hay ediciones.</li>"
    indice = base.substitute(
        titulo="Otra lectura",
        descripcion="Archivo de ediciones del radar de noticias.",
        raiz="",
        contenido=f"""<header class="cabecera">
<h1>Otra lectura</h1>
<p class="bajada">Archivo de ediciones del radar.</p>
</header>
<ol class="indice" reversed>
{lista}
</ol>""",
    )
    (SITE / "index.html").write_text(indice, encoding="utf-8")
    print(f"{len(ediciones)} ediciones → {SITE.relative_to(RAIZ)}/")


if __name__ == "__main__":
    main()
