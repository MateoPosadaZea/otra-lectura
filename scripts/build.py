#!/usr/bin/env python3
"""Genera site/ a partir de ediciones/*.md y candidatas.md.

El markdown es la fuente; todo lo que hay en site/ es salida y se puede
borrar y regenerar. Única dependencia externa: Python-Markdown (ver
requirements.txt). El frontmatter lo lee scripts/frontmatter.py.

Convenciones del cuerpo de las ediciones (ver prompt.md y RUTINA.md):
  # Radar · fecha              → antetítulo (se omite; la cabecera sale del frontmatter)
  ## Carril 1: Radar           → carril (divisor de sección)
  ### 1. Fricción {#slug}      → fricción; el slug es opcional (si falta, sale del título)
  **Qué ocurrió.** texto       → subtítulo de la fricción (etiqueta en negrita)
  *(Conocimiento general.)*    → marca de "no verificado"

El build falla con un mensaje claro si una edición tiene frontmatter
inválido, si una fuente no tiene url o si un slug de seguimiento no
resuelve a ninguna edición anterior.
"""

import html
import json
import re
import shutil
import sys
import unicodedata
from datetime import date
from pathlib import Path
from string import Template

import markdown

sys.path.insert(0, str(Path(__file__).resolve().parent))
from frontmatter import ErrorFrontmatter, parsear  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
EDICIONES = RAIZ / "ediciones"
PLANTILLA = RAIZ / "plantilla"
SITE = RAIZ / "site"
CANDIDATAS = RAIZ / "candidatas.md"

# Dirección pública del sitio, sin barra final (p. ej. "https://otra-lectura.xxx.workers.dev").
# Hace falta para las vistas previas al compartir (og:image y og:url deben ser
# absolutas), la url canónica y el sitemap. Vacía, esas etiquetas se omiten.
SITIO_URL = ""

NOMBRE_SITIO = "Otra lectura"
FRASE_SITIO = "Una mirada pragmática para informarse y participar."
DESCRIPCION_SITIO = (
    "Otra manera de leer noticias, con contexto, soluciones y contrapeso. Cada "
    "día, los problemas que se repiten en Colombia, América Latina "
    "y el mundo, con su contexto histórico, las soluciones que ya funcionan en "
    "otros lugares y sus críticas.")

# Mientras el proyecto está en calibración, el sitio pide no ser indexado
# (robots.txt con Disallow total y meta noindex). Para abrirlo a buscadores,
# basta con cambiar esto a True y volver a publicar.
INDEXAR = False

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

# Categorías amplias y fijas para navegar el archivo. Cada edición declara las
# suyas en el frontmatter (`categorias: [economia, salud]`). Para agregar una,
# se añade aquí y en RUTINA.md.
# Pocas y amplias, porque van en la barra de la cabecera:
#   economia  → economía, finanzas públicas, trabajo
#   salud     → salud pública, medicamentos, sistemas de salud
#   ambiente  → clima, agua, energía, minería, biodiversidad
#   sociedad  → justicia, seguridad, Estado, ciudades, territorio, educación
#   ciencia   → ciencia, tecnología, inteligencia artificial, descubrimientos
CATEGORIAS = {
    "economia": "Economía",
    "salud": "Salud",
    "ambiente": "Ambiente",
    "sociedad": "Sociedad",
    "ciencia": "Ciencia",
}

# Explicación corta bajo la banda de cada carril (el markdown dice "Carril 1: Radar";
# en pantalla se muestra solo "Radar").
BAJADA_CARRIL = {
    "carril-radar": "Problemas que se repiten, quién los está abordando, con qué resultados y con qué críticas.",
    "carril-asombro": "Hallazgos e historias que amplían la mirada, aunque no sirvan para nada inmediato.",
}

# Categorías con al menos una edición; las llena main() para el menú.
CATEGORIAS_ACTIVAS = []

ESTADOS_CANDIDATA = ["pendiente", "evaluada", "descartada", "activa"]

CAMPOS_LISTA = ["temas", "categorias", "lugares", "cruce_mattriz", "seguimiento"]
CAMPOS_CONOCIDOS = {"fecha", "edicion", "titulo", "slug", "nota",
                    "actualizaciones", "correcciones", "fuentes", *CAMPOS_LISTA}

RE_NO_VERIFICADO = re.compile(r"conocimiento\s+general|no\s+verificad[oa]s?", re.I)

# Etiqueta en negrita → clase del párrafo que la lleva.
TIPOS_ETIQUETA = [
    (re.compile(r"contrapeso", re.I), "contrapeso"),
    (re.compile(r"sin salida conocida", re.I), "sin-salida"),
    (re.compile(r"conflicto de inter[eé]s", re.I), "conflicto"),
    (re.compile(r"cruce con mattriz", re.I), "cruce"),
]


class ErrorEdicion(Exception):
    pass


# --- Utilidades --------------------------------------------------------------

