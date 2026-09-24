#!/usr/bin/env python3
"""Genera site/ a partir de ediciones/*.md.

El markdown es la fuente; todo lo que hay en site/ es salida y se puede
borrar y regenerar. Única dependencia externa: Python-Markdown (ver
requirements.txt).

Convenciones de las ediciones (ver prompt.md):
  # Radar · fecha            → antetítulo
  ## Carril 1: Radar         → carril (divisor de sección)
  ### 1. Nombre de fricción  → fricción
  **Qué pasó.** texto        → subtítulo de la fricción (etiqueta en negrita)
  *(Conocimiento general…)*  → marca de "no verificado"
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

# Categorías amplias y fijas para navegar el archivo. Cada edición declara las
# suyas en el frontmatter (`categorias: [economia, salud]`). Para agregar una,
# se añade aquí y en RUTINA.md.
CATEGORIAS = {
    "economia": "Economía",
    "salud": "Salud",
    "ambiente": "Ambiente y clima",
    "energia": "Energía",
    "justicia": "Justicia y Estado",
    "territorio": "Ciudades y territorio",
    "sociedad": "Sociedad",
    "ciencia": "Ciencia y tecnología",
}

RE_NO_VERIFICADO = re.compile(r"conocimiento\s+general|no\s+verificad[oa]s?", re.I)

# Etiqueta en negrita → clase del párrafo que la lleva.
TIPOS_ETIQUETA = [
    (re.compile(r"contrapeso", re.I), "contrapeso"),
    (re.compile(r"sin salida conocida", re.I), "sin-salida"),
    (re.compile(r"conflicto de inter[eé]s", re.I), "conflicto"),
    (re.compile(r"cruce con mattriz", re.I), "cruce"),
]


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
        m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*?)(?:\s+#.*)?$", linea)
        if m:
            clave = m.group(1).lower()
            meta[clave] = _valor(m.group(2)) if m.group(2) else []
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


def clases_heading(nivel, texto):
    t = texto.lower()
    if nivel == 2:
        if "asombro" in t:
            return ["carril", "carril-asombro"]
        if "radar" in t or "carril" in t:
            return ["carril", "carril-radar"]
        return ["carril", "cierre"]
    if nivel == 3:
        clases = ["item"]
        if t.startswith("seguimiento"):
            clases.append("seguimiento")
        if "sin salida conocida" in t:
            clases.append("sin-salida")
        return clases
    return []


def envolver_secciones(cuerpo):
    """<h2> abre un carril (<section>) y <h3> una fricción (<article>).

    Cada bloque va hasta el siguiente título de nivel igual o superior.
    """
    salida, pila, pos = [], [], 0
    for m in RE_HEADING.finditer(cuerpo):
        nivel = int(m.group(1))
        salida.append(cuerpo[pos:m.start()])
        while pila and pila[-1][0] >= nivel:
            salida.append(f"</{pila.pop()[1]}>\n")
        clases = clases_heading(nivel, texto_plano(m.group(3)))
        if clases:
            tag = "section" if nivel == 2 else "article"
            salida.append(f'<{tag} class="{" ".join(clases)}">\n')
            pila.append((nivel, tag))
        salida.append(m.group(0))
        pos = m.end()
    salida.append(cuerpo[pos:])
    salida.extend(f"</{tag}>\n" for _, tag in reversed(pila))
    return "".join(salida)


def _marcar_em_nv(fragmento):
    """Marca las cursivas "(Conocimiento general…)" y el tramo que cubren."""
    # Tramo partido: *(Conocimiento general:* texto *)*
    fragmento = re.sub(
        r"<em>(\([^<)]*?conocimiento\s+general[^<)]*)</em>(.*?)<em>\)</em>",
        r'<span class="nv-tramo"><em class="marca-nv">\1</em>\2<em class="marca-nv">)</em></span>',
        fragmento, flags=re.I | re.S)
    # Marca completa: *(Conocimiento general, no verificado.)*
    return re.sub(
        r"<em>(\([^<]*?(?:conocimiento\s+general|no\s+verificad)[^<]*\))</em>",
        r'<em class="marca-nv">\1</em>',
        fragmento, flags=re.I)


def marcar_parrafo(m):
    apertura, interior, cierre = m.group(1), m.group(2), m.group(3)
    clases, etiqueta = [], ""

    e = re.match(r"\s*<strong>(.{1,80}?)</strong>\s*", interior, re.S)
    if e and texto_plano(e.group(1)).rstrip().endswith((".", ":")):
        clases.append("con-etiqueta")
        label = texto_plano(e.group(1))
        for patron, clase in TIPOS_ETIQUETA:
            if patron.search(label):
                clases.append(clase)
        etiqueta = f'<strong class="etiqueta">{e.group(1)}</strong> '
        interior = interior[e.end():]

    # Si la marca abre el párrafo (tras la etiqueta), todo el párrafo es no verificado.
    if re.match(r"\s*<em>\([^<]*?(?:conocimiento\s+general|no\s+verificad)", interior, re.I):
        clases.append("no-verificado")
    interior = _marcar_em_nv(interior)

    if clases:
        apertura = apertura[:-1] + f' class="{" ".join(clases)}">'
    return apertura + etiqueta + interior + cierre


def marcar_items(m):
    apertura, interior, cierre = m.group(1), m.group(2), m.group(3)
    if "<li" not in interior and RE_NO_VERIFICADO.search(texto_plano(interior)):
        interior = _marcar_em_nv(interior)
    return apertura + interior + cierre


def marcar_bloques(cuerpo):
    cuerpo = re.sub(r"(<p>)(.*?)(</p>)", marcar_parrafo, cuerpo, flags=re.S)
    return re.sub(r"(<li>)(.*?)(</li>)", marcar_items, cuerpo, flags=re.S)


# --- Build -------------------------------------------------------------------

def convertir(md_texto):
    return markdown.markdown(md_texto, extensions=["extra", "sane_lists"], output_format="html")


def leer_edicion(ruta):
    meta, cuerpo_md = parsear_frontmatter(ruta.read_text(encoding="utf-8"))
    cuerpo = convertir(cuerpo_md).strip()

    # El "# Radar · fecha" del cuerpo pasa a ser el antetítulo de la cabecera.
    antetitulo = ""
    m = re.match(r"<h1[^>]*>(.*?)</h1>\s*", cuerpo, re.S)
    if m:
        antetitulo = texto_plano(m.group(1)).strip()
        cuerpo = cuerpo[m.end():]

    m_fecha = re.match(r"(\d{4}-\d{2}-\d{2})", ruta.stem)
    fecha = str(primero(meta, "fecha", "date", defecto=m_fecha.group(1) if m_fecha else ""))
    edicion = str(primero(meta, "edicion", "edición", defecto=""))

    categorias = []
    for c in como_lista(primero(meta, "categorias", "categorías")):
        if c in CATEGORIAS:
            categorias.append(c)
        else:
            print(f"aviso: {ruta.name}: categoría desconocida '{c}' "
                  f"(válidas: {', '.join(CATEGORIAS)})", file=sys.stderr)

    return {
        "slug": str(primero(meta, "slug", defecto=ruta.stem)),
        "titulo": str(primero(meta, "titulo", "título", "title", defecto=antetitulo or ruta.stem)),
        "antetitulo": antetitulo,
        "fecha": fecha,
        "edicion": edicion,
        "orden": int(edicion) if edicion.isdigit() else 0,
        "temas": como_lista(primero(meta, "temas", "tags")),
        "categorias": categorias,
        "lugares": como_lista(meta.get("lugares")),
        "nota": str(primero(meta, "nota", defecto="")),
        "cuerpo": marcar_bloques(envolver_secciones(cuerpo)),
    }


def html_categorias(categorias, raiz):
    if not categorias:
        return ""
    items = "".join(f'<li><a href="{raiz}categorias/{c}.html">{html.escape(CATEGORIAS[c])}</a></li>'
                    for c in categorias)
    return f'<ul class="temas" aria-label="Categorías">{items}</ul>'


def nav_categorias(ediciones, raiz, actual=None):
    """Barra de categorías con cuántas ediciones tiene cada una."""
    conteo = {c: sum(c in e["categorias"] for e in ediciones) for c in CATEGORIAS}
    marca = ' aria-current="page"' if actual is None else ""
    items = [f'<li><a href="{raiz}index.html"{marca}>Todas</a></li>']
    for c, nombre in CATEGORIAS.items():
        if not conteo[c]:
            continue
        marca = ' aria-current="page"' if c == actual else ""
        items.append(f'<li><a href="{raiz}categorias/{c}.html"{marca}>{html.escape(nombre)}'
                     f' <span>{conteo[c]}</span></a></li>')
    return f'<nav class="categorias" aria-label="Categorías"><ul>{"".join(items)}</ul></nav>'


def linea_fecha(e):
    partes = [f'<time datetime="{html.escape(e["fecha"])}">{fecha_legible(e["fecha"])}</time>']
    if e["edicion"]:
        partes.append(f"Edición {html.escape(e['edicion'])}")
    return " · ".join(partes)


def form_ajuste(pagina, titulo):
    """Formulario de ajustes de estilo y tono; lo recibe src/worker.js."""
    return f"""<details class="ajuste">
