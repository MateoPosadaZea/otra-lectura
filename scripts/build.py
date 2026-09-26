#!/usr/bin/env python3
"""Genera site/ a partir de ediciones/*.md y candidatas.md.

El markdown es la fuente; todo lo que hay en site/ es salida y se puede
borrar y regenerar. Única dependencia externa: Python-Markdown (ver
requirements.txt). El frontmatter lo lee scripts/frontmatter.py.

Convenciones del cuerpo de las ediciones (ver prompt.md y RUTINA.md):
  # Radar · fecha              → antetítulo (se omite; la cabecera sale del frontmatter)
  ## Carril 1: Radar           → carril (divisor de sección)
  ### 1. Nudo {#slug}      → nudo; el slug es opcional (si falta, sale del título)
  **Qué ocurrió.** texto       → subtítulo del nudo (etiqueta en negrita)
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
import graficos  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
EDICIONES = RAIZ / "ediciones"
PLANTILLA = RAIZ / "plantilla"
SITE = RAIZ / "site"
CANDIDATAS = RAIZ / "candidatas.md"
AYUDA = RAIZ / "ayuda.md"
SOBRE = RAIZ / "sobre.md"

# Dirección pública del sitio, sin barra final (p. ej. "https://otra-lectura.xxx.workers.dev").
# Hace falta para las vistas previas al compartir (og:image y og:url deben ser
# absolutas), la url canónica y el sitemap. Vacía, esas etiquetas se omiten.
SITIO_URL = "https://otralectura.co"

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

# Comentarios abiertos al público. Mientras esté en False, comentar y
# corregir exige la clave familiar (como hasta ahora). Para abrir: poner
# True, pegar aquí la "site key" pública de Turnstile y guardar la clave
# secreta como TURNSTILE_SECRET en el Worker. Pasos en APERTURA.md.
COMENTARIOS_ABIERTOS = False
TURNSTILE_SITEKEY = ""

DIAS_SEMANA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

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

# Techo editorial de una edición (palabras de lectura, sin el cierre).
LARGO_MAXIMO = 1500

# Tipos de fuente (campo `tipo` en `fuentes`). Si falta, se deduce del dominio.
TIPOS_FUENTE = {
    "academica": ("Académica", "Académicas"),       # artículos revisados por pares, universidades, preprints
    "oficial": ("Oficial", "Oficiales"),           # Estado, organismos multilaterales, tribunales, leyes
    "datos": ("Datos", "De datos"),                # estadísticas y bases de datos
    "organizacion": ("Organización", "De organizaciones"),  # ONG, centros de pensamiento
    "prensa": ("Prensa", "De prensa"),
    "referencia": ("Referencia", "De referencia"),  # enciclopedias (solo para contexto, nunca para cifras)
}
DOMINIOS_TIPO = [
    ("referencia", r"wikipedia\.org|britannica\.com"),
    ("academica", r"index\.php/[^/]+/article|revistabiomedica|doi\.org|pubmed|ncbi\.nlm|scielo|redalyc|jstor|sciencedirect|springer|wiley|nature\.com|science\.org|"
                  r"thelancet|nejm|bmj|plos|frontiersin|mdpi|arxiv|ssrn|nber\.org|academic\.oup|cambridge\.org|tandfonline|"
                  r"sagepub|\.edu(\.|/|$)|uniandes|unal\.edu|javeriana|researchgate|revistas?\.|journals?\."),
    ("datos", r"dane\.gov|datos\.gov|data\.|ourworldindata|statista|datosmacro"),
    ("oficial", r"\.gov(\.|/|$)|\.gob\.|who\.int|unesco\.org|preventionweb|undrr|paho\.org|worldbank|imf\.org|cepal|un\.org|unicef|undp|oecd|"
                "europa\.eu|banrep|minhacienda|minsalud|ideam|corteconstitucional|jep\.gov|senado|camara\.gov|"
                "funcionpublica|ins\.gov"),
    ("organizacion", r"dejusticia|fedesarrollo|ideaspaz|crisisgroup|brookings|cepr|oxfam|msf\.org|medicosinfronteras|"
                     r"gavi\.org|cepi\.net|ashden|addiopizzo|hrw\.org|amnesty|\.org(/|$)"),
]


def tipo_por_url(url):
    for tipo, patron in DOMINIOS_TIPO:
        if re.search(patron, url, re.I):
            return tipo
    return "prensa"


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


def fecha_con_dia(iso):
    """"jueves 24 de septiembre de 2026"."""
    return f"{DIAS_SEMANA[date.fromisoformat(iso).weekday()]} {fecha_legible(iso)}"


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
         # "nudo"; "friccion" es el nombre anterior y se sigue aceptando.
         "nudo": _texto(a.get("nudo", a.get("friccion")), f"actualizaciones[{i}].nudo", requerido=False)}
        for i, a in enumerate(_lista_mapas(meta.get("actualizaciones"), "actualizaciones",
                                           ["fecha", "nudo", "friccion", "texto"]), 1)]
    datos["correcciones"] = [
        {"fecha": _fecha(c.get("fecha"), f"correcciones[{i}].fecha"),
         "texto": _texto(c.get("texto"), f"correcciones[{i}].texto")}
        for i, c in enumerate(_lista_mapas(meta.get("correcciones"), "correcciones",
                                           ["fecha", "texto"]), 1)]
    fuentes = []
    for i, f in enumerate(_lista_mapas(meta.get("fuentes"), "fuentes", ["titulo", "medio", "url", "tipo"]), 1):
        url = _texto(f.get("url"), f"fuentes[{i}].url")
        if not re.match(r"^https?://\S+$", url):
            raise ErrorEdicion(f"fuentes[{i}].url: «{url}» no es una url http(s) válida")
        tipo = _texto(f.get("tipo"), f"fuentes[{i}].tipo", requerido=False)
        if tipo and tipo not in TIPOS_FUENTE:
            raise ErrorEdicion(f"fuentes[{i}].tipo: «{tipo}» no existe (válidos: {', '.join(TIPOS_FUENTE)})")
        fuentes.append({"titulo": _texto(f.get("titulo"), f"fuentes[{i}].titulo"),
                        "medio": _texto(f.get("medio"), f"fuentes[{i}].medio", requerido=False),
                        "url": url, "tipo": tipo or tipo_por_url(url)})
    datos["fuentes"] = fuentes
    return datos


# --- Marcado del cuerpo -------------------------------------------------------

RE_HEADING = re.compile(r"<h([1-6])([^>]*)>(.*?)</h\1>", re.S)


def clases_heading(nivel, texto):
    t = texto.lower()
    if nivel == 2:
        if "para conversar" in t:
            return ["carril", "conversar"]
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
    """<h2> abre un carril (<section>) y <h3> un nudo (<article id=slug>).

    Cada bloque va hasta el siguiente título de nivel igual o superior. Deja
    marcas <!--fin:slug--> al cierre de cada nudo (para sus
    actualizaciones) y <!--antes-glosario--> antes del glosario (para las
    fuentes). Devuelve (html, slugs_de_nudos).
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
                ancla = {"conversar": ' id="para-conversar"'}
                extra = next((ancla[c] for c in clases if c in ancla), "")
                salida.append(f'<section class="{" ".join(clases)}"{extra}>\n')
            # "Carril 1: Radar" → "Radar", con una línea que explica el carril.
            heading = re.sub(r"(<h2[^>]*>)\s*Carril\s+\d+\s*:\s*", r"\1", heading, flags=re.I)
            pila.append((nivel, "section", None))
        elif nivel == 3 and clases:
            # Slug explícito con {#slug} (attr_list) o derivado del título sin número.
            m_id = re.search(r'\sid="([^"]+)"', attrs)
            slug = m_id.group(1) if m_id else slugificar(re.sub(r"^\s*\d+\.\s*", "", texto))
            if m_id:
                heading = heading.replace(m_id.group(0), "", 1)
            heading = re.sub(r"(<h3[^>]*>)\s*\d+\.\s*", r"\1", heading, count=1)
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
    try:
        cuerpo_md, figuras = graficos.extraer(cuerpo_md)
    except graficos.ErrorGrafico as err:
        raise ErrorEdicion(str(err))
    cuerpo = convertir(cuerpo_md).strip()

    # El "# Radar · fecha" del cuerpo se omite: la cabecera sale del frontmatter.
    e["antetitulo"] = ""
    m = re.match(r"<h1[^>]*>(.*?)</h1>\s*", cuerpo, re.S)
    if m:
        e["antetitulo"] = texto_plano(m.group(1)).strip()
        cuerpo = cuerpo[m.end():]

    cuerpo, e["nudos"] = envolver_secciones(cuerpo)
    # Títulos de los nudos (sin número ni lugares) para la descripción.
    e["indice_nudos"] = [
        (slug, re.sub(r"\s*\([^)]*\)\s*$", "", re.sub(r"^\s*\d+\.\s*", "", texto_plano(t))).strip())
        for slug, t in re.findall(
            r'<article class="item(?! seguimiento)[^"]*" id="([^"]+)">\s*<h3[^>]*>(.*?)</h3>', cuerpo, re.S)]
    e["titulos_nudos"] = [t for _, t in e["indice_nudos"]]
    # Tiempo de lectura: ~200 palabras por minuto, sin contar descartes,
    # glosario ni nota metodológica (van al cierre y son de consulta).
    lectura = re.split(r'<section class="carril cierre"', cuerpo)[0]
    e["palabras"] = len(texto_plano(lectura).split())
    e["minutos"] = max(1, round(e["palabras"] / 200))
    e["cuerpo"] = graficos.insertar(marcar_bloques(cuerpo), figuras)
    e["cuerpo"], e["cruces"] = sacar_cruces(e["cuerpo"], dict(e["indice_nudos"]))
    e["glosario"] = extraer_glosario(e["cuerpo"])

    for i, a in enumerate(e["actualizaciones"], 1):
        if a["nudo"] and a["nudo"] not in e["nudos"]:
            raise ErrorEdicion(
                f"actualizaciones[{i}].nudo: «{a['nudo']}» no es un nudo de esta "
                f"edición (disponibles: {', '.join(e['nudos']) or 'ninguno'})")
    cambios = [a["fecha"] for a in e["actualizaciones"]] + [c["fecha"] for c in e["correcciones"]]
    e["ultimo_cambio"] = max(cambios) if cambios else ""
    return e