def fecha_legible(iso):
    try:
        d = date.fromisoformat(iso)
    except ValueError:
        return iso
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def slugificar(texto):
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def normalizar(texto):
    return re.sub(r"\s+", " ", texto).strip().lower()


def texto_plano(fragmento):
    return html.unescape(re.sub(r"<[^>]+>", "", fragmento))


def convertir(md_texto):
    return markdown.markdown(md_texto, extensions=["extra", "sane_lists"], output_format="html")


def convertir_linea(md_texto):
    """Markdown de una sola línea (texto de una actualización o fuente), sin <p>."""
    h = convertir(md_texto).strip()
    return h[3:-4] if h.startswith("<p>") and h.endswith("</p>") and h.count("<p>") == 1 else h


# --- Validación del frontmatter ----------------------------------------------

def _fecha(valor, donde):
    if not isinstance(valor, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", valor):
        raise ErrorEdicion(f"{donde}: fecha inválida «{valor}» (formato AAAA-MM-DD)")
    try:
        date.fromisoformat(valor)
    except ValueError:
        raise ErrorEdicion(f"{donde}: la fecha «{valor}» no existe")
    return valor


def _texto(valor, donde, requerido=True):
    if valor is None or valor == "":
        if requerido:
            raise ErrorEdicion(f"{donde}: falta")
        return ""
    if not isinstance(valor, str):
        raise ErrorEdicion(f"{donde}: debe ser texto")
    return valor.strip()


def _lista_textos(valor, donde):
    if valor is None:
        return []
    if isinstance(valor, str):
        return [x.strip() for x in valor.split(",") if x.strip()]
    if not isinstance(valor, list) or not all(isinstance(x, str) for x in valor):
        raise ErrorEdicion(f"{donde}: debe ser una lista de textos")
    return [x.strip() for x in valor if x.strip()]


def _lista_mapas(valor, donde, campos):
    if valor is None:
        return []
    if not isinstance(valor, list) or not all(isinstance(x, dict) for x in valor):
        raise ErrorEdicion(f"{donde}: debe ser una lista de elementos con {', '.join(campos)}")
    for i, item in enumerate(valor, 1):
        sobran = set(item) - set(campos)
        if sobran:
            raise ErrorEdicion(f"{donde}[{i}]: campo desconocido «{', '.join(sorted(sobran))}» "
                               f"(válidos: {', '.join(campos)})")
    return valor


def validar(meta, ruta):
    desconocidos = set(meta) - CAMPOS_CONOCIDOS
    if desconocidos:
        raise ErrorEdicion(f"campo desconocido «{', '.join(sorted(desconocidos))}» "
                           f"(válidos: {', '.join(sorted(CAMPOS_CONOCIDOS))})")
    fecha = _fecha(meta.get("fecha"), "fecha")
    edicion = _texto(meta.get("edicion"), "edicion")
    if not edicion.isdigit():
        raise ErrorEdicion(f"edicion: debe ser un número entero, no «{edicion}»")
    datos = {
        "slug": _texto(meta.get("slug"), "slug", requerido=False) or ruta.stem,
        "titulo": _texto(meta.get("titulo"), "titulo"),
        "fecha": fecha,
        "edicion": edicion,
        "orden": int(edicion),
        "nota": _texto(meta.get("nota"), "nota", requerido=False),
    }
    for campo in CAMPOS_LISTA:
        datos[campo] = _lista_textos(meta.get(campo), campo)
    malas = [c for c in datos["categorias"] if c not in CATEGORIAS]
    if malas:
        raise ErrorEdicion(f"categorias: «{', '.join(malas)}» no existe (válidas: {', '.join(CATEGORIAS)})")

    datos["actualizaciones"] = [
        {"fecha": _fecha(a.get("fecha"), f"actualizaciones[{i}].fecha"),
         "texto": _texto(a.get("texto"), f"actualizaciones[{i}].texto"),
         "friccion": _texto(a.get("friccion"), f"actualizaciones[{i}].friccion", requerido=False)}
        for i, a in enumerate(_lista_mapas(meta.get("actualizaciones"), "actualizaciones",
                                           ["fecha", "friccion", "texto"]), 1)]
    datos["correcciones"] = [
        {"fecha": _fecha(c.get("fecha"), f"correcciones[{i}].fecha"),
         "texto": _texto(c.get("texto"), f"correcciones[{i}].texto")}
        for i, c in enumerate(_lista_mapas(meta.get("correcciones"), "correcciones",
                                           ["fecha", "texto"]), 1)]
    fuentes = []
    for i, f in enumerate(_lista_mapas(meta.get("fuentes"), "fuentes", ["titulo", "medio", "url"]), 1):
        url = _texto(f.get("url"), f"fuentes[{i}].url")
        if not re.match(r"^https?://\S+$", url):
            raise ErrorEdicion(f"fuentes[{i}].url: «{url}» no es una url http(s) válida")
        fuentes.append({"titulo": _texto(f.get("titulo"), f"fuentes[{i}].titulo"),
                        "medio": _texto(f.get("medio"), f"fuentes[{i}].medio", requerido=False),
                        "url": url})
    datos["fuentes"] = fuentes
    return datos


# --- Marcado del cuerpo -------------------------------------------------------

RE_HEADING = re.compile(r"<h([1-6])([^>]*)>(.*?)</h\1>", re.S)


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
    """<h2> abre un carril (<section>) y <h3> una fricción (<article id=slug>).

    Cada bloque va hasta el siguiente título de nivel igual o superior. Deja
    marcas <!--fin:slug--> al cierre de cada fricción (para sus
    actualizaciones) y <!--antes-glosario--> antes del glosario (para las
    fuentes). Devuelve (html, slugs_de_fricciones).
    """
    salida, pila, pos, slugs = [], [], 0, []

    def cerrar():
        nivel, tag, slug = pila.pop()
        if slug:
            salida.append(f"<!--fin:{slug}-->\n")
        salida.append(f"</{tag}>\n")

    for m in RE_HEADING.finditer(cuerpo):
        nivel, attrs, interior = int(m.group(1)), m.group(2), m.group(3)
        texto = texto_plano(interior)
        salida.append(cuerpo[pos:m.start()])
        while pila and pila[-1][0] >= nivel:
            cerrar()
        clases = clases_heading(nivel, texto)
        heading = m.group(0)
        if nivel == 2 and clases:
            if texto.strip().lower().startswith("glosario"):
                salida.append("<!--antes-glosario-->\n")
                salida.append(f'<section class="{" ".join(clases)}" id="glosario">\n')
            else:
                salida.append(f'<section class="{" ".join(clases)}">\n')
            # "Carril 1: Radar" → "Radar", con una línea que explica el carril.
            heading = re.sub(r"(<h2[^>]*>)\s*Carril\s+\d+\s*:\s*", r"\1", heading, flags=re.I)
            bajada = next((BAJADA_CARRIL[c] for c in clases if c in BAJADA_CARRIL), "")
            if bajada:
                heading += f'\n<p class="carril-bajada">{bajada}</p>'
            pila.append((nivel, "section", None))
        elif nivel == 3 and clases:
            # Slug explícito con {#slug} (attr_list) o derivado del título sin número.
            m_id = re.search(r'\sid="([^"]+)"', attrs)
            slug = m_id.group(1) if m_id else slugificar(re.sub(r"^\s*\d+\.\s*", "", texto))
            if m_id:
                heading = heading.replace(m_id.group(0), "", 1)
            base, n = slug, 2
            while slug in slugs:
                slug, n = f"{base}-{n}", n + 1
            slugs.append(slug)
            salida.append(f'<article class="{" ".join(clases)}" id="{slug}">\n')
            pila.append((nivel, "article", slug))
        salida.append(heading)
        pos = m.end()
    salida.append(cuerpo[pos:])
    while pila:
        cerrar()
    return "".join(salida), slugs


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


def extraer_glosario(cuerpo):
    """Términos de la sección Glosario: [(término, definición_html)]."""
    m = re.search(r'<section[^>]*id="glosario">(.*?)</section>', cuerpo, re.S)
    if not m:
        return []
    terminos = []
    for li in re.findall(r"<li>(.*?)</li>", m.group(1), re.S):
        t = re.match(r"\s*<strong>(.*?)</strong>\s*(.*)", li, re.S)
        if t:
            termino = texto_plano(t.group(1)).strip().rstrip(":").strip()
            definicion = re.sub(r"^\s*:\s*", "", t.group(2)).strip()
            terminos.append((termino, definicion))
    return terminos


# --- Lectura de ediciones -----------------------------------------------------

def leer_edicion(ruta):
    try:
        meta, cuerpo_md = parsear(ruta.read_text(encoding="utf-8"))
    except ErrorFrontmatter as err:
        raise ErrorEdicion(f"frontmatter inválido: {err}")
    e = validar(meta, ruta)
    cuerpo = convertir(cuerpo_md).strip()

    # El "# Radar · fecha" del cuerpo se omite: la cabecera sale del frontmatter.
    e["antetitulo"] = ""
    m = re.match(r"<h1[^>]*>(.*?)</h1>\s*", cuerpo, re.S)
    if m:
        e["antetitulo"] = texto_plano(m.group(1)).strip()
        cuerpo = cuerpo[m.end():]

    cuerpo, e["fricciones"] = envolver_secciones(cuerpo)
    # Títulos de las fricciones (sin número ni lugares) para la descripción.
    e["titulos_fricciones"] = [
        re.sub(r"\s*\([^)]*\)\s*$", "", re.sub(r"^\s*\d+\.\s*", "", texto_plano(t))).strip()
        for t in re.findall(r'<article class="item(?! seguimiento)[^"]*"[^>]*>\s*<h3[^>]*>(.*?)</h3>', cuerpo, re.S)]
    e["cuerpo"] = marcar_bloques(cuerpo)
    e["glosario"] = extraer_glosario(e["cuerpo"])

    for i, a in enumerate(e["actualizaciones"], 1):
        if a["friccion"] and a["friccion"] not in e["fricciones"]:
            raise ErrorEdicion(
                f"actualizaciones[{i}].friccion: «{a['friccion']}» no es una fricción de esta "
                f"edición (disponibles: {', '.join(e['fricciones']) or 'ninguna'})")
    cambios = [a["fecha"] for a in e["actualizaciones"]] + [c["fecha"] for c in e["correcciones"]]
    e["ultimo_cambio"] = max(cambios) if cambios else ""
    return e


def resolver_seguimientos(ediciones):
    """Cada slug de `seguimiento` debe aparecer en `temas` de una edición anterior."""
    errores = []
    for e in ediciones:
        e["seguimiento_enlaces"] = []
        for tema in e["seguimiento"]:
            previas = [o for o in ediciones
                       if o is not e and tema in o["temas"]
                       and (o["fecha"], o["orden"]) < (e["fecha"], e["orden"])]
            if not previas:
                errores.append(f"ediciones/{e['archivo']}: seguimiento «{tema}» no resuelve: ninguna "
                               f"edición anterior lo tiene en `temas`")
                continue
            previas.sort(key=lambda o: (o["fecha"], o["orden"]))
            e["seguimiento_enlaces"].append((tema, previas))
    return errores


# --- Candidatas ---------------------------------------------------------------

def leer_candidatas():
    """candidatas.md: {idea_normalizada: {"titulo", "estado", "detalle" (html)}}.

    Formato: una sección "## Idea" por candidata; primera línea
    "Estado: …"; el resto es markdown (qué resolvería, cómo, por dónde
    empezar, entregable posible).
    """
    if not CANDIDATAS.exists():
        return {}
    candidatas = {}
    lineas = CANDIDATAS.read_text(encoding="utf-8").split("\n")
    inicios = [i for i, l in enumerate(lineas) if l.startswith("## ")]
    for k, i in enumerate(inicios):
        fin = inicios[k + 1] if k + 1 < len(inicios) else len(lineas)
        titulo = lineas[i][3:].strip()
        resto = lineas[i + 1:fin]
        m = next(((n, l) for n, l in enumerate(resto) if l.strip()), None)
        if not m or not m[1].lower().startswith("estado:"):
            raise ErrorEdicion(f"candidatas.md, línea {i + 1}: «{titulo}» debe empezar con "
                               f"'Estado: …' (válidos: {' | '.join(ESTADOS_CANDIDATA)})")
        estado = m[1].split(":", 1)[1].strip().lower()
        if estado not in ESTADOS_CANDIDATA:
            raise ErrorEdicion(f"candidatas.md, línea {i + m[0] + 2}: estado «{estado}» inválido "
                               f"(válidos: {' | '.join(ESTADOS_CANDIDATA)})")
        detalle = marcar_bloques(convertir("\n".join(resto[m[0] + 1:])))
        candidatas[normalizar(titulo)] = {"titulo": titulo, "estado": estado, "detalle": detalle}
    return candidatas


def reunir_candidatas(ediciones, estados):
    grupos = {}
    for e in ediciones:
        for idea in e["cruce_mattriz"]:
            g = grupos.setdefault(normalizar(idea), {"idea": idea, "origenes": []})
            g["origenes"].append(e)
    for clave in estados:
        if clave not in grupos:
            print(f"aviso: candidatas.md menciona «{clave}», que no aparece en ninguna edición",
                  file=sys.stderr)
    candidatas = []
    for clave, g in grupos.items():
        g["origenes"].sort(key=lambda o: (o["fecha"], o["orden"]))
        info = estados.get(clave, {})
        g["estado"] = info.get("estado", "pendiente")
        g["detalle"] = info.get("detalle", "")
        if info.get("titulo"):
            g["idea"] = info["titulo"]
        candidatas.append(g)
    candidatas.sort(key=lambda g: (g["origenes"][-1]["fecha"], g["origenes"][-1]["orden"]), reverse=True)
    return candidatas


# --- HTML ---------------------------------------------------------------------

def html_categorias(categorias, raiz):
    if not categorias:
        return ""
    items = "".join(f'<li><a href="{raiz}categorias/{c}.html">{html.escape(CATEGORIAS[c])}</a></li>'
                    for c in categorias)
    return f'<ul class="temas" aria-label="Categorías">{items}</ul>'


def linea_fecha(e):
    partes = [f'<time datetime="{html.escape(e["fecha"])}">{fecha_legible(e["fecha"])}</time>']
    if e["edicion"]:
        partes.append(f"Edición {html.escape(e['edicion'])}")
    return " · ".join(partes)


def enlace_edicion(o, raiz):
    return (f'<a href="{raiz}ediciones/{o["slug"]}.html">Edición {html.escape(o["edicion"])}'
            f' · {fecha_legible(o["fecha"])}</a>')


def aviso_cambios(e, raiz=None):
    """Aviso de actualizaciones o correcciones posteriores a la publicación.

    Con `raiz` enlaza a la edición (índice); sin ella, a los bloques de la
    misma página (cabecera de la edición).
    """
    if not e["ultimo_cambio"]:
        return ""
    n_a, n_c = len(e["actualizaciones"]), len(e["correcciones"])
    partes = []
    if n_a:
        partes.append(f"{n_a} actualización" if n_a == 1 else f"{n_a} actualizaciones")
    if n_c:
        partes.append(f"{n_c} corrección" if n_c == 1 else f"{n_c} correcciones")
    detalle = " y ".join(partes)
    fecha = f'<time datetime="{e["ultimo_cambio"]}">{fecha_legible(e["ultimo_cambio"])}</time>'
    if raiz is None:
        destino = "#actualizacion-1" if n_a else "#correcciones"
        return (f'<p class="aviso-cambios">Revisada el {fecha} · '
                f'<a href="{destino}">{detalle} posteriores a la publicación</a></p>')
    return (f'<p class="aviso-cambios"><a href="{raiz}ediciones/{e["slug"]}.html#'
            f'{"actualizacion-1" if n_a else "correcciones"}">Revisada el {fecha}</a> · {detalle}</p>')


def html_actualizacion(a, n):
    return (f'<aside class="actualizacion" id="actualizacion-{n}">\n'
            f'<p class="aviso-etiqueta">Actualización · <time datetime="{a["fecha"]}">'
            f'{fecha_legible(a["fecha"])}</time></p>\n'
            f'<p>{convertir_linea(a["texto"])}</p>\n</aside>\n')


def html_fuentes(fuentes):
    if not fuentes:
        return ""
    items = []
    for f in fuentes:
        medio = f'<span class="medio">{html.escape(f["medio"])}</span>. ' if f["medio"] else ""
        items.append(f'<li>{medio}<a href="{html.escape(f["url"])}">{html.escape(f["titulo"])}</a></li>')
    return (f'<section class="carril cierre fuentes" id="fuentes">\n<h2>Fuentes</h2>\n'
            f'<ol>\n{chr(10).join(items)}\n</ol>\n</section>\n')


def html_glosario_flotante(terminos):
    """Glosario fijo a la derecha en pantallas anchas; en móviles, un botón al glosario."""
    if not terminos:
        return ""
    items = "\n".join(f"<dt>{html.escape(t)}</dt><dd>{d}</dd>" for t, d in terminos)
    return f"""<aside class="glosario-flotante" aria-label="Glosario de la edición">
<details open>
<summary>Glosario</summary>
<dl>
{items}
</dl>
</details>
</aside>
<a class="glosario-boton" href="#glosario">Glosario</a>"""


def cuerpo_edicion(e):
    """Cuerpo con actualizaciones, fuentes y correcciones en su lugar."""
    cuerpo, n = e["cuerpo"], 0
    generales = []
    for a in e["actualizaciones"]:
        n += 1
        bloque = html_actualizacion(a, n)
        if a["friccion"]:
            marca = f"<!--fin:{a['friccion']}-->"
            cuerpo = cuerpo.replace(marca, bloque + marca, 1)
        else:
            generales.append(bloque)
    cuerpo = re.sub(r"<!--fin:[^>]*-->\n?", "", cuerpo)

    fuentes = html_fuentes(e["fuentes"])
    if "<!--antes-glosario-->" in cuerpo:
        cuerpo = cuerpo.replace("<!--antes-glosario-->", fuentes, 1)
    else:
        cuerpo += fuentes

    if generales:
        cuerpo += ('<section class="carril cierre avisos" id="actualizaciones">\n'
                   '<h2>Actualizaciones</h2>\n' + "".join(generales) + "</section>\n")
    if e["correcciones"]:
        items = "".join(
            f'<li><p class="aviso-etiqueta">Corrección · <time datetime="{c["fecha"]}">'
            f'{fecha_legible(c["fecha"])}</time></p>{convertir_linea(c["texto"])}</li>\n'
            for c in e["correcciones"])
        cuerpo += ('<section class="carril cierre avisos" id="correcciones">\n<h2>Correcciones</h2>\n'
                   '<p class="aviso-nota">El texto original no se modifica; las correcciones se '
                   f'agregan aquí.</p>\n<ol class="correcciones">\n{items}</ol>\n</section>\n')
    return cuerpo


def form_ajuste(pagina, titulo):
    """Formulario de ajustes (contenido, estilo o funciones del sitio); lo recibe src/worker.js."""
    return f"""<details class="ajuste">
<summary>Sugerir un ajuste</summary>
<form method="post" action="/api/ajuste">
<input type="hidden" name="pagina" value="{html.escape(pagina)}">
<input type="hidden" name="titulo" value="{html.escape(titulo)}">
<label>Ajuste
<textarea name="texto" rows="5" maxlength="4000" required placeholder="Una corrección de esta edición, una regla de estilo o tono, o un cambio al sitio. Por ejemplo: «un glosario flotante a la derecha»."></textarea></label>
<div class="ajuste-fila">
<label>Nombre <input name="quien" autocomplete="name"></label>
<label>Clave <input name="clave" type="password" autocomplete="current-password" required></label>
</div>
<button type="submit">Enviar ajuste</button>
<p class="ajuste-estado" role="status" aria-live="polite" hidden></p>
<p class="ajuste-nota">Correcciones de contenido, reglas de estilo y cambios de diseño o funciones del sitio. Se revisan cada hora, de 6 a. m. a 10 p. m.; los cambios grandes quedan para aprobación de Mateo.</p>
</form>
</details>"""


def html_menu(raiz, seccion=None):
    """Barra de secciones: Inicio y categorías; la actual va marcada."""
    def item(clave, href, nombre):
        marca = ' aria-current="page"' if clave == seccion else ""
        return f'<li><a href="{href}"{marca}>{html.escape(nombre)}</a></li>'
    items = [item("inicio", f"{raiz}index.html", "Inicio")]
    items += [item(c, f"{raiz}categorias/{c}.html", CATEGORIAS[c]) for c in CATEGORIAS_ACTIVAS]
    return "<ul>" + "".join(items) + "</ul>"


def recortar(texto, limite):
    """Corta en el último espacio antes del límite y agrega puntos suspensivos."""
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto if len(texto) <= limite else texto[:limite].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def descripcion_edicion(e):
    temas = "; ".join(e["titulos_fricciones"])
    inicio = f"Edición {e['edicion']}, {fecha_legible(e['fecha'])}"
    cuerpo = f"{inicio}: {temas}." if temas else f"{inicio}: {e['titulo']}."
    return f"{cuerpo} Contexto, soluciones y contrapeso."


def meta_etiquetas(titulo, descripcion, ruta, tipo, ld):
    """<meta> de descripción, robots, Open Graph, tarjeta de X y JSON-LD."""
    desc = recortar(descripcion, 300)
    m = [f'<meta name="description" content="{html.escape(recortar(descripcion, 160))}">',
         f'<meta property="og:site_name" content="{NOMBRE_SITIO}">',
         '<meta property="og:locale" content="es_CO">',
         f'<meta property="og:type" content="{tipo}">',
         f'<meta property="og:title" content="{titulo}">',
         f'<meta property="og:description" content="{html.escape(desc)}">',
         '<meta name="twitter:card" content="summary_large_image">',
         f'<meta name="twitter:title" content="{titulo}">',
         f'<meta name="twitter:description" content="{html.escape(desc)}">',
         '<meta name="theme-color" content="#d8d1c7" media="(prefers-color-scheme: light)">',
         '<meta name="theme-color" content="#1b1a18" media="(prefers-color-scheme: dark)">']
    if not INDEXAR:
        m.append('<meta name="robots" content="noindex, nofollow">')
    if SITIO_URL:
        url = SITIO_URL + ruta
        m += [f'<link rel="canonical" href="{url}">',
              f'<meta property="og:url" content="{url}">',
              f'<meta property="og:image" content="{SITIO_URL}/og.png">',
              '<meta property="og:image:width" content="1200">',
              '<meta property="og:image:height" content="630">',
              f'<meta property="og:image:alt" content="{NOMBRE_SITIO}: una mirada pragmática para informarse y participar">',
              f'<meta name="twitter:image" content="{SITIO_URL}/og.png">']
        ld = {**ld, "url": url}
    # "<\/" evita que un "</script>" dentro de los datos cierre el bloque.
    datos = json.dumps({"@context": "https://schema.org", **ld}, ensure_ascii=False).replace("</", "<\\/")
    m.append(f'<script type="application/ld+json">{datos}</script>')
    return "\n".join(m)


def pagina(base, titulo, descripcion, raiz, contenido, ruta, tipo="website", ld=None, seccion=None):
    ld = ld or {"@type": "WebPage", "name": html.unescape(titulo), "description": descripcion,
                "inLanguage": "es-CO", "isPartOf": {"@type": "WebSite", "name": NOMBRE_SITIO}}
    return base.substitute(titulo=titulo, raiz=raiz, contenido=contenido, menu=html_menu(raiz, seccion),
                           meta=meta_etiquetas(titulo, descripcion, ruta, tipo, ld))


def pagina_edicion(base, e, anterior, siguiente):
    nav = []
    if anterior:
        nav.append(f'<a rel="prev" href="{anterior["slug"]}.html">← {html.escape(anterior["titulo"])}</a>')
    if siguiente:
        nav.append(f'<a rel="next" href="{siguiente["slug"]}.html">{html.escape(siguiente["titulo"])} →</a>')
    lugares = (f'<p class="lugares">{" · ".join(html.escape(l) for l in e["lugares"])}</p>'
               if e["lugares"] else "")
    nota = f'<p class="nota">{html.escape(e["nota"])}</p>' if e["nota"] else ""
    seguimiento = ""
    if e["seguimiento_enlaces"]:
        filas = "".join(
            f'<li><span>{html.escape(tema.replace("-", " "))}</span>: '
            f'{", ".join(enlace_edicion(o, "../") for o in previas)}</li>'
            for tema, previas in e["seguimiento_enlaces"])
        seguimiento = f'<div class="seguimiento-de"><p>Seguimiento de temas anteriores</p><ul>{filas}</ul></div>'
    contenido = f"""<article class="edicion">
<header class="cabecera">
<p class="fecha">{linea_fecha(e)}</p>
<h1>{html.escape(e['titulo'])}</h1>
{lugares}
{html_categorias(e['categorias'], '../')}
{nota}
{aviso_cambios(e)}
{seguimiento}
</header>
{cuerpo_edicion(e)}
</article>
{html_glosario_flotante(e['glosario'])}
<nav class="entre-ediciones" aria-label="Otras ediciones">{''.join(nav)}</nav>
{form_ajuste(f"/ediciones/{e['slug']}.html", e['titulo'])}"""
    descripcion = descripcion_edicion(e)
    ld = {"@type": "Article", "headline": e["titulo"], "description": descripcion,
          "datePublished": e["fecha"], "dateModified": e["ultimo_cambio"] or e["fecha"],
          "inLanguage": "es-CO", "articleSection": [CATEGORIAS[c] for c in e["categorias"]],
          "keywords": ", ".join(e["temas"]), "contentLocation": e["lugares"],
          "author": {"@type": "Organization", "name": NOMBRE_SITIO},
          "publisher": {"@type": "Organization", "name": NOMBRE_SITIO},
          "isAccessibleForFree": True}
    if e["fuentes"]:
        ld["citation"] = [f["url"] for f in e["fuentes"]]
    return pagina(base, html.escape(f"{e['titulo']} · Otra lectura"), descripcion, "../",
                  contenido, f"/ediciones/{e['slug']}.html", "article", ld)


# Epígrafe de la portada: cita, autor y obra.
EPIGRAFE = {
    "cita": "He procurado con esmero no ridiculizar ni lamentar ni detestar las acciones "
            "humanas, sino entenderlas.",
    "autor": "Baruch Spinoza",
    "obra": "Tratado político",
    "anio": "1677",
}


def pagina_lista(base, ediciones, todas, raiz, titulo, bajada, actual=None):
    """Portada (todas las ediciones) o página de una categoría."""
    filas = [f"""<li>
<p class="fecha">{linea_fecha(e)}</p>
<a href="{raiz}ediciones/{e['slug']}.html">{html.escape(e['titulo'])}</a>
{aviso_cambios(e, raiz)}
</li>""" for e in ediciones]
    lista = "\n".join(filas) if filas else "<li>Todavía no hay ediciones.</li>"
    if actual is None:
        cabecera = f"""<header class="cabecera portada">
<h1 class="solo-lectores">Otra lectura</h1>
<figure class="epigrafe">
<blockquote><p>«{html.escape(EPIGRAFE['cita'])}»</p></blockquote>
<figcaption>{html.escape(EPIGRAFE['autor'])} <cite>{html.escape(EPIGRAFE['obra'])}</cite>, {EPIGRAFE['anio']}</figcaption>
</figure>
</header>"""
    else:
        cabecera = f"""<header class="cabecera">
<h1>{html.escape(titulo)}</h1>
<p class="bajada">{html.escape(bajada)}</p>
</header>"""
    contenido = f"""{cabecera}
<ol class="indice" reversed>
{lista}
</ol>
{form_ajuste("/" if actual is None else f"/categorias/{actual}.html", titulo)}"""
    if actual is None:
        ld = {"@type": "WebSite", "name": NOMBRE_SITIO, "description": DESCRIPCION_SITIO,
              "inLanguage": "es-CO"}
        return pagina(base, "Otra lectura", DESCRIPCION_SITIO,
                      raiz, contenido, "/", "website", ld, seccion="inicio")
    descripcion = (f"{titulo}: ediciones de Otra lectura con contexto, soluciones y contrapeso. "
                   f"{bajada}.")
    return pagina(base, html.escape(f"{titulo} · Otra lectura"), descripcion, raiz, contenido,
                  f"/categorias/{actual}.html", seccion=actual)


def pagina_candidatas(base, candidatas):
    conteo = {s: sum(c["estado"] == s for c in candidatas) for s in ESTADOS_CANDIDATA}
    resumen = " · ".join(f"{n} {s}" + ("s" if n != 1 else "") for s, n in conteo.items() if n)
    filas = []
    for c in candidatas:
        origenes = ", ".join(enlace_edicion(o, "") for o in c["origenes"])
        filas.append(f"""<li>
<p class="fecha"><span class="estado estado-{c['estado']}">{c['estado']}</span></p>
<p class="idea">{html.escape(c['idea'][:1].upper() + c['idea'][1:])}</p>
<p class="origen">Surgió en {origenes}</p>
{f'<div class="candidata-detalle">{c["detalle"]}</div>' if c["detalle"] else ""}
</li>""")
    lista = "\n".join(filas) if filas else "<li>Todavía no hay candidatas.</li>"
    contenido = f"""<header class="cabecera">
<h1>Candidatas</h1>
<p class="bajada">Cruces con Mattriz surgidos en el radar. Candidatas, no tareas.</p>
</header>
<p class="candidatas-resumen">{resumen or "Sin candidatas"}. El desarrollo y el estado se editan en <code>candidatas.md</code>.</p>
<ol class="indice candidatas">
{lista}
</ol>
{form_ajuste("/candidatas.html", "Candidatas")}"""
    return pagina(base, "Candidatas · Otra lectura",
                  "Ideas de cruce con Mattriz surgidas en Otra lectura: candidatas, no tareas.",
                  "", contenido, "/candidatas.html")


# --- Principal -----------------------------------------------------------------

def main():
    base = Template((PLANTILLA / "base.html").read_text(encoding="utf-8"))

    ediciones, errores = [], []
    for ruta in sorted(EDICIONES.glob("*.md")):
        try:
            e = leer_edicion(ruta)
            e["archivo"] = ruta.name
            ediciones.append(e)
        except ErrorEdicion as err:
            errores.append(f"ediciones/{ruta.name}: {err}")

    slugs = [e["slug"] for e in ediciones]
    repetidos = {s for s in slugs if slugs.count(s) > 1}
    if repetidos:
        errores.append(f"slugs de edición repetidos: {', '.join(sorted(repetidos))}")
    errores += resolver_seguimientos(ediciones)
    try:
        estados = leer_candidatas()
    except ErrorEdicion as err:
        errores.append(str(err))
    if errores:
        print("El build se detuvo. Corrija esto y vuelva a ejecutar ./build.sh:", file=sys.stderr)
        for err in errores:
            print(f"  error: {err}", file=sys.stderr)
        sys.exit(1)

    # Cronológico inverso; a igual fecha, la edición de número mayor primero.
    ediciones.sort(key=lambda e: (e["fecha"], e["orden"], e["slug"]), reverse=True)
    CATEGORIAS_ACTIVAS[:] = [c for c in CATEGORIAS if any(c in e["categorias"] for e in ediciones)]

    # site/ es salida: se regenera entero.
    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "ediciones").mkdir(parents=True)
    shutil.copy(PLANTILLA / "estilo.css", SITE / "estilo.css")
    shutil.copytree(PLANTILLA / "fuentes", SITE / "fuentes")
    shutil.copy(PLANTILLA / "og.png", SITE / "og.png")
    robots = "User-agent: *\n" + ("Allow: /\n" if INDEXAR else "Disallow: /\n")
    if INDEXAR and SITIO_URL:
        robots += f"Sitemap: {SITIO_URL}/sitemap.xml\n"
    (SITE / "robots.txt").write_text(robots, encoding="utf-8")

    for i, e in enumerate(ediciones):
        anterior = ediciones[i + 1] if i + 1 < len(ediciones) else None
        siguiente = ediciones[i - 1] if i > 0 else None
        (SITE / "ediciones" / f"{e['slug']}.html").write_text(
            pagina_edicion(base, e, anterior, siguiente), encoding="utf-8")

    (SITE / "index.html").write_text(pagina_lista(
        base, ediciones, ediciones, "", "Archivo",
        FRASE_SITIO), encoding="utf-8")

    (SITE / "categorias").mkdir()
    for c, nombre in CATEGORIAS.items():
        de_categoria = [e for e in ediciones if c in e["categorias"]]
        n = len(de_categoria)
        bajada = f"{n} edición" if n == 1 else f"{n} ediciones"
        (SITE / "categorias" / f"{c}.html").write_text(pagina_lista(
            base, de_categoria, ediciones, "../", nombre, bajada, actual=c), encoding="utf-8")

    if SITIO_URL:
        urls = [("/", ediciones[0]["fecha"] if ediciones else "")]
        urls += [(f"/ediciones/{e['slug']}.html", e["ultimo_cambio"] or e["fecha"]) for e in ediciones]
        urls += [(f"/categorias/{c}.html", "") for c in CATEGORIAS_ACTIVAS]
        filas = "".join(f"<url><loc>{SITIO_URL}{u}</loc>" + (f"<lastmod>{f}</lastmod>" if f else "")
                        + "</url>\n" for u, f in urls)
        (SITE / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{filas}</urlset>\n',
            encoding="utf-8")

    candidatas = reunir_candidatas(ediciones, estados)
    (SITE / "candidatas.html").write_text(pagina_candidatas(base, candidatas), encoding="utf-8")

    print(f"{len(ediciones)} ediciones, {len(candidatas)} candidatas → {SITE.relative_to(RAIZ)}/"
          + ("" if INDEXAR else " (sin indexación)"))


if __name__ == "__main__":
    main()