<summary>Sugerir un ajuste de estilo o tono</summary>
<form method="post" action="/api/ajuste">
<input type="hidden" name="pagina" value="{html.escape(pagina)}">
<input type="hidden" name="titulo" value="{html.escape(titulo)}">
<label>Ajuste
<textarea name="texto" rows="5" maxlength="4000" required placeholder="Por ejemplo: en la fricción 2, «plata» debería decir «recursos». En general, menos frases cortas."></textarea></label>
<div class="ajuste-fila">
<label>Nombre <input name="quien" autocomplete="name"></label>
<label>Clave <input name="clave" type="password" autocomplete="current-password" required></label>
</div>
<button type="submit">Enviar ajuste</button>
<p class="ajuste-nota">Los ajustes puntuales corrigen esta edición; los generales se vuelven regla para las siguientes. Se aplican cada hora, de 6 a. m. a 10 p. m.</p>
</form>
</details>"""


def pagina_edicion(base, e, anterior, siguiente):
    nav = []
    if anterior:
        nav.append(f'<a rel="prev" href="{anterior["slug"]}.html">← {html.escape(anterior["titulo"])}</a>')
    if siguiente:
        nav.append(f'<a rel="next" href="{siguiente["slug"]}.html">{html.escape(siguiente["titulo"])} →</a>')
    lugares = (f'<p class="lugares">{" · ".join(html.escape(l) for l in e["lugares"])}</p>'
               if e["lugares"] else "")
    nota = f'<p class="nota">{html.escape(e["nota"])}</p>' if e["nota"] else ""
    contenido = f"""<article class="edicion">