RE_CRUCE = re.compile(r'<p class="con-etiqueta cruce[^"]*">\s*<strong class="etiqueta">[^<]*</strong>\s*(.*?)</p>\n?', re.S)


def sacar_cruces(cuerpo, titulos):
    """El "Cruce con Mattriz" no se muestra en la edición: se guarda para la
    página de Candidatas (con el nudo de donde salió). Los "No hay." se
    descartan."""
    cruces = []
    for m in re.finditer(r'<article class="item[^"]*" id="([^"]+)">(.*?)<!--fin:\1-->', cuerpo, re.S):
        for c in RE_CRUCE.finditer(m.group(2)):
            texto = c.group(1).strip()
            if not re.fullmatch(r"no hay\.?", texto_plano(texto).strip(), re.I):
                cruces.append({"slug": m.group(1), "nudo": titulos.get(m.group(1), ""), "html": texto})
    return RE_CRUCE.sub("", cuerpo), cruces


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


def reunir_hilos(ediciones):
    """Temas con historia: donde se trató por primera vez, sus seguimientos y
    sus actualizaciones, en orden. Solo los que tienen más de una entrada."""
    hilos = {}
    for e in sorted(ediciones, key=lambda o: (o["fecha"], o["orden"])):
        titulos = dict(e["indice_nudos"])
        for slug in e["temas"]:
            if slug not in e["nudos"]:
                continue
            h = hilos.setdefault(slug, {"slug": slug, "titulo": titulos.get(slug, slug.replace("-", " ")),
                                        "entradas": []})
            h["entradas"].append({"fecha": e["fecha"], "tipo": "Primera vez", "e": e,
                                  "href": f"../ediciones/{e['slug']}.html#{slug}"})
            for a in e["actualizaciones"]:
                if a["nudo"] == slug:
                    h["entradas"].append({"fecha": a["fecha"], "tipo": "Actualización", "e": e,
                                          "texto": a["texto"],
                                          "href": f"../ediciones/{e['slug']}.html#{slug}"})
        for slug in e["seguimiento"]:
            if slug in hilos:
                hilos[slug]["entradas"].append({"fecha": e["fecha"], "tipo": "Seguimiento", "e": e,
                                                "href": f"../ediciones/{e['slug']}.html"})
    for h in hilos.values():
        h["entradas"].sort(key=lambda x: (x["fecha"], x["e"]["orden"]))
    return {k: h for k, h in hilos.items() if len(h["entradas"]) > 1}


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
    partes.append(minutos_lectura(e))
    return " · ".join(partes)


def minutos_lectura(e):
    return f"{e['minutos']} min de lectura"


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
    """Fuentes numeradas, cada una con su tipo, y un conteo arriba para ver
    de un vistazo cuánto viene de la academia, del Estado o de la prensa."""
    if not fuentes:
        return ""
    items = []
    for f in fuentes:
        medio = f'<span class="medio">{html.escape(f["medio"])}</span>. ' if f["medio"] else ""
        tipo = TIPOS_FUENTE[f["tipo"]][0]
        items.append(f'<li><span class="tipo-fuente tipo-{f["tipo"]}">{tipo}</span> '
                     f'{medio}<a href="{html.escape(f["url"])}">{html.escape(f["titulo"])}</a></li>')
    conteo = [(t, sum(f["tipo"] == t for f in fuentes)) for t in TIPOS_FUENTE]
    singular = {"academica": "académica", "oficial": "oficial", "datos": "de datos",
                "organizacion": "de una organización", "prensa": "de prensa", "referencia": "de referencia"}
    partes = [f"{n} {TIPOS_FUENTE[t][1].lower() if n != 1 else singular[t]}" for t, n in conteo if n]
    resumen = f'<p class="fuentes-resumen">{len(fuentes)} fuentes: {", ".join(partes)}.</p>'
    return (f'<section class="carril cierre fuentes" id="fuentes">\n<h2>Fuentes</h2>\n{resumen}\n'
            f'<ol>\n{chr(10).join(items)}\n</ol>\n</section>\n')