<header class="cabecera">
<p class="fecha">{linea_fecha(e)}</p>
<h1>{html.escape(e['titulo'])}</h1>
{lugares}
{html_categorias(e['categorias'], '../')}
{nota}
</header>
{e['cuerpo']}
</article>
<nav class="entre-ediciones" aria-label="Otras ediciones">{''.join(nav)}</nav>
{form_ajuste(f"/ediciones/{e['slug']}.html", e['titulo'])}"""
    return base.substitute(
        titulo=html.escape(f"{e['titulo']} · Otra lectura"),
        descripcion=html.escape(e["antetitulo"] or e["titulo"]),
        raiz="../",
        contenido=contenido,
    )


def pagina_lista(base, ediciones, todas, raiz, titulo, bajada, actual=None):
    """Portada (todas las ediciones) o página de una categoría."""
    filas = [f"""<li>
<p class="fecha">{linea_fecha(e)}</p>
<a href="{raiz}ediciones/{e['slug']}.html">{html.escape(e['titulo'])}</a>
{html_categorias(e['categorias'], raiz)}
</li>""" for e in ediciones]
    lista = "\n".join(filas) if filas else "<li>Todavía no hay ediciones.</li>"
    return base.substitute(
        titulo=html.escape(titulo if actual is None else f"{titulo} · Otra lectura"),
        descripcion=html.escape(bajada),
        raiz=raiz,
        contenido=f"""<header class="cabecera">
<h1>{html.escape(titulo)}</h1>
<p class="bajada">{html.escape(bajada)}</p>
</header>
{nav_categorias(todas, raiz, actual)}
<ol class="indice" reversed>
{lista}
</ol>
{form_ajuste("/" if actual is None else f"/categorias/{actual}.html", titulo)}""",
    )


def main():
    base = Template((PLANTILLA / "base.html").read_text(encoding="utf-8"))
    ediciones = [leer_edicion(p) for p in sorted(EDICIONES.glob("*.md"))]

    slugs = [e["slug"] for e in ediciones]
    repetidos = {s for s in slugs if slugs.count(s) > 1}
    if repetidos:
        sys.exit(f"error: slugs repetidos: {', '.join(sorted(repetidos))}")

    # Cronológico inverso; a igual fecha, la edición de número mayor primero.
    ediciones.sort(key=lambda e: (e["fecha"], e["orden"], e["slug"]), reverse=True)

    # site/ es salida: se regenera entero.
    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "ediciones").mkdir(parents=True)
    shutil.copy(PLANTILLA / "estilo.css", SITE / "estilo.css")
    shutil.copytree(PLANTILLA / "fuentes", SITE / "fuentes")

    for i, e in enumerate(ediciones):
        anterior = ediciones[i + 1] if i + 1 < len(ediciones) else None
        siguiente = ediciones[i - 1] if i > 0 else None
        (SITE / "ediciones" / f"{e['slug']}.html").write_text(
            pagina_edicion(base, e, anterior, siguiente), encoding="utf-8")

    (SITE / "index.html").write_text(pagina_lista(
        base, ediciones, ediciones, "", "Archivo",
        "Un hábito de lectura, no un noticiero: qué se traba, quién lo está "
        "resolviendo y con qué contrapeso."), encoding="utf-8")

    (SITE / "categorias").mkdir()
    for c, nombre in CATEGORIAS.items():
        de_categoria = [e for e in ediciones if c in e["categorias"]]
        n = len(de_categoria)
        bajada = f"{n} edición" if n == 1 else f"{n} ediciones"
        (SITE / "categorias" / f"{c}.html").write_text(pagina_lista(
            base, de_categoria, ediciones, "../", nombre, bajada, actual=c), encoding="utf-8")
    print(f"{len(ediciones)} ediciones → {SITE.relative_to(RAIZ)}/")


if __name__ == "__main__":
    main()