def html_glosario_flotante(terminos):
    """Glosario fijo a la derecha en pantallas anchas; en móviles, un botón al glosario."""
    if not terminos:
        return ""
    items = "\n".join(f"<dt>{html.escape(t)}</dt><dd>{d}</dd>" for t, d in terminos)
    return f"""<aside class="glosario-flotante" aria-label="Glosario de la edición">
<button type="button" class="cerrar-panel" aria-label="Cerrar el glosario" hidden>×</button>
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
        if a["nudo"]:
            marca = f"<!--fin:{a['nudo']}-->"
            cuerpo = cuerpo.replace(marca, bloque + marca, 1)
        else:
            generales.append(bloque)
    cuerpo = re.sub(r"<!--fin:[^>]*-->\n?", "", cuerpo)
    # Cada "### Seguimiento: …" enlaza a la historia completa del tema (o a la
    # edición donde se trató, si todavía no hay hilo).
    for tema, previas in e.get("seguimiento_enlaces", ()):
        destino = (f"../temas/{tema}.html" if tema in e.get("hilos_todos", ())
                   else f"../ediciones/{previas[-1]['slug']}.html")
        cuerpo = re.sub(rf'(<article class="item seguimiento[^"]*" id="[^"]*{re.escape(tema)}[^"]*">\s*<h3[^>]*>.*?</h3>)',
                        rf'\1\n<p class="hilo-enlace"><a href="{destino}">Ver cómo empezó este tema →</a></p>',
                        cuerpo, count=1, flags=re.S)
    for slug in e.get("hilos", ()):
        cuerpo = re.sub(rf'(<article class="[^"]*" id="{re.escape(slug)}">\s*<h3[^>]*>.*?</h3>)',
                        rf'\1\n<p class="hilo-enlace"><a href="../temas/{slug}.html">Ver todo el tema, '
                        rf'de principio a fin →</a></p>', cuerpo, count=1, flags=re.S)

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
                   '<p class="aviso-nota">Datos corregidos después de publicar; '
                   f'cada corrección lleva su fecha.</p>\n<ol class="correcciones">\n{items}</ol>\n</section>\n')
    return plegar_cierre(cuerpo)


# "Lo que descarté" queda en el markdown (la rutina lo usa para no repetir
# temas) pero no se muestra. Fuentes y nota metodológica van plegadas.
RE_SECCION_CIERRE = re.compile(
    r'<section class="(carril cierre[^"]*)"([^>]*)>\s*(<h2[^>]*>(.*?)</h2>)(.*?)</section>\n?', re.S)


def plegar_cierre(cuerpo):
    def cambiar(m):
        clases, attrs, h2, titulo, resto = m.groups()
        t = texto_plano(titulo).lower()
        if "descart" in t:
            return ""
        if "fuentes" in t or "metodol" in t or "lo que hice" in t or "glosario" in t:
            return (f'<section class="{clases} plegable"{attrs}>\n<details>\n<summary>{h2}</summary>'
                    f'{resto}</details>\n</section>\n')
        return m.group(0)
    return RE_SECCION_CIERRE.sub(cambiar, cuerpo)


def html_menu(raiz, seccion=None):
    """Barra de secciones: Inicio y categorías; la actual va marcada."""
    def item(clave, href, nombre):
        marca = ' aria-current="page"' if clave == seccion else ""
        return f'<li><a href="{href}"{marca}>{html.escape(nombre)}</a></li>'
    items = [item("inicio", f"{raiz}index.html", "Inicio")]
    items += [item(c, f"{raiz}categorias/{c}.html", CATEGORIAS[c]) for c in CATEGORIAS_ACTIVAS]
    items.append(item("sobre", f"{raiz}sobre.html", "¿Qué es esto?"))
    return "<ul>" + "".join(items) + "</ul>"


def recortar(texto, limite):
    """Corta en el último espacio antes del límite y agrega puntos suspensivos."""
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto if len(texto) <= limite else texto[:limite].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def descripcion_edicion(e):
    temas = "; ".join(e["titulos_nudos"])
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
    nota_titulo = html.escape(re.sub(r"\s*·\s*Otra lectura$", "", html.unescape(titulo)))
    abierto = COMENTARIOS_ABIERTOS and bool(TURNSTILE_SITEKEY)
    config = json.dumps({"abierto": abierto, "sitekey": TURNSTILE_SITEKEY if abierto else ""})
    return base.substitute(titulo=titulo, raiz=raiz, contenido=contenido, menu=html_menu(raiz, seccion),
                           nota_pagina=ruta, nota_titulo=nota_titulo, config=config,
                           meta=meta_etiquetas(titulo, descripcion, ruta, tipo, ld))


def recomendar(e, ediciones):
    """Ediciones para leer después: primero las que comparten temas (o les
    hacen seguimiento), luego las de la misma categoría; a igualdad, la
    más cercana en el tiempo, prefiriendo la más nueva."""
    propios = set(e["temas"]) | set(e["seguimiento"])
    def puntaje(o):
        comunes = len(propios & (set(o["temas"]) | set(o["seguimiento"])))
        cats = len(set(e["categorias"]) & set(o["categorias"]))
        dias = abs((date.fromisoformat(o["fecha"]) - date.fromisoformat(e["fecha"])).days)
        mas_nueva = (o["fecha"], o["orden"]) > (e["fecha"], e["orden"])
        return (comunes * 3 + cats, mas_nueva, -dias)
    otras = [o for o in ediciones if o is not e]
    return sorted(otras, key=puntaje, reverse=True)


def html_fin(e, ediciones):
    ultima = e["fecha"] == ediciones[0]["fecha"]
    return f'<p class="fin-edicion">{"Eso es todo por hoy." if ultima else "Eso es todo en esta edición."}</p>'


def html_siguiente(e, ediciones):
    """Cierre de la edición: "Eso es todo", una sola lectura sugerida y el
    camino a los demás temas. Sin listas largas."""
    recomendadas = recomendar(e, ediciones)
    sugerida = ""
    if recomendadas:
        s = recomendadas[0]
        sugerida = f"""<p class="siguiente-rotulo">Siguiente lectura</p>
<a class="siguiente-titulo" href="{s['slug']}.html">{html.escape(s['titulo'])}</a>
<p class="fecha">{fecha_legible(s['fecha'])} · {minutos_lectura(s)}</p>"""
    return f"""<aside class="siguiente" aria-label="Siguiente lectura">
{sugerida}
<p class="otros-temas"><a href="../archivo.html">Ver otros temas →</a></p>
</aside>"""


def pagina_edicion(base, e, ediciones):
    contenido = f"""<article class="edicion">
<header class="cabecera">
<p class="fecha">{linea_fecha(e)}</p>
<h1>{html.escape(e['titulo'])}</h1>
{html_categorias(e['categorias'], '../')}
{aviso_cambios(e)}
{html_atajos(e)}
{HTML_ESCUCHAR}
</header>
{cuerpo_edicion(e)}
</article>
{html_fin(e, ediciones)}
{html_pulso(e)}
{html_glosario_flotante(e['glosario'])}
{html_siguiente(e, ediciones)}"""
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


def html_atajos(e):
    """Índice de la edición: sus temas y la pregunta del final, para orientarse."""
    items = [f'<li><a href="#{slug}">{html.escape(t)}</a></li>' for slug, t in e["indice_nudos"]]
    if 'id="para-conversar"' in e["cuerpo"]:
        items.append('<li><a href="#para-conversar">Para conversar</a></li>')
    if len(items) < 2:
        return ""
    return (f'<nav class="indice-edicion" aria-label="En esta edición"><p>En esta edición</p>'
            f'<ol>{"".join(items)}</ol></nav>')


# Controles para escuchar la edición. Ocultos sin JavaScript o sin voz en el
# navegador; los activa plantilla/base.html.
HTML_ESCUCHAR = """<div class="escuchar" role="group" aria-label="Escuchar la edición" hidden>
<button type="button" class="escuchar-play" aria-pressed="false">Escuchar</button>
<button type="button" class="escuchar-detener" hidden>Detener</button>
<label><span class="escuchar-rotulo">Ritmo</span> <select class="escuchar-velocidad" aria-label="Ritmo de lectura">
<option value="0.9">Pausado</option>
<option value="0.97" selected>Normal</option>
<option value="1.1">Ágil</option>
</select></label>
<label class="escuchar-voces" hidden><span class="escuchar-rotulo">Voz</span> <select class="escuchar-voz" aria-label="Voz"></select></label>
<p class="escuchar-pista" hidden>¿Quiere una voz masculina o más natural? En iPhone: Ajustes → Accesibilidad → Contenido leído → Voces → Español, y descargue Jorge, Juan o Diego (versión «mejorada»). En Android: Ajustes → Texto a voz. En computador, el navegador Edge trae voces naturales como Gonzalo (Colombia) o Jorge (México).</p>
<p class="escuchar-estado" role="status" aria-live="polite"></p>
</div>"""


def html_pulso(e):
    """¿Cómo le quedó esta edición? Liviana / Justa / Pesada. Sin JS es un
    formulario normal; con JS se envía de un toque si ya hay nombre y clave."""
    titulo = html.escape(f"Edición {e['edicion']} · {fecha_legible(e['fecha'])}")
    botones = "".join(f'<button type="submit" name="pulso" value="{v}">{n}</button>'
                      for v, n in [("liviana", "Liviana"), ("justa", "Justa"), ("pesada", "Pesada")])
    return f"""<form class="pulso" method="post" action="/api/ajuste">
<input type="hidden" name="pagina" value="/ediciones/{e['slug']}.html">
<input type="hidden" name="titulo" value="{titulo}">
<fieldset>
<legend>¿Cómo le quedó esta edición?</legend>
<p class="pulso-ayuda">Un toque nos ayuda a calibrar el largo y la carga de las próximas.</p>
<div class="pulso-cred">
<label>Nombre <input name="quien" autocomplete="name"></label>
<label>Clave <input name="clave" type="password" autocomplete="current-password" required></label>
</div>
<div class="pulso-opciones">{botones}</div>
<p class="pulso-estado" role="status" aria-live="polite" hidden></p>
</fieldset>
</form>"""


# Epígrafe de la portada: cita, autor y obra.
EPIGRAFE = {
    "cita": "He procurado con esmero no ridiculizar ni lamentar ni detestar las acciones "
            "humanas, sino entenderlas.",
    "autor": "Baruch Spinoza",
    "obra": "Tratado político",
    "anio": "1677",
}


def por_dia(ediciones):
    """[(fecha, [ediciones de ese día])], del día más reciente al más antiguo."""
    dias = {}
    for e in ediciones:
        dias.setdefault(e["fecha"], []).append(e)
    return sorted(dias.items(), reverse=True)


def html_ediciones_dia(ediciones, raiz):
    """Las ediciones de un día con sus nudos principales."""
    bloques = []
    for e in ediciones:
        href = f"{raiz}ediciones/{e['slug']}.html"
        temas = "".join(f'<li><a href="{href}#{slug}">{html.escape(t)}</a></li>'
                        for slug, t in e["indice_nudos"])
        temas = f'<ul class="dia-temas" aria-label="Temas principales">{temas}</ul>' if temas else ""
        edicion = " · ".join(([f"Edición {html.escape(e['edicion'])}"] if e["edicion"] else [])
                             + [minutos_lectura(e)])
        bloques.append(f"""<li>
<p class="fecha">{edicion}</p>
<a class="dia-titulo" href="{href}">{html.escape(e['titulo'])}</a>
{aviso_cambios(e, raiz)}
{temas}
</li>""")
    return '<ol class="indice dia">\n' + "\n".join(bloques) + "\n</ol>"


def pagina_portada(base, dias):
    """Portada: solo las ediciones del día más reciente y el camino a los anteriores."""
    epigrafe = f"""<header class="cabecera portada">
<h1 class="solo-lectores">Otra lectura</h1>
<figure class="epigrafe">
<blockquote><p>«{html.escape(EPIGRAFE['cita'])}»</p></blockquote>
<figcaption>{html.escape(EPIGRAFE['autor'])} <cite>{html.escape(EPIGRAFE['obra'])}</cite>, {EPIGRAFE['anio']}</figcaption>
</figure>
</header>"""
    if dias:
        fecha, del_dia = dias[0]
        cuerpo = f"""<section class="hoy" aria-labelledby="hoy-titulo">
<h2 id="hoy-titulo" class="dia-fecha"><time datetime="{fecha}">{fecha_con_dia(fecha).capitalize()}</time></h2>
{html_ediciones_dia(del_dia, "")}
</section>"""
        if len(dias) > 1:
            cuerpo += '\n<p class="dias-anteriores"><a href="archivo.html">Días anteriores →</a></p>'
    else:
        cuerpo = '<p class="bajada">Todavía no hay ediciones.</p>'
    ld = {"@type": "WebSite", "name": NOMBRE_SITIO, "description": DESCRIPCION_SITIO,
          "inLanguage": "es-CO"}
    return pagina(base, "Otra lectura", DESCRIPCION_SITIO, "", f"{epigrafe}\n{cuerpo}",
                  "/", "website", ld, seccion="inicio")


def pagina_dia(base, fecha, del_dia, anterior, siguiente):
    """dias/AAAA-MM-DD.html: lo que se publicó ese día."""
    nav = []
    if anterior:
        nav.append(f'<a rel="prev" href="{anterior}.html">← {fecha_legible(anterior)}</a>')
    if siguiente:
        nav.append(f'<a rel="next" href="{siguiente}.html">{fecha_legible(siguiente)} →</a>')
    titulo = fecha_con_dia(fecha).capitalize()
    contenido = f"""<header class="cabecera">
<p class="fecha"><a href="../archivo.html">Días anteriores</a></p>
<h1><time datetime="{fecha}">{titulo}</time></h1>
</header>
{html_ediciones_dia(del_dia, "../")}
<nav class="entre-ediciones" aria-label="Otros días">{''.join(nav)}</nav>"""
    temas = "; ".join(t for e in del_dia for t in e["titulos_nudos"])
    descripcion = f"Otra lectura del {fecha_legible(fecha)}: {temas}." if temas else f"Otra lectura del {fecha_legible(fecha)}."
    return pagina(base, html.escape(f"{titulo} · Otra lectura"), descripcion, "../", contenido,
                  f"/dias/{fecha}.html")


def html_temas_seguidos(hilos):
    if not hilos:
        return ""
    orden = sorted(hilos.values(), key=lambda h: h["entradas"][-1]["fecha"], reverse=True)
    filas = "".join(
        f'<li><a href="temas/{h["slug"]}.html">{html.escape(h["titulo"])}</a> '
        f'<span>{len(h["entradas"])} entradas · última: {fecha_legible(h["entradas"][-1]["fecha"])}</span></li>'
        for h in orden)
    return (f'<section class="temas-seguidos" id="temas">\n<h2>Temas que seguimos</h2>\n'
            f'<ul>{filas}</ul>\n</section>')


def pagina_archivo(base, dias, hilos=None):
    """archivo.html: todos los días, agrupados por mes, con sus temas."""
    meses, bloques = {}, []
    for fecha, del_dia in dias:
        meses.setdefault(fecha[:7], []).append((fecha, del_dia))
    for mes, lista in meses.items():
        anio, m = mes.split("-")
        filas = []
        for fecha, del_dia in lista:
            temas = " · ".join(html.escape(t) for e in del_dia for t in e["titulos_nudos"])
            filas.append(f"""<li>
<a href="dias/{fecha}.html"><time datetime="{fecha}">{fecha_con_dia(fecha).capitalize()}</time></a>
<p class="archivo-temas">{temas}</p>
</li>""")
        bloques.append(f'<section class="archivo-mes">\n<h2>{MESES[int(m) - 1].capitalize()} de {anio}</h2>\n'
                       f'<ol class="archivo-dias">\n{"".join(filas)}\n</ol>\n</section>')
    fechas = [f for f, _ in dias]
    buscador = ""
    if fechas:
        # Sin JavaScript queda la lista; con él, un selector de fecha.
        buscador = f"""<form class="ir-fecha" hidden data-fechas="{' '.join(fechas)}">
<label>Ir a una fecha <input type="date" min="{fechas[-1]}" max="{fechas[0]}" value="{fechas[0]}"></label>
<button type="submit">Ver</button>
<p class="ir-fecha-estado" role="status" aria-live="polite"></p>
</form>
<script>
(function () {{
  var f = document.querySelector(".ir-fecha");
  var hay = f.getAttribute("data-fechas").split(" ");
  var estado = f.querySelector(".ir-fecha-estado");
  f.hidden = false;
  f.addEventListener("submit", function (ev) {{
    ev.preventDefault();
    var v = f.querySelector("input").value;
    if (hay.indexOf(v) >= 0) location.href = "dias/" + v + ".html";
    else estado.textContent = "Ese día no hubo edición. Pruebe con otra fecha de la lista.";
  }});
}})();
</script>"""
    n = len(dias)
    contenido = f"""<header class="cabecera">
<h1>Días anteriores</h1>
<p class="bajada">{n} {"día" if n == 1 else "días"} con edición. Elija una fecha para ver qué se publicó.</p>
</header>
{buscador}
{html_temas_seguidos(hilos or {})}
{"".join(bloques) or "<p>Todavía no hay ediciones.</p>"}"""
    return pagina(base, "Días anteriores · Otra lectura",
                  "Archivo de Otra lectura por fechas: qué temas se trataron cada día.", "",
                  contenido, "/archivo.html", seccion="archivo")


def pagina_hilo(base, h):
    """temas/<slug>.html: la historia de un tema a lo largo de las ediciones."""
    filas = []
    for x in h["entradas"]:
        e = x["e"]
        texto = (convertir_linea(x["texto"]) if x.get("texto")
                 else f'<a href="{x["href"]}">{html.escape(e["titulo"])}</a>')
        filas.append(f"""<li class="hilo-{slugificar(x['tipo'])}">
<p class="fecha"><time datetime="{x['fecha']}">{fecha_legible(x['fecha'])}</time> · {x['tipo']}</p>
<p>{texto}</p>
</li>""")
    contenido = f"""<header class="cabecera">
<p class="fecha"><a href="../archivo.html#temas">Temas que seguimos</a></p>
<h1>{html.escape(h['titulo'])}</h1>
<p class="bajada">Cómo ha evolucionado este tema, de la primera vez que se trató a hoy.</p>
</header>
<ol class="hilo">
{"".join(filas)}
</ol>"""
    return pagina(base, html.escape(f"{h['titulo']} · Otra lectura"),
                  f"{h['titulo']}: la historia completa del tema en Otra lectura.", "../",
                  contenido, f"/temas/{h['slug']}.html")


CATEGORIA_RECIENTES = 6


def pagina_categoria(base, ediciones, clave):
    todas, ediciones = ediciones, ediciones[:CATEGORIA_RECIENTES]
    filas = [f"""<li>
<p class="fecha">{linea_fecha(e)}</p>
<a href="../ediciones/{e['slug']}.html">{html.escape(e['titulo'])}</a>
{aviso_cambios(e, "../")}
</li>""" for e in ediciones]
    titulo = CATEGORIAS[clave]
    n = len(todas)
    bajada = f"{n} edición" if n == 1 else f"{n} ediciones"
    contenido = f"""<header class="cabecera">
<h1>{html.escape(titulo)}</h1>
<p class="bajada">{bajada}</p>
</header>
<ol class="indice" reversed>
{"".join(filas) or "<li>Todavía no hay ediciones.</li>"}
</ol>
{'<p class="dias-anteriores"><a href="../archivo.html">Las anteriores, por fecha →</a></p>' if n > len(ediciones) else ''}"""
    descripcion = f"{titulo}: ediciones de Otra lectura con contexto, soluciones y contrapeso. {bajada}."
    return pagina(base, html.escape(f"{titulo} · Otra lectura"), descripcion, "../", contenido,
                  f"/categorias/{clave}.html", seccion=clave)


def html_cruces(ediciones):
    """Cruces con Mattriz anotados en las ediciones (ya no se muestran en ellas)."""
    filas = []
    for e in ediciones:
        for c in e["cruces"]:
            filas.append(f"""<li>
<p class="origen"><a href="ediciones/{e['slug']}.html#{c['slug']}">{html.escape(c['nudo'] or e['titulo'])}</a> · {enlace_edicion(e, "")}</p>
<p>{c['html']}</p>
</li>""")
    if not filas:
        return ""
    return ('<section class="cruces">\n<h2>Cruces anotados en las ediciones</h2>\n'
            '<p class="candidatas-resumen">Lo que cada noticia sugirió para Mattriz. Queda aquí como archivo; '
            'ya no aparece en las ediciones.</p>\n'
            f'<ol class="cruces-lista">{"".join(filas)}</ol>\n</section>')


def pagina_candidatas(base, candidatas, ediciones=()):
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
{html_cruces(ediciones)}"""
    return pagina(base, "Candidatas · Otra lectura",
                  "Ideas de cruce con Mattriz surgidas en Otra lectura: candidatas, no tareas.",
                  "", contenido, "/candidatas.html")


def pagina_texto(base, origen, destino, titulo, descripcion, seccion=None):
    """Página de texto a partir de un markdown de la raíz (ayuda.md, sobre.md)."""
    cuerpo = convertir(origen.read_text(encoding="utf-8")).strip()
    m = re.match(r"<h1[^>]*>(.*?)</h1>\s*", cuerpo, re.S)
    if m:
        titulo, cuerpo = texto_plano(m.group(1)).strip(), cuerpo[m.end():]
    contenido = f"""<header class="cabecera">
<h1>{html.escape(titulo)}</h1>
</header>
<article class="texto">
{cuerpo}
</article>"""
    return pagina(base, f"{html.escape(titulo)} · Otra lectura", descripcion, "", contenido,
                  f"/{destino}", seccion=seccion)


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

    # Aviso (no detiene el build): el techo editorial es de ~1.500 palabras.
    for e in ediciones:
        if e["palabras"] > LARGO_MAXIMO:
            print(f"  aviso: ediciones/{e['archivo']} tiene ~{e['palabras']} palabras de lectura "
                  f"(techo: {LARGO_MAXIMO}).", file=sys.stderr)

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

    hilos = reunir_hilos(ediciones)
    for e in ediciones:
        e["hilos"] = [slug for slug in hilos if slug in e["nudos"] and slug in e["temas"]]
        e["hilos_todos"] = set(hilos)
    if hilos:
        (SITE / "temas").mkdir()
        for h in hilos.values():
            (SITE / "temas" / f"{h['slug']}.html").write_text(pagina_hilo(base, h), encoding="utf-8")

    for i, e in enumerate(ediciones):
        (SITE / "ediciones" / f"{e['slug']}.html").write_text(
            pagina_edicion(base, e, ediciones), encoding="utf-8")

    dias = por_dia(ediciones)
    (SITE / "index.html").write_text(pagina_portada(base, dias), encoding="utf-8")
    (SITE / "archivo.html").write_text(pagina_archivo(base, dias, hilos), encoding="utf-8")
    (SITE / "dias").mkdir()
    for i, (fecha, del_dia) in enumerate(dias):
        anterior = dias[i + 1][0] if i + 1 < len(dias) else None
        siguiente = dias[i - 1][0] if i > 0 else None
        (SITE / "dias" / f"{fecha}.html").write_text(
            pagina_dia(base, fecha, del_dia, anterior, siguiente), encoding="utf-8")

    (SITE / "categorias").mkdir()
    for c in CATEGORIAS:
        de_categoria = [e for e in ediciones if c in e["categorias"]]
        (SITE / "categorias" / f"{c}.html").write_text(
            pagina_categoria(base, de_categoria, c), encoding="utf-8")

    if SITIO_URL:
        urls = [("/", ediciones[0]["fecha"] if ediciones else "")]
        urls += [(f"/ediciones/{e['slug']}.html", e["ultimo_cambio"] or e["fecha"]) for e in ediciones]
        urls += [(f"/dias/{f}.html", "") for f, _ in dias]
        urls += [(f"/categorias/{c}.html", "") for c in CATEGORIAS_ACTIVAS]
        urls += [("/archivo.html", ""), ("/sobre.html", "")]
        urls += [(f"/temas/{slug}.html", "") for slug in hilos]
        filas = "".join(f"<url><loc>{SITIO_URL}{u}</loc>" + (f"<lastmod>{f}</lastmod>" if f else "")
                        + "</url>\n" for u, f in urls)
        (SITE / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{filas}</urlset>\n',
            encoding="utf-8")

    if AYUDA.exists():
        (SITE / "ayuda.html").write_text(pagina_texto(
            base, AYUDA, "ayuda.html", "Cómo participar",
            "Cómo dejar notas y comentarios en Otra lectura, y cómo leer una edición."), encoding="utf-8")
    if SOBRE.exists():
        (SITE / "sobre.html").write_text(pagina_texto(
            base, SOBRE, "sobre.html", "¿Qué es esto?",
            "Otra lectura: un sitio para entender temas de actualidad y de alto impacto, con "
            "contexto, historia, soluciones y contrapeso.", seccion="sobre"), encoding="utf-8")

    candidatas = reunir_candidatas(ediciones, estados)
    (SITE / "candidatas.html").write_text(pagina_candidatas(base, candidatas, ediciones), encoding="utf-8")

    print(f"{len(ediciones)} ediciones, {len(candidatas)} candidatas → {SITE.relative_to(RAIZ)}/"
          + ("" if INDEXAR else " (sin indexación)"))


if __name__ == "__main__":
    main()
