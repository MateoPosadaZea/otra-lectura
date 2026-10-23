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
from datetime import date, timedelta
from pathlib import Path
from string import Template

import markdown

sys.path.insert(0, str(Path(__file__).resolve().parent))
from frontmatter import ErrorFrontmatter, parsear  # noqa: E402
import graficos  # noqa: E402
import recorridos  # noqa: E402
import og  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
EDICIONES = RAIZ / "ediciones"
PLANTILLA = RAIZ / "plantilla"
SITE = RAIZ / "site"
IMAGENES = RAIZ / "imagenes"
CANDIDATAS = RAIZ / "candidatas.md"
AYUDA = RAIZ / "ayuda.md"
SOBRE = RAIZ / "sobre.md"

# Dirección pública del sitio, sin barra final (p. ej. "https://otra-lectura.xxx.workers.dev").
# Hace falta para las vistas previas al compartir (og:image y og:url deben ser
# absolutas), la url canónica y el sitemap. Vacía, esas etiquetas se omiten.
SITIO_URL = "https://otralectura.co"

NOMBRE_SITIO = "Otra lectura"
FRASE_SITIO = "Apostando por una ciudadanía informada."
# Rastreadores de buscadores con IA y asistentes, permitidos explícitamente.
BOTS_IA = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot",
           "Claude-User", "PerplexityBot", "Google-Extended", "Applebot-Extended",
           "CCBot", "Bingbot"]


def editor_ld():
    """La organización que publica, con su logo, para los datos estructurados."""
    org = {"@type": "Organization", "name": NOMBRE_SITIO}
    if SITIO_URL:
        org["url"] = SITIO_URL + "/"
        org["logo"] = {"@type": "ImageObject", "url": f"{SITIO_URL}/icono-512.png", "width": 512, "height": 512}
    return org


DESCRIPCION_SITIO = (
    "Otra manera de leer noticias, con contexto, soluciones y contrapeso. Cada "
    "día, los problemas que se repiten en Colombia, América Latina "
    "y el mundo, con su contexto histórico, las soluciones que ya funcionan en "
    "otros lugares y sus críticas.")

# Mientras el proyecto está en calibración, el sitio pide no ser indexado
# (robots.txt con Disallow total y meta noindex). Para abrirlo a buscadores,
# basta con cambiar esto a True y volver a publicar.
INDEXAR = True

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
#   ciencia     → ciencia, descubrimientos, investigación, espacio
#   tecnologia  → tecnología, inteligencia artificial, internet, energía nueva
#   deporte     → historias e hitos del deporte, más allá de los resultados
# (Tecnología y Deporte desde el 2026-10-23; una categoría aparece en el menú
# cuando tiene al menos una edición.)
CATEGORIAS = {
    "economia": "Economía",
    "salud": "Salud",
    "ambiente": "Ambiente",
    "sociedad": "Sociedad",
    "ciencia": "Ciencia",
    "tecnologia": "Tecnología",
    "deporte": "Deporte",
}

# Explicación corta bajo la banda de cada carril (el markdown dice "Carril 1: Radar";
# en pantalla se muestra solo "Radar").
BAJADA_CARRIL = {
    "carril-asombro": "Hallazgos e historias que amplían la mirada, aunque no sirvan para nada inmediato.",
}

# Categorías con al menos una edición; las llena main() para el menú.
CATEGORIAS_ACTIVAS = []

ESTADOS_CANDIDATA = ["pendiente", "evaluada", "descartada", "activa"]

# Por qué puerta entró el tema (prompt.md, «Qué entra al Radar»). Opcional:
# las ediciones anteriores al 2026-10-22 no lo llevan.
PUERTAS = ["nudo", "avance", "fondo"]

CAMPOS_LISTA = ["temas", "categorias", "lugares", "cruce_mattriz", "seguimiento"]
CAMPOS_CONOCIDOS = {"fecha", "edicion", "titulo", "slug", "nota",
                    "actualizaciones", "correcciones", "fuentes", "decisiones", "grabado", "puerta", "viene",
                    *CAMPOS_LISTA}

# Seguimiento de decisiones (campo `decisiones`): quién decide qué y para
# cuándo, y en qué quedó. El estado lo actualiza la rutina cuando hay noticia.
ESTADOS_DECISION = {
    "pendiente": "Pendiente",
    "tomada": "Se tomó",
    "aplazada": "Aplazada",
    "sin_decision": "Nadie la tomó",
}

# Techo editorial de una edición (palabras de lectura, sin el cierre).
LARGO_MAXIMO = 1200
# Desde el 2026-10-24 (pedido de Mateo: «en Colombia no se lee mucho… que no
# se canse»), las ediciones son más cortas: unas 750 palabras visibles (sin
# lo plegado) y titulares de máximo unas 12 palabras.
FORMATO_CORTO_DESDE = "2026-10-24"
LARGO_MAXIMO_CORTO = 750
TITULO_MAXIMO_PALABRAS = 14

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
    (re.compile(r"el dato curioso", re.I), "curioso"),
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
        "puerta": _texto(meta.get("puerta"), "puerta", requerido=False),
    }
    if datos["puerta"] and datos["puerta"] not in PUERTAS:
        raise ErrorEdicion(f"puerta: «{datos['puerta']}» no existe (válidas: {', '.join(PUERTAS)})")
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
    grabados = []
    for i, g in enumerate(_lista_mapas(meta.get("grabado"), "grabado",
                                       ["archivo", "pie", "credito", "url", "alt"]), 1):
        archivo = _texto(g.get("archivo"), f"grabado[{i}].archivo")
        if not (IMAGENES / archivo).is_file():
            raise ErrorEdicion(f"grabado[{i}].archivo: no existe imagenes/{archivo}")
        url = _texto(g.get("url"), f"grabado[{i}].url")
        if not re.match(r"^https?://\S+$", url):
            raise ErrorEdicion(f"grabado[{i}].url: «{url}» no es una url http(s) válida")
        grabados.append({"archivo": archivo, "url": url,
                         "pie": _texto(g.get("pie"), f"grabado[{i}].pie"),
                         "credito": _texto(g.get("credito"), f"grabado[{i}].credito"),
                         "alt": _texto(g.get("alt"), f"grabado[{i}].alt")})
    datos["grabado"] = grabados[0] if grabados else None
    decisiones = []
    for i, d in enumerate(_lista_mapas(meta.get("decisiones"), "decisiones",
                                       ["nudo", "quien", "que", "plazo", "estado", "nota", "revisada",
                                        "prometido_desde", "incumplidos"]), 1):
        estado = _texto(d.get("estado"), f"decisiones[{i}].estado", requerido=False) or "pendiente"
        if estado not in ESTADOS_DECISION:
            raise ErrorEdicion(f"decisiones[{i}].estado: «{estado}» no existe "
                               f"(válidos: {', '.join(ESTADOS_DECISION)})")
        decisiones.append({
            "nudo": _texto(d.get("nudo"), f"decisiones[{i}].nudo", requerido=False),
            "quien": _texto(d.get("quien"), f"decisiones[{i}].quien"),
            "que": _texto(d.get("que"), f"decisiones[{i}].que"),
            "plazo": _fecha(d.get("plazo"), f"decisiones[{i}].plazo") if d.get("plazo") else "",
            "estado": estado,
            "nota": _texto(d.get("nota"), f"decisiones[{i}].nota", requerido=False),
            "revisada": _fecha(d.get("revisada"), f"decisiones[{i}].revisada") if d.get("revisada") else "",
            "prometido_desde": (_fecha(d.get("prometido_desde"), f"decisiones[{i}].prometido_desde")
                                if d.get("prometido_desde") else ""),
            "incumplidos": _entero_no_negativo(d.get("incumplidos"), f"decisiones[{i}].incumplidos"),
        })
    datos["decisiones"] = decisiones
    # Fechas que vienen y no son decisiones (una campaña, un lanzamiento, un
    # evento científico o deportivo): van al recuadro «Lo que viene».
    datos["viene"] = [
        {"fecha": _fecha(v.get("fecha"), f"viene[{i}].fecha"),
         "que": _texto(v.get("que"), f"viene[{i}].que"),
         "quien": _texto(v.get("quien"), f"viene[{i}].quien", requerido=False)}
        for i, v in enumerate(_lista_mapas(meta.get("viene"), "viene", ["fecha", "que", "quien"]), 1)]
    return datos


def _entero_no_negativo(valor, campo):
    if valor in (None, ""):
        return 0
    try:
        n = int(str(valor).strip())
    except ValueError:
        raise ErrorEdicion(f"{campo}: «{valor}» debe ser un número entero")
    if n < 0:
        raise ErrorEdicion(f"{campo}: no puede ser negativo")
    return n


# --- Marcado del cuerpo -------------------------------------------------------

RE_HEADING = re.compile(r"<h([1-6])([^>]*)>(.*?)</h\1>", re.S)


def clases_heading(nivel, texto):
    t = texto.lower()
    if nivel == 2:
        if "para conversar" in t:
            return ["carril", "conversar"]
        if "qué hacer con esto" in t or "que hacer con esto" in t:
            return ["carril", "hacer"]
        if "quién decide" in t or "quien decide" in t:
            return ["carril", "decide"]
        if "dos lecturas" in t:
            return ["carril", "lecturas"]
        if "paradoja" in t:
            return ["carril", "paradoja"]
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
                ancla = {"conversar": ' id="para-conversar"', "decide": ' id="quien-decide"'}
                extra = next((ancla[c] for c in clases if c in ancla), "")
                salida.append(f'<section class="{" ".join(clases)}"{extra}>\n')
            # "Carril 1: Radar" → "Radar", con una línea que explica el carril.
            heading = re.sub(r"(<h2[^>]*>)\s*Carril\s+\d+\s*:\s*", r"\1", heading, flags=re.I)
            # El Radar no lleva banda de título: los nudos abren la edición directamente.
            if "carril-radar" in clases:
                heading = ""
            pila.append((nivel, "section", None))
        elif nivel == 3 and clases:
            # Slug explícito con {#slug} (attr_list) o derivado del título sin número.
            m_id = re.search(r'\sid="([^"]+)"', attrs)
            slug = m_id.group(1) if m_id else slugificar(re.sub(r"^\s*\d+\.\s*", "", texto))
            if m_id:
                heading = heading.replace(m_id.group(0), "", 1)
            heading = re.sub(r"(<h3[^>]*>)\s*\d+\.\s*", r"\1", heading, count=1)
            # Sin el paréntesis de lugares "(Colombia → Países Bajos)": el texto lo explica.
            heading = re.sub(r"\s*\([^()]*→[^()]*\)\s*(</h3>)", r"\1", heading)
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
    # Un rótulo termina en punto, dos puntos o, desde el 2026-10-23, en
    # signo de pregunta («¿Por qué pasa?», «¿Alguien lo ha resuelto?»).
    if e and texto_plano(e.group(1)).rstrip().endswith((".", ":", "?")):
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
    try:
        cuerpo_md, historias = recorridos.extraer(cuerpo_md)
    except recorridos.ErrorRecorrido as err:
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
    # Dos lecturas y la paradoja van plegadas: no cuentan en el largo.
    lectura = re.sub(r'<section class="carril (?:lecturas|paradoja)[^"]*".*?</section>', "", lectura, flags=re.S)
    e["palabras"] = len(texto_plano(lectura).split())
    e["minutos"] = max(1, round(e["palabras"] / 200))
    e["cuerpo"] = bajar_conexion(subir_que_hacer(recorridos.insertar(
        graficos.insertar(marcar_bloques(cuerpo), figuras), historias)))
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
    return (f'<section class="carril cierre fuentes" id="fuentes">\n<h2>¿Le interesa ver las fuentes?</h2>\n{resumen}\n'
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

    if e["decisiones"]:
        items = "".join(html_decision(d) for d in e["decisiones"])
        bloque = (f'<div class="decision-seguimiento"><p class="decision-rotulo">Seguimiento de la decisión</p>'
                  f'<ul class="decisiones">{items}</ul>'
                  f'<p class="decision-mas"><a href="../decisiones.html">Ver todas las decisiones en seguimiento →</a></p></div>\n')
        cuerpo, n = re.subn(r'(<section class="carril decide"[^>]*>.*?)(</section>)',
                            lambda m: m.group(1) + bloque + m.group(2), cuerpo, count=1, flags=re.S)
        if not n:
            cuerpo += f'<section class="carril decide" id="quien-decide">{bloque}</section>\n'
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


# Todas las secciones plegadas se ven igual (2026-10-23, pedido de Mateo:
# «si son botones, que se vean iguales todos»): el título y, debajo, una
# pista corta de qué hay adentro, para que se entienda antes de abrir.
PISTAS_PLEGABLE = [
    ("dos lecturas", "Las dos posturas sobre el tema, en su mejor versión"),
    ("paradoja", "Lo más absurdo de la edición, en dos líneas"),
    ("para leer más", "Libros para seguir con el tema"),
    ("para leer mas", "Libros para seguir con el tema"),
    ("fuentes", "Todos los documentos y datos que usamos"),
    ("glosario", "Las palabras técnicas, explicadas"),
    ("metodol", "Cómo se hizo esta edición y qué no pudimos verificar"),
    ("lo que hic", "Cómo se hizo esta edición y qué no pudimos verificar"),
]


def resumen_plegable(h2, titulo):
    t = texto_plano(titulo).lower()
    pista = next((p for clave, p in PISTAS_PLEGABLE if clave in t), "")
    return (f'<summary>{h2}' + (f'<span class="plegable-pista">{pista}</span>' if pista else "")
            + '<span class="plegable-signo" aria-hidden="true"></span></summary>')


def plegar_cierre(cuerpo):
    def cambiar(m):
        clases, attrs, h2, titulo, resto = m.groups()
        t = texto_plano(titulo).lower()
        if "descart" in t:
            return ""
        if ("fuentes" in t or "metodol" in t or "lo que hice" in t or "lo que hicimos" in t
                or "glosario" in t or "para leer más" in t or "para leer mas" in t):
            return (f'<section class="{clases} plegable"{attrs}>\n<details>\n{resumen_plegable(h2, titulo)}'
                    f'{resto}</details>\n</section>\n')
        return m.group(0)
    # Para que la edición no canse (2026-10-23): Dos lecturas y la paradoja
    # quedan plegadas, para quien quiera más; se abren con un toque.
    cuerpo = RE_SECCION_EXTRA.sub(
        lambda m: (f'<section class="{m.group(1)} plegable plegable-extra"{m.group(2)}>\n<details>\n'
                   f'{resumen_plegable(m.group(3), m.group(4))}'
                   f'<div class="plegable-contenido">{m.group(5)}</div></details>\n</section>\n'), cuerpo)
    return RE_SECCION_CIERRE.sub(cambiar, cuerpo)


RE_SECCION_EXTRA = re.compile(
    r'<section class="(carril (?:lecturas|paradoja)[^"]*)"([^>]*)>\s*(<h2[^>]*>(.*?)</h2>)(.*?)</section>\n?', re.S)


def html_menu(raiz, seccion=None):
    """Barra de secciones: Inicio y categorías; la actual va marcada."""
    def item(clave, href, nombre):
        marca = ' aria-current="page"' if clave == seccion else ""
        return f'<li><a href="{href}"{marca}>{html.escape(nombre)}</a></li>'
    items = [item("inicio", f"{raiz}index.html", "Inicio")]
    items += [item(c, f"{raiz}categorias/{c}.html", CATEGORIAS[c]) for c in CATEGORIAS_ACTIVAS]
    items.append(item("buscar", f"{raiz}buscar.html", "Buscar"))
    items.append(item("sobre", f"{raiz}sobre.html", "¿Qué es esto?"))
    return "<ul>" + "".join(items) + "</ul>"


def recortar(texto, limite):
    """Corta en el último espacio antes del límite y agrega puntos suspensivos."""
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto if len(texto) <= limite else texto[:limite].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def rss(ediciones):
    """RSS 2.0 con las 20 ediciones más recientes (salen a las 5 a. m. de Colombia)."""
    from email.utils import format_datetime
    from datetime import datetime, timedelta, timezone
    bogota = timezone(timedelta(hours=-5))
    def fecha_rss(f):
        return format_datetime(datetime.fromisoformat(f).replace(hour=5, tzinfo=bogota))
    items = []
    for e in ediciones[:20]:
        url = f"{SITIO_URL}/ediciones/{e['slug']}.html"
        items.append(f"<item><title>{html.escape(e['titulo'])}</title><link>{url}</link>"
                     f"<guid isPermaLink=\"true\">{url}</guid><pubDate>{fecha_rss(e['fecha'])}</pubDate>"
                     f"<description>{html.escape(descripcion_edicion(e))}</description></item>")
    ultima = fecha_rss(ediciones[0]["fecha"]) if ediciones else ""
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" '
            'xmlns:atom="http://www.w3.org/2005/Atom"><channel>'
            f"<title>{NOMBRE_SITIO}</title><link>{SITIO_URL}/</link>"
            f"<description>{html.escape(DESCRIPCION_SITIO)}</description><language>es-co</language>"
            f'<atom:link href="{SITIO_URL}/feed.xml" rel="self" type="application/rss+xml"/>'
            f"<lastBuildDate>{ultima}</lastBuildDate>" + "".join(items) + "</channel></rss>\n")


def llms_txt(ediciones, hilos):
    """Guía para asistentes de IA (formato llms.txt): qué es el sitio y dónde está cada cosa."""
    lineas = [f"# {NOMBRE_SITIO}", "", f"> {DESCRIPCION_SITIO}", "",
              "Sitio colombiano en español. Cada día explica un problema que se repite (un «nudo»): "
              "qué pasó, por qué se repite, quién lo está resolviendo, el contrapeso y la historia. "
              "Toda cifra tiene su fuente al final de cada edición; lo no verificado se marca así; "
              "los errores se corrigen con una nota visible y fechada. Al citar, enlace la edición.", "",
              "## Sobre el sitio", "",
              f"- [¿Qué es esto?]({SITIO_URL}/sobre.html): propósito, método y en qué se puede confiar",
              f"- [Días anteriores]({SITIO_URL}/archivo.html): todas las ediciones por fecha",
              f"- [Decisiones]({SITIO_URL}/decisiones.html): decisiones públicas pendientes que seguimos",
              f"- [RSS]({SITIO_URL}/feed.xml)", "", "## Ediciones", ""]
    for e in ediciones:
        nudos = [t for t in e["titulos_nudos"] if t.lower() not in e["titulo"].lower()]
        lineas.append(f"- [{e['titulo']}]({SITIO_URL}/ediciones/{e['slug']}.html): "
                      f"{fecha_legible(e['fecha'])}." + (f" Temas: {'; '.join(nudos)}." if nudos else ""))
    if hilos:
        lineas += ["", "## Temas que seguimos", ""]
        lineas += [f"- [{h['titulo']}]({SITIO_URL}/temas/{h['slug']}.html)" for h in hilos.values()]
    return "\n".join(lineas) + "\n"


def descripcion_edicion(e):
    temas = "; ".join(e["titulos_nudos"])
    inicio = f"Edición {e['edicion']}, {fecha_legible(e['fecha'])}"
    cuerpo = f"{inicio}: {temas}." if temas else f"{inicio}: {e['titulo']}."
    return f"{cuerpo} Contexto, soluciones y contrapeso."


def meta_etiquetas(titulo, descripcion, ruta, tipo, ld, imagen="og.png", alt=None):
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
         '<meta name="theme-color" content="#efe7d6" media="(prefers-color-scheme: light)">',
         '<meta name="theme-color" content="#181512" media="(prefers-color-scheme: dark)">']
    if not INDEXAR:
        m.append('<meta name="robots" content="noindex, nofollow">')
    if SITIO_URL:
        url = SITIO_URL + ruta
        m += [f'<link rel="canonical" href="{url}">',
              f'<meta property="og:url" content="{url}">',
              f'<meta property="og:image" content="{SITIO_URL}/{imagen}">',
              '<meta property="og:image:width" content="1200">',
              '<meta property="og:image:height" content="630">',
              f'<meta property="og:image:alt" content="{html.escape(alt or NOMBRE_SITIO + ": apostando por una ciudadanía informada")}">',
              f'<meta name="twitter:image" content="{SITIO_URL}/{imagen}">']
        ld = {**ld, "url": url}
        ld.setdefault("image", f"{SITIO_URL}/{imagen}")
        if ld.get("@type") == "NewsArticle":
            ld.setdefault("mainEntityOfPage", url)
    # "<\/" evita que un "</script>" dentro de los datos cierre el bloque.
    datos = json.dumps({"@context": "https://schema.org", **ld}, ensure_ascii=False).replace("</", "<\\/")
    m.append(f'<script type="application/ld+json">{datos}</script>')
    return "\n".join(m)


def imagen_compartir(ruta, titulo, rotulo="", pie="UNA EDICIÓN CADA MAÑANA", bajada=""):
    """Genera la imagen para compartir de una página y devuelve su ruta en el
    sitio; si no se puede (sin Pillow), la imagen fija og.png."""
    if ruta in ("/", "/index.html"):
        return "og.png"
    nombre = "og" + ruta[:-len(".html")] + ".png" if ruta.endswith(".html") else "og.png"
    if nombre != "og.png" and og.generar(SITE / nombre, titulo, rotulo, pie, bajada):
        return nombre
    return "og.png"


def pagina(base, titulo, descripcion, raiz, contenido, ruta, tipo="website", ld=None, seccion=None, compartir=None):
    ld = ld or {"@type": "WebPage", "name": html.unescape(titulo), "description": descripcion,
                "inLanguage": "es-CO", "isPartOf": {"@type": "WebSite", "name": NOMBRE_SITIO}}
    nota_titulo = html.escape(re.sub(r"\s*·\s*Otra lectura$", "", html.unescape(titulo)))
    abierto = COMENTARIOS_ABIERTOS and bool(TURNSTILE_SITEKEY)
    config = json.dumps({"abierto": abierto, "sitekey": TURNSTILE_SITEKEY if abierto else ""})
    volver = "" if ruta in ("/", "index.html") else (
        f'<a class="volver" href="{raiz}index.html"><span aria-hidden="true">←</span> Inicio</a>')
    return base.substitute(titulo=titulo, raiz=raiz, contenido=contenido, menu=html_menu(raiz, seccion), volver=volver,
                           nota_pagina=ruta, nota_titulo=nota_titulo, config=config,
                           meta=meta_etiquetas(titulo, descripcion, ruta, tipo, ld, *compartir_de(ruta, nota_titulo, compartir, descripcion)))


def compartir_de(ruta, nota_titulo, compartir, descripcion=""):
    """(imagen, alt): `compartir` = (título, rótulo, pie); si falta, el título
    de la página con su descripción debajo."""
    if compartir:
        titulo, rotulo, pie = compartir
        return imagen_compartir(ruta, titulo, rotulo, pie), titulo
    titulo = html.unescape(nota_titulo)
    return imagen_compartir(ruta, titulo, "", "UNA EDICIÓN CADA MAÑANA", recortar(descripcion, 110)), titulo


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


def relacionada(e, ediciones):
    """La edición más afín que comparta tema o seguimiento con esta, o None.
    Solo se sugiere una lectura si de verdad está relacionada."""
    propios = set(e["temas"]) | set(e["seguimiento"])
    for o in recomendar(e, ediciones):
        if propios & (set(o["temas"]) | set(o["seguimiento"])):
            return o
    return None


def html_siguiente(e, ediciones):
    """Cierre de la edición: si hay una lectura relacionada con el tema, se
    ofrece; si no, «Eso es todo por hoy» y nada más."""
    s = relacionada(e, ediciones)
    if s:
        return f"""<aside class="siguiente" aria-label="Seguir leyendo">
<p class="siguiente-pregunta">¿Le gustaría seguir leyendo? Tenemos esta otra lectura:</p>
<a class="siguiente-titulo" href="{s['slug']}.html">{html.escape(s['titulo'])}</a>
<p class="fecha">{fecha_legible(s['fecha'])} · {minutos_lectura(s)}</p>
</aside>"""
    ultima = e["fecha"] == ediciones[0]["fecha"]
    return f'<p class="fin-edicion">{"Eso es todo por hoy." if ultima else "Eso es todo en esta edición."}</p>'


def pagina_edicion(base, e, ediciones):
    contenido = f"""<article class="edicion">
<header class="cabecera">
<p class="fecha">{linea_fecha(e)}</p>
<h1>{html.escape(e['titulo'])}</h1>
{html_categorias(e['categorias'], '../')}
{aviso_cambios(e)}
{html_grabado(e)}
{html_herramientas(e)}
{html_atajos(e)}
</header>
{cuerpo_edicion(e)}
</article>
{html_glosario_flotante(e['glosario'])}
{html_siguiente(e, ediciones)}"""
    descripcion = descripcion_edicion(e)
    ld = {"@type": "NewsArticle", "headline": e["titulo"], "description": descripcion,
          "datePublished": e["fecha"], "dateModified": e["ultimo_cambio"] or e["fecha"],
          "inLanguage": "es-CO", "articleSection": [CATEGORIAS[c] for c in e["categorias"]],
          "keywords": ", ".join(e["temas"]), "contentLocation": e["lugares"],
          "author": editor_ld(), "publisher": editor_ld(),
          "isPartOf": {"@type": "WebSite", "name": NOMBRE_SITIO},
          "isAccessibleForFree": True}
    if e["fuentes"]:
        ld["citation"] = [f["url"] for f in e["fuentes"]]
    if e["grabado"] and SITIO_URL:
        ld["image"] = [f"{SITIO_URL}/imagenes/{e['grabado']['archivo']}"]
    cats = " · ".join(CATEGORIAS[c] for c in e["categorias"]) or "Otra lectura"
    rotulo = f"Edición {e['edicion']} · {fecha_legible(e['fecha'])}"
    return pagina(base, html.escape(f"{e['titulo']} · Otra lectura"), descripcion, "../",
                  contenido, f"/ediciones/{e['slug']}.html", "article", ld,
                  compartir=(e["titulo"], rotulo, cats))


def html_herramientas(e):
    """Escuchar la edición (voz del propio dispositivo; solo con JavaScript y
    si el navegador la tiene) y enviarla por WhatsApp (un enlace, sin JS)."""
    url = f"{SITIO_URL}/ediciones/{e['slug']}.html" if SITIO_URL else f"ediciones/{e['slug']}.html"
    pocas = entradilla(e)
    texto = f"*{e['titulo']}*\n\n" + (f"{pocas}\n\n" if pocas else "") + f"Léala completa en Otra lectura: {url}"
    from urllib.parse import quote
    wa = "https://wa.me/?text=" + quote(texto, safe="")
    return f"""<div class="herramientas">
<button class="escuchar" type="button" hidden aria-pressed="false"><span aria-hidden="true">▶</span> Escuchar</button>
<button class="escuchar-parar" type="button" hidden>Detener</button>
<a class="whatsapp" href="{html.escape(wa)}" target="_blank" rel="noopener">Enviar por WhatsApp</a>
</div>"""


def html_grabado(e):
    """Grabado de época bajo el título, con pie y crédito (ver RUTINA.md)."""
    g = e["grabado"]
    if not g:
        return ""
    medidas = ""
    try:
        from PIL import Image
        with Image.open(IMAGENES / g["archivo"]) as im:
            medidas = f' width="{im.width}" height="{im.height}"'
    except Exception:
        pass
    return (f'<figure class="grabado"><img src="../imagenes/{html.escape(g["archivo"])}"{medidas} '
            f'alt="{html.escape(g["alt"])}" decoding="async">'
            f'<figcaption>{html.escape(g["pie"])}<br>'
            f'<a href="{html.escape(g["url"])}">{html.escape(g["credito"])}</a></figcaption></figure>')


def html_atajos(e):
    """Índice de la edición: sus temas y la pregunta del final, para orientarse."""
    items = [f'<li><a href="#{slug}">{html.escape(t)}</a></li>' for slug, t in e["indice_nudos"]]
    if 'id="para-conversar"' in e["cuerpo"]:
        items.append('<li><a href="#para-conversar">Para conversar</a></li>')
    if len(items) < 2:
        return ""
    return (f'<nav class="indice-edicion" aria-label="En esta edición"><p>En esta edición</p>'
            f'<ol>{"".join(items)}</ol></nav>')


def por_dia(ediciones):
    """[(fecha, [ediciones de ese día])], del día más reciente al más antiguo."""
    dias = {}
    for e in ediciones:
        dias.setdefault(e["fecha"], []).append(e)
    return sorted(dias.items(), reverse=True)


RE_POCAS = re.compile(r'<strong class="etiqueta">En pocas palabras\.</strong>(.*?)</p>', re.S)


def entradilla(e):
    """El «En pocas palabras» del primer tema: la bajada de la edición en la retícula."""
    m = RE_POCAS.search(e["cuerpo"])
    return recortar(" ".join(texto_plano(m.group(1)).split()), 320) if m else ""


def miniatura_grabado(e, raiz, principal):
    """El grabado de la edición, enlazado, para la retícula del día."""
    g = e["grabado"]
    if not g:
        return ""
    medidas = ""
    try:
        from PIL import Image
        with Image.open(IMAGENES / g["archivo"]) as im:
            medidas = f' width="{im.width}" height="{im.height}"'
    except Exception:
        pass
    carga = "" if principal else ' loading="lazy"'
    return (f'<a class="reticula-imagen" href="{raiz}ediciones/{e["slug"]}.html" tabindex="-1" aria-hidden="true">'
            f'<img src="{raiz}imagenes/{html.escape(g["archivo"])}"{medidas} alt="" decoding="async"{carga}></a>')


def html_ediciones_dia(ediciones, raiz):
    """Las ediciones de un día en retícula de periódico: la primera publicada abre
    a todo el ancho; las demás van en columnas debajo. Si el día tiene un solo
    tema, se ve solo ese."""
    orden = sorted(ediciones, key=lambda o: (o["orden"], o["slug"]))
    bloques = []
    for i, e in enumerate(orden):
        href = f"{raiz}ediciones/{e['slug']}.html"
        temas = ""
        if len(e["indice_nudos"]) > 1:
            temas = "".join(f'<li><a href="{href}#{slug}">{html.escape(t)}</a></li>'
                            for slug, t in e["indice_nudos"])
            temas = f'<ul class="dia-temas" aria-label="Temas principales">{temas}</ul>'
        edicion = " · ".join(([f"Edición {html.escape(e['edicion'])}"] if e["edicion"] else [])
                             + [minutos_lectura(e)])
        bajada = entradilla(e)
        bajada = f'<p class="reticula-bajada">{html.escape(bajada)}</p>' if bajada else ""
        clase = "reticula-principal" if i == 0 else "reticula-columna"
        bloques.append(f"""<li class="{clase}">
{miniatura_grabado(e, raiz, i == 0)}
<p class="fecha">{edicion}</p>
<a class="dia-titulo" href="{href}">{html.escape(e['titulo'])}</a>
{aviso_cambios(e, raiz)}
{bajada}
{temas}
<p class="seguir-leyendo"><a class="boton-seguir" href="{href}">Seguir leyendo<span class="solo-lectores">: {html.escape(e['titulo'])}</span> <span aria-hidden="true">→</span></a></p>
</li>""")
    n = min(len(orden), 3)
    return f'<ol class="indice dia reticula reticula-{n}">\n' + "\n".join(bloques) + "\n</ol>"


def es_repaso(e):
    """Los repasos de la semana resumen otras ediciones: no van en la plana de anteriores."""
    titulo = e["titulo"].lower()
    return e["slug"].endswith("-semana") or titulo.startswith(("la semana", "lo que pasó esta semana"))


def _ante_nota(e):
    """«Sábado 17 de octubre · Economía»: la línea sobre el titular de cada nota."""
    d = date.fromisoformat(e["fecha"])
    fecha = f"{DIAS_SEMANA[d.weekday()]} {d.day} de {MESES[d.month - 1]}"
    seccion = CATEGORIAS.get((e["categorias"] or [""])[0], "")
    return f'<time datetime="{e["fecha"]}">{fecha}</time>' + (f" · {html.escape(seccion)}" if seccion else "")


DECISIONES_EN_RECUADRO = 2


def html_recuadro_decisiones(ediciones, raiz="", cuantas=4):
    """Recuadro en negativo de la primera plana: «Lo que viene», las próximas
    fechas de los temas que hemos contado, la más cercana primero. Mezcla
    decisiones (casi siempre políticas) con otras fechas (campo `viene`):
    si hay de las otras, las decisiones ocupan como máximo dos de cuatro
    puestos (pedido de Mateo, 2026-10-23: «que no solo fuera política»)."""
    hoy = date.today().isoformat()
    decisiones, vistas = [], set()
    for d, e in sorted(((d, e) for e in ediciones for d in e["decisiones"]
                        if d["estado"] == "pendiente" and d["plazo"] and d["plazo"] >= hoy),
                       key=lambda x: (x[0]["plazo"], x[1]["fecha"])):
        clave = (d["plazo"], d["quien"].split()[0])
        if clave in vistas:
            continue
        vistas.add(clave)
        decisiones.append(({"plazo": d["plazo"], "quien": d["quien"], "que": d["que"]}, e))
    otras = sorted((({"plazo": v["fecha"], "quien": v["quien"] or "Para el calendario", "que": v["que"]}, e)
                    for e in ediciones for v in e["viene"] if v["fecha"] >= hoy),
                   key=lambda x: (x[0]["plazo"], x[1]["fecha"]))
    if otras:
        cupo = max(DECISIONES_EN_RECUADRO, cuantas - len(otras))
        proximas = sorted(decisiones[:cupo] + otras[:cuantas - min(cupo, len(decisiones))],
                          key=lambda x: x[0]["plazo"])[:cuantas]
    else:
        proximas = decisiones[:cuantas]
    if not proximas:
        return ""
    items = []
    for d, e in proximas:
        f = date.fromisoformat(d["plazo"])
        items.append(f"""<li><a href="{raiz}ediciones/{e['slug']}.html">
<time datetime="{d['plazo']}"><span class="pp-dia">{f.day}</span> {MESES[f.month - 1][:3]}</time>
<span class="pp-quien">{html.escape(d['quien'])}</span>
<span class="pp-que">{html.escape(recortar(d['que'], 110))}</span>
</a></li>""")
    return f"""<aside class="pp-decide" aria-labelledby="pp-decide-titulo">
<h2 id="pp-decide-titulo">Lo que viene</h2>
<p class="pp-decide-sub">Fechas que vienen en los temas que contamos</p>
<ol>
{chr(10).join(items)}
</ol>
<p class="pp-decide-mas"><a href="{raiz}decisiones.html">Todas las decisiones →</a></p>
</aside>"""


def html_calendario(dias, raiz=""):
    """Calendario de los días con edición, un mes a la vista. Con JavaScript,
    tocar un día muestra sus noticias ahí mismo, en la portada; sin él, el
    enlace lleva a la página del día. Los meses anteriores se abren con
    enlaces a su ancla (:target); por defecto se ve el mes más reciente."""
    titulares = {f: sorted(d, key=lambda o: (o["orden"], o["slug"]))[0]["titulo"] for f, d in dias}
    fechas = sorted(titulares)
    hoy = date.today().isoformat()
    primero, ultimo = date.fromisoformat(fechas[0]), date.fromisoformat(fechas[-1])
    meses, a, m = [], primero.year, primero.month
    while (a, m) <= (ultimo.year, ultimo.month):
        meses.append((a, m))
        a, m = (a + 1, 1) if m == 12 else (a, m + 1)
    bloques = []
    for i, (a, m) in enumerate(meses):
        ident = f"cal-{a}-{m:02d}"
        inicio = date(a, m, 1)
        fin = date(a + 1, 1, 1) if m == 12 else date(a, m + 1, 1)
        celdas = ['<td></td>'] * inicio.weekday()
        d = inicio
        while d < fin:
            f = d.isoformat()
            hoy_attr = ' aria-current="date"' if f == hoy else ""
            if f in titulares:
                celdas.append(f'<td><a href="{raiz}dias/{f}.html" data-dia="{f}" '
                              f'data-fecha="{html.escape(fecha_con_dia(f).capitalize())}" '
                              f'title="{html.escape(titulares[f])}"{hoy_attr}>'
                              f'<span class="solo-lectores">{fecha_con_dia(f)}: </span>{d.day}</a></td>')
            else:
                celdas.append(f'<td><span class="cal-vacio"{hoy_attr}>{d.day}</span></td>')
            d += timedelta(days=1)
        celdas += ['<td></td>'] * (-len(celdas) % 7)
        filas = "".join("<tr>" + "".join(celdas[j:j + 7]) + "</tr>" for j in range(0, len(celdas), 7))
        nav = []
        if i > 0:
            pa, pm = meses[i - 1]
            nav.append(f'<a class="cal-ant" href="#cal-{pa}-{pm:02d}">← {MESES[pm - 1]}</a>')
        if i < len(meses) - 1:
            sa, sm = meses[i + 1]
            nav.append(f'<a class="cal-sig" href="#cal-{sa}-{sm:02d}">{MESES[sm - 1]} →</a>')
        cabeza = "".join(f'<th scope="col"><abbr title="{dia}">{dia[0].upper() if dia != "miércoles" else "X"}</abbr></th>'
                         for dia in DIAS_SEMANA)
        actual = " cal-actual" if i == len(meses) - 1 else ""
        bloques.append(f"""<section class="cal-mes{actual}" id="{ident}" aria-label="{MESES[m - 1]} de {a}">
<p class="cal-titulo">{MESES[m - 1].capitalize()} {a}</p>
<table class="cal-tabla"><thead><tr>{cabeza}</tr></thead><tbody>{filas}</tbody></table>
<p class="cal-nav">{''.join(nav)}</p>
</section>""")
    return f"""<div class="calendario" aria-label="Calendario de ediciones">
<p class="cal-ayuda">Toque un día marcado para ver sus noticias.</p>
{chr(10).join(bloques)}
</div>"""


SECCION_RECIENTES = 4


def html_por_seccion(dias, raiz=""):
    """Una columna por categoría con sus ediciones más recientes: aquí solo
    salud, aquí solo economía. Se ve la variedad y cada cosa en su lugar."""
    todas = [e for _, d in dias for e in sorted(d, key=lambda o: (o["orden"], o["slug"])) if not es_repaso(e)]
    # Cada edición sale una sola vez: en su categoría principal (la primera);
    # una sección con pocas se completa con las que la tienen de segunda.
    elegidas = {c: [e for e in todas if e["categorias"][:1] == [c]][:SECCION_RECIENTES] for c in CATEGORIAS_ACTIVAS}
    vistas = {e["slug"] for l in elegidas.values() for e in l}
    for c in CATEGORIAS_ACTIVAS:
        for e in todas:
            if len(elegidas[c]) >= SECCION_RECIENTES:
                break
            if c in e["categorias"] and e["slug"] not in vistas:
                elegidas[c].append(e)
                vistas.add(e["slug"])
        elegidas[c].sort(key=lambda e: (e["fecha"], e["orden"]), reverse=True)
    columnas = []
    for c in CATEGORIAS_ACTIVAS:
        de_esta = [e for e in todas if c in e["categorias"]]
        if not elegidas[c]:
            continue
        items = []
        for i, e in enumerate(elegidas[c]):
            h = f"{raiz}ediciones/{e['slug']}.html"
            d = date.fromisoformat(e["fecha"])
            imagen = miniatura_grabado(e, raiz, False) if i == 0 else ""
            items.append(f"""<li{' class="sec-primera"' if i == 0 else ''}>
{imagen}<p class="sec-fecha"><time datetime="{e['fecha']}">{d.day} de {MESES[d.month - 1]}</time></p>
<a class="sec-titulo" href="{h}">{html.escape(e['titulo'])}</a>
</li>""")
        n = len(de_esta)
        columnas.append(f"""<section class="sec-col sec-{c}" aria-labelledby="sec-{c}">
<h3 class="sec-nombre" id="sec-{c}"><a href="{raiz}categorias/{c}.html">{html.escape(CATEGORIAS[c])}</a></h3>
<ol class="sec-lista">
{chr(10).join(items)}
</ol>
<p class="sec-mas"><a href="{raiz}categorias/{c}.html">{'La edición' if n == 1 else f'Las {n} ediciones'} de {html.escape(CATEGORIAS[c].lower())} →</a></p>
</section>""")
    if not columnas:
        return ""
    return f"""<h2 class="pp-banda-sec" id="secciones">Por secciones <span>Cada tema en su lugar</span></h2>
<div class="pp-secciones">
{chr(10).join(columnas)}
</div>"""


def html_primera_plana(dias, raiz="", cuantas=12):
    """La portada como la primera plana de un periódico, a todo el ancho: la
    edición del día abre con titular grande, al lado el recuadro de lo que se
    decide, y debajo las notas de días anteriores en columnas con filete. Así
    nada se pierde detrás de un enlace y se llega directo a los titulares."""
    fecha, del_dia = dias[0]
    hoy = sorted(del_dia, key=lambda o: (o["orden"], o["slug"]))
    abre = hoy[0]
    href = f"{raiz}ediciones/{abre['slug']}.html"
    edicion = " · ".join((["Hoy"] + ([f"Edición {html.escape(abre['edicion'])}"] if abre["edicion"] else [])
                          + [minutos_lectura(abre)]))
    bajada = entradilla(abre)
    temas = ""
    if len(abre["indice_nudos"]) > 1:
        temas = "".join(f'<li><a href="{href}#{slug}">{html.escape(t)}</a></li>'
                        for slug, t in abre["indice_nudos"])
        temas = f'<ul class="dia-temas" aria-label="Temas principales">{temas}</ul>'
    largo = " pp-largo" if len(abre["titulo"]) > 90 else ""
    portada = f"""<article class="pp-abre{' pp-con-grabado' if abre['grabado'] else ''}">
<p class="pp-ante">{edicion}</p>
<h2 class="pp-titular{largo}"><a href="{href}">{html.escape(abre['titulo'])}</a></h2>
{miniatura_grabado(abre, raiz, True)}
<div class="pp-cuerpo">
{aviso_cambios(abre, raiz)}
{f'<p class="pp-bajada">{html.escape(bajada)}</p>' if bajada else ''}
{temas}
<p class="seguir-leyendo"><a class="boton-seguir" href="{href}">Seguir leyendo<span class="solo-lectores">: {html.escape(abre['titulo'])}</span> <span aria-hidden="true">→</span></a></p>
</div>
</article>"""
    todas = [e for _, d in dias for e in d]
    recuadro = html_recuadro_decisiones(todas, raiz)

    # Las demás del día y las de días anteriores (sin los repasos de la semana).
    notas_ed = hoy[1:] + [e for _, d in dias[1:]
                          for e in sorted(d, key=lambda o: (o["orden"], o["slug"])) if not es_repaso(e)]
    def nota(e, con_imagen):
        h = f"{raiz}ediciones/{e['slug']}.html"
        b = entradilla(e)
        b = recortar(b, 220) if b else ""
        imagen = miniatura_grabado(e, raiz, False) if con_imagen else ""
        ante = ("Hoy · " if e["fecha"] == fecha else "") + _ante_nota(e)
        return f"""<li class="pp-nota{' pp-con-grabado' if imagen else ''}">
{imagen}<p class="plana-ante">{ante}</p>
<h3 class="plana-titulo"><a href="{h}">{html.escape(e['titulo'])}</a></h3>
<p class="plana-bajada">{html.escape(b)}</p>
<p class="plana-seguir"><a href="{h}">Seguir leyendo<span class="solo-lectores">: {html.escape(e['titulo'])}</span> <span aria-hidden="true">→</span></a></p>
</li>"""

    # Arriba va sola la edición del día (pedido de Mateo, 2026-10-22); las
    # demás van junto al calendario, de la más reciente a la más antigua, en
    # filas que se leen de izquierda a derecha y siempre alineadas: sin
    # grabados, para que todas tengan la misma forma (2026-10-23). Cada día
    # del calendario trae sus notas ya en la página (ocultas) para mostrarlas
    # sin cambiar de página.
    notas = [nota(e, False) for e in notas_ed[:cuantas]]
    por_fecha = "\n".join(
        f'<ol class="pp-notas pp-del-dia" data-dia="{f}" hidden>\n'
        + "\n".join(nota(e, False) for e in sorted(d, key=lambda o: (o["orden"], o["slug"])))
        + "\n</ol>" for f, d in dias)
    anteriores = ""
    if notas:
        anteriores = f"""<h2 class="pp-banda-sec" id="anteriores">Días anteriores <span>Lo que contamos y sigue en pie</span></h2>
<div class="pp-anteriores">
{html_calendario(dias, raiz)}
<div class="pp-lista">
<div class="pp-lista-cabeza" hidden>
<p class="pp-lista-fecha" tabindex="-1"></p>
<button class="pp-lista-volver" type="button">← Volver a lo más reciente</button>
</div>
<ol class="pp-notas pp-recientes">
{chr(10).join(notas)}
</ol>
{por_fecha}
</div>
</div>
<script>
/* Calendario: tocar un día muestra sus noticias aquí mismo, sin cambiar de página. */
(function () {{
  var cal = document.querySelector(".calendario"), lista = document.querySelector(".pp-lista");
  if (!cal || !lista) return;
  var recientes = lista.querySelector(".pp-recientes"), cabeza = lista.querySelector(".pp-lista-cabeza"),
      fecha = cabeza.querySelector(".pp-lista-fecha");
  function mostrar(a) {{
    var dia = a ? a.getAttribute("data-dia") : "";
    lista.querySelectorAll(".pp-del-dia").forEach(function (o) {{ o.hidden = o.getAttribute("data-dia") !== dia; }});
    recientes.hidden = !!dia;
    cabeza.hidden = !dia;
    cal.querySelectorAll("a[data-dia]").forEach(function (x) {{ x.classList.toggle("cal-elegido", x === a); }});
    if (!a) return;
    fecha.textContent = "Noticias del " + a.getAttribute("data-fecha").replace(/^./, function (c) {{ return c.toLowerCase(); }});
    var r = lista.getBoundingClientRect();
    if (r.top < 0 || r.top > innerHeight * 0.5) lista.scrollIntoView({{ behavior: "smooth", block: "start" }});
    fecha.focus({{ preventScroll: true }});
  }}
  cal.addEventListener("click", function (ev) {{
    var a = ev.target.closest("a[data-dia]");
    if (!a) return;
    ev.preventDefault();
    mostrar(a);
  }});
  cabeza.querySelector(".pp-lista-volver").addEventListener("click", function () {{ mostrar(null); }});
}})();
</script>
<p class="dias-anteriores"><a href="{raiz}archivo.html">Todos los días anteriores →</a></p>"""
    numero = f'<span>Edición {html.escape(abre["edicion"])}</span>' if abre["edicion"] else ""
    return f"""<section class="primera" aria-label="Primera plana">
<h1 class="solo-lectores">Otra lectura</h1>
<p class="pp-banda"><time datetime="{fecha}">{fecha_con_dia(fecha).capitalize()}</time>{numero}</p>
<div class="pp-arriba{' pp-sin-recuadro' if not recuadro else ''}">
<div class="pp-principal">
{portada}
</div>
{recuadro}
</div>
{html_por_seccion(dias, raiz)}
{anteriores}
</section>"""


def pagina_portada(base, dias):
    """Portada: directo a los titulares, como la primera plana de un periódico.
    La cita de Spinoza y la explicación del proyecto viven en «¿Qué es esto?»."""
    cuerpo = html_primera_plana(dias) if dias else '<p class="bajada">Todavía no hay ediciones.</p>'
    ld = {"@type": "WebSite", "name": NOMBRE_SITIO, "alternateName": "Otra Lectura",
          "description": DESCRIPCION_SITIO, "slogan": FRASE_SITIO,
          "inLanguage": "es-CO", "publisher": editor_ld()}
    return pagina(base, "Otra lectura", DESCRIPCION_SITIO, "", cuerpo,
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
    principal = del_dia[0]["titulo"] if del_dia else titulo
    return pagina(base, html.escape(f"{titulo} · Otra lectura"), descripcion, "../", contenido,
                  f"/dias/{fecha}.html", compartir=(principal, titulo, "UNA EDICIÓN CADA MAÑANA"))


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


def estado_decision(d, hoy=None):
    """(clase, texto) del estado de una decisión; una pendiente con plazo
    vencido se marca aparte, porque es justo la que hay que vigilar."""
    hoy = hoy or date.today().isoformat()
    if d["estado"] == "pendiente" and d["plazo"] and d["plazo"] < hoy:
        return "vencida", "Venció el plazo sin noticia"
    return d["estado"], ESTADOS_DECISION[d["estado"]]


def html_decision(d, raiz="", e=None):
    clase, texto = estado_decision(d)
    plazo = f' · plazo: <time datetime="{d["plazo"]}">{fecha_legible(d["plazo"])}</time>' if d["plazo"] else " · sin fecha fija"
    nota = f'<p class="decision-nota">{convertir_linea(d["nota"])}</p>' if d["nota"] else ""
    partes = []
    if d.get("prometido_desde"):
        f = d["prometido_desde"]
        partes.append(f'Prometido desde <time datetime="{f}">{MESES[int(f[5:7]) - 1]} de {f[:4]}</time>')
    if d.get("incumplidos"):
        n = d["incumplidos"]
        partes.append(f'{n} plazo{"s" if n != 1 else ""} incumplido{"s" if n != 1 else ""}')
    historial = f'<p class="decision-historial">{" · ".join(partes)}</p>' if partes else ""
    nota = historial + nota
    origen = (f'<p class="decision-origen"><a href="{raiz}ediciones/{e["slug"]}.html">'
              f'{html.escape(e["titulo"])}</a> · {fecha_legible(e["fecha"])}</p>') if e else ""
    return (f'<li class="decision decision-{clase}"><p class="decision-estado">'
            f'<span class="estado">{texto}</span>{plazo}</p>'
            f'<p class="decision-que"><strong>{html.escape(d["quien"])}</strong>: {convertir_linea(d["que"])}</p>'
            f'{nota}{origen}</li>')


def pagina_decisiones(base, ediciones):
    """decisiones.html: lo que se está decidiendo, quién y para cuándo, y en qué quedó."""
    todas = [(d, e) for e in ediciones for d in e["decisiones"]]
    orden = ["vencida", "pendiente", "aplazada", "tomada", "sin_decision"]
    titulos = {"vencida": "Venció el plazo y no hay noticia", "pendiente": "Por decidir",
               "aplazada": "Aplazadas", "tomada": "Ya se decidieron", "sin_decision": "Nadie las tomó"}
    grupos = {k: [] for k in orden}
    for d, e in todas:
        grupos[estado_decision(d)[0]].append((d, e))
    bloques = []
    for k in orden:
        if not grupos[k]:
            continue
        lista = sorted(grupos[k], key=lambda x: (x[0]["plazo"] or "9999", x[1]["fecha"]))
        items = "".join(html_decision(d, "", e) for d, e in lista)
        bloques.append(f'<section class="decisiones-grupo"><h2>{titulos[k]}</h2><ul class="decisiones">{items}</ul></section>')
    contenido = f"""<header class="cabecera">
<h1>Decisiones</h1>
<p class="bajada">Lo que alguien tiene que decidir sobre los temas que hemos contado: quién, para cuándo y en qué quedó.</p>
<p class="bajada"><a href="memoria.html">Memoria: promesas que siguen esperando →</a></p>
</header>
{"".join(bloques) or "<p>Todavía no hay decisiones en seguimiento.</p>"}"""
    return pagina(base, "Decisiones · Otra lectura",
                  "Seguimiento de las decisiones pendientes sobre los temas de Otra lectura.", "",
                  contenido, "/decisiones.html", seccion="decisiones")


def subir_que_hacer(cuerpo):
    """«Qué hacer con esto» se escribe al final, pero se muestra al cerrar la
    historia principal, antes de «Dos lecturas» y «Quién decide»: primero se
    entiende el tema y después lo práctico. Para que nadie se lo pierda, debajo
    de «En pocas palabras» queda un enlace discreto que baja hasta allí."""
    m = re.search(r'<section class="carril hacer"[^>]*>.*?</section>\n?', cuerpo, re.S)
    ancla = re.search(r'<p class="con-etiqueta[^"]*">\s*<strong class="etiqueta">En pocas palabras\.?</strong>.*?</p>\n?',
                      cuerpo, re.S)
    if not m or not ancla or ancla.start() > m.start():
        return cuerpo
    bloque = m.group(0)
    if ' id=' not in bloque.split('>', 1)[0]:
        bloque = bloque.replace('<section class="carril hacer"', '<section class="carril hacer" id="que-hacer"', 1)
    sin = cuerpo[:m.start()] + cuerpo[m.end():]
    # Tras la historia: antes del primer carril secundario que siga a «En pocas palabras».
    sig = re.compile(r'<section class="carril (?:lecturas|decide|paradoja|conversar|cierre)\b')
    destino = sig.search(sin, ancla.end())
    pos = destino.start() if destino else len(sin)
    sin = sin[:pos] + bloque + sin[pos:]
    enlace = '<p class="ir-hacer"><a href="#que-hacer">Qué hacer con esto <span aria-hidden="true">↓</span></a></p>\n'
    fin = ancla.end()
    curioso = re.match(r'\s*<p class="con-etiqueta curioso[^"]*">.*?</p>\n?', sin[fin:], re.S)
    if curioso:  # el enlace va después de «El dato curioso», que sigue a «En pocas palabras»
        fin += curioso.end()
    return sin[:fin] + enlace + sin[fin:]


RE_CONEXION = re.compile(r'<p class="con-etiqueta[^"]*">\s*<strong class="etiqueta">'
                         r'(?:Cómo se conecta|Lo que ya habíamos contado)\.?</strong>.*?</p>\n?', re.S)


def bajar_conexion(cuerpo):
    """«Lo que ya habíamos contado» (antes «Cómo se conecta») va al cerrar la
    historia, antes de «Qué hacer con esto»: quien llega por primera vez lee
    primero el tema y después, si quiere, el hilo con ediciones anteriores."""
    m = RE_CONEXION.search(cuerpo)
    if not m:
        return cuerpo
    parrafo = re.sub(r'(<strong class="etiqueta">)Cómo se conecta(\.?</strong>)',
                     r'\1Lo que ya habíamos contado\2', m.group(0))
    sin = cuerpo[:m.start()] + cuerpo[m.end():]
    hacer = sin.find('<section class="carril hacer"')
    if hacer < 0:
        return sin[:m.start()] + parrafo + sin[m.start():]
    cierre = sin.rfind('</article>', 0, hacer)
    if cierre < 0 or cierre < m.start():
        cierre = sin.rfind('</section>', 0, hacer)
    if cierre < 0 or cierre < m.start():
        return sin[:m.start()] + parrafo + sin[m.start():]
    return sin[:cierre] + parrafo + sin[cierre:]


RE_PATRON = re.compile(r'<p class="con-etiqueta[^"]*">\s*<strong class="etiqueta">El patrón\.?</strong>\s*(.*?)</p>', re.S)
RE_CUENTO = re.compile(r'<p class="con-etiqueta[^"]*">\s*<strong class="etiqueta">Ojo con el cuento\.?</strong>\s*(.*?)</p>', re.S)


def pagina_memoria(base, ediciones):
    """memoria.html: lo que no se nos puede olvidar. Las promesas que siguen
    esperando y los patrones para no dejarse meter el cuento, de todas las ediciones."""
    promesas = [(d, e) for e in ediciones for d in e["decisiones"]
                if estado_decision(d)[0] == "vencida" or d.get("incumplidos")
                or (d.get("prometido_desde") and d["estado"] in ("pendiente", "aplazada"))]
    promesas.sort(key=lambda x: (x[0].get("prometido_desde") or x[1]["fecha"], x[1]["fecha"]))
    items_p = "".join(html_decision(d, "", e) for d, e in promesas)
    def recoger(regex):
        return [f'<li><p>{m.group(1).strip()}</p><p class="decision-origen">'
                f'<a href="ediciones/{e["slug"]}.html">{html.escape(e["titulo"])}</a> · '
                f'{fecha_legible(e["fecha"])}</p></li>'
                for e in ediciones for m in regex.finditer(e["cuerpo"])]
    cuentos, patrones = recoger(RE_CUENTO), recoger(RE_PATRON)
    bloque_p = (f'<section class="decisiones-grupo"><h2>Promesas que siguen esperando</h2>'
                f'<p class="memoria-nota">Lo que alguien prometió y no ha cumplido, de la más antigua a la más reciente.</p>'
                f'<ul class="decisiones">{items_p}</ul></section>') if items_p else ""
    bloque_c = (f'<section class="decisiones-grupo"><h2>Para no dejarse meter el cuento</h2>'
                f'<p class="memoria-nota">Patrones que se repiten. Cada uno salió de una edición.</p>'
                f'<ul class="memoria-cuentos">{"".join(cuentos)}</ul></section>') if cuentos else ""
    bloque_h = (f'<section class="decisiones-grupo"><h2>Lo que enseña la historia</h2>'
                f'<p class="memoria-nota">Momentos en que algo cambió de verdad, y el patrón que dejan. Cada uno salió de una edición.</p>'
                f'<ul class="memoria-cuentos">{"".join(patrones)}</ul></section>') if patrones else ""
    contenido = f"""<header class="cabecera">
<h1>Memoria</h1>
<p class="bajada">Lo que no se nos puede olvidar: promesas que siguen esperando, patrones para reconocer una promesa vacía y lo que enseña la historia. Se actualiza solo, con cada edición.</p>
</header>
{bloque_p}{bloque_c}{bloque_h}
{"" if (bloque_p or bloque_c or bloque_h) else "<p>Todavía no hay nada en la memoria.</p>"}
<p class="decision-mas"><a href="decisiones.html">Ver todas las decisiones →</a></p>"""
    return pagina(base, "Memoria · Otra lectura",
                  "Promesas que siguen esperando y patrones para no dejarse meter el cuento.", "",
                  contenido, "/memoria.html", seccion="memoria")


def indice_busqueda(ediciones):
    """buscar.json: lo que el buscador recorre. Título, fecha, temas, lugares,
    resumen y el texto de lectura (sin fuentes, glosario ni nota metodológica)."""
    filas = []
    for e in ediciones:
        lectura = re.split(r'<section class="carril cierre"', e["cuerpo"])[0]
        lectura = re.sub(r'<h[1-3][^>]*>.*?</h[1-3]>', ' ', lectura, flags=re.S)  # los títulos ya van en "t" y "k"
        filas.append({
            "t": html.unescape(e["titulo"]),
            "f": e["fecha"],
            "d": fecha_legible(e["fecha"]),
            "u": f"ediciones/{e['slug']}.html",
            "k": " ".join(e["titulos_nudos"] + e["lugares"] + [CATEGORIAS.get(c, c) for c in e["categorias"]]),
            "r": entradilla(e),
            "x": " ".join(texto_plano(lectura).split()),
        })
    return json.dumps(filas, ensure_ascii=False, separators=(",", ":"))


def pagina_buscar(base):
    """buscar.html: busca por palabra clave en todas las ediciones. Necesita
    JavaScript; sin él, remite al archivo de días anteriores."""
    contenido = """<header class="cabecera">
<h1>Buscar</h1>
<p class="bajada">Escriba una palabra o un nombre y aparecen las ediciones que hablan de eso.</p>
</header>
<form class="buscador" action="buscar.html" method="get" role="search">
<label for="q">Palabra clave</label>
<div class="buscador-fila">
<input id="q" name="q" type="search" autocomplete="off" placeholder="Por ejemplo: agua, EPS, Guajira">
<button type="submit">Buscar</button>
</div>
</form>
<p class="buscador-estado" role="status" aria-live="polite"></p>
<ol class="resultados"></ol>
<noscript><p class="buscador-sin-js">El buscador necesita JavaScript. Mientras tanto, puede recorrer los <a href="archivo.html">días anteriores</a>.</p></noscript>
<script>
(function () {
  var form = document.querySelector(".buscador"), input = form.querySelector("input");
  var estado = document.querySelector(".buscador-estado"), lista = document.querySelector(".resultados");
  var datos = null, espera = null;
  function plano(t) { return (t || "").normalize("NFD").replace(/[\\u0300-\\u036f]/g, "").toLowerCase(); }
  function esc(t) { return t.replace(/[&<>"]/g, function (c) { return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]; }); }
  function marcar(texto, terminos) {
    var p = plano(texto), out = "", i = 0, rangos = [];
    terminos.forEach(function (t) { var j = p.indexOf(t); while (j >= 0) { rangos.push([j, j + t.length]); j = p.indexOf(t, j + t.length); } });
    rangos.sort(function (a, b) { return a[0] - b[0]; });
    rangos.forEach(function (r) { if (r[0] < i) return; out += esc(texto.slice(i, r[0])) + "<mark>" + esc(texto.slice(r[0], r[1])) + "</mark>"; i = r[1]; });
    return out + esc(texto.slice(i));
  }
  function fragmento(texto, terminos) {
    var p = plano(texto), j = -1;
    for (var k = 0; k < terminos.length && j < 0; k++) j = p.indexOf(terminos[k]);
    if (j < 0) return "";
    var ini = Math.max(0, j - 90), fin = Math.min(texto.length, j + 160);
    while (ini > 0 && texto[ini] !== " ") ini--;
    while (fin < texto.length && texto[fin] !== " ") fin++;
    return (ini > 0 ? "… " : "") + texto.slice(ini, fin).trim() + (fin < texto.length ? " …" : "");
  }
  function buscar() {
    var q = input.value.trim(), terminos = plano(q).split(/\\s+/).filter(function (t) { return t.length > 1; });
    try { history.replaceState(null, "", q ? "?q=" + encodeURIComponent(q) : location.pathname); } catch (e) {}
    lista.innerHTML = "";
    if (!terminos.length) { estado.textContent = ""; return; }
    var hallados = [];
    datos.forEach(function (d) {
      var t = plano(d.t), k = plano(d.k), r = plano(d.r), x = plano(d.x), puntos = 0;
      for (var i = 0; i < terminos.length; i++) {
        var w = terminos[i], en = 0;
        if (t.indexOf(w) >= 0) en += 6;
        if (k.indexOf(w) >= 0) en += 3;
        if (r.indexOf(w) >= 0) en += 2;
        if (x.indexOf(w) >= 0) en += 1 + Math.min(3, x.split(w).length - 2);
        if (!en) return;
        puntos += en;
      }
      hallados.push([puntos, d]);
    });
    hallados.sort(function (a, b) { return b[0] - a[0] || (a[1].f < b[1].f ? 1 : -1); });
    var n = hallados.length;
    estado.textContent = n ? (n === 1 ? "Una edición" : n + " ediciones") + " con «" + q + "»." : "Ninguna edición menciona «" + q + "». Pruebe con otra palabra.";
    lista.innerHTML = hallados.slice(0, 40).map(function (h) {
      var d = h[1], frag = fragmento(d.x, terminos) || d.r;
      return '<li><a href="' + d.u + '">' + marcar(d.t, terminos) + '</a><p class="resultado-fecha"><time datetime="' + d.f + '">' + esc(d.d) + "</time></p>" +
             '<p class="resultado-texto">' + marcar(frag, terminos) + "</p></li>";
    }).join("");
  }
  form.addEventListener("submit", function (ev) { ev.preventDefault(); if (datos) buscar(); });
  input.addEventListener("input", function () { clearTimeout(espera); espera = setTimeout(function () { if (datos) buscar(); }, 200); });
  var inicial = new URLSearchParams(location.search).get("q");
  if (inicial) input.value = inicial;
  estado.textContent = "Cargando el archivo…";
  fetch("buscar.json").then(function (r) { return r.json(); }).then(function (j) {
    datos = j; estado.textContent = ""; if (input.value.trim()) buscar(); else input.focus();
  }).catch(function () {
    estado.innerHTML = 'No se pudo cargar el buscador. Puede recorrer los <a href="archivo.html">días anteriores</a>.';
  });
})();
</script>"""
    return pagina(base, "Buscar · Otra lectura",
                  "Busque por palabra clave en todas las ediciones de Otra lectura.", "",
                  contenido, "/buscar.html", seccion="buscar")


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

    # Aviso (no detiene el build): el techo editorial es de ~1.200 palabras,
    # y de ~750 visibles desde el 2026-10-24.
    for e in ediciones:
        # Las ediciones anteriores al 28 de septiembre de 2026 tenían otro techo (1.500).
        techo = LARGO_MAXIMO_CORTO if e["fecha"] >= FORMATO_CORTO_DESDE else LARGO_MAXIMO
        if e["palabras"] > techo and e["fecha"] >= "2026-09-28":
            print(f"  aviso: ediciones/{e['archivo']} tiene ~{e['palabras']} palabras de lectura "
                  f"(techo: {techo}).", file=sys.stderr)
        n = len(e["titulo"].split())
        if e["fecha"] >= FORMATO_CORTO_DESDE and n > TITULO_MAXIMO_PALABRAS and not es_repaso(e):
            print(f"  aviso: ediciones/{e['archivo']} tiene un titular de {n} palabras "
                  f"(máximo: unas 12).", file=sys.stderr)

    # Aviso: desde el 2026-10-13, la edición diaria trae «El dato curioso» (pedido de Mateo).
    for e in ediciones:
        if (e["fecha"] >= "2026-10-13" and e["archivo"].endswith("-radar.md")
                and 'class="con-etiqueta curioso' not in e["cuerpo"]):
            print(f"  aviso: ediciones/{e['archivo']} no trae «El dato curioso».", file=sys.stderr)
    # Aviso: desde el 2026-10-09, toda edición con seguimiento explica por qué se conecta.
    for e in ediciones:
        if e["seguimiento"] and e["fecha"] >= "2026-10-09" and not RE_CONEXION.search(e["cuerpo"]):
            print(f"  aviso: ediciones/{e['archivo']} tiene seguimiento pero no explica "
                  f"«Lo que ya habíamos contado».", file=sys.stderr)

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
    for icono in (PLANTILLA / "iconos").iterdir():
        shutil.copy(icono, SITE / icono.name)
    (SITE / "site.webmanifest").write_text(json.dumps({
        "name": NOMBRE_SITIO, "short_name": NOMBRE_SITIO, "description": FRASE_SITIO,
        "lang": "es-CO", "start_url": "/", "display": "browser",
        "background_color": "#efe7d6", "theme_color": "#16130f",
        "icons": [{"src": "/icono-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "/icono-512.png", "sizes": "512x512", "type": "image/png"}]},
        ensure_ascii=False, indent=1), encoding="utf-8")
    if IMAGENES.is_dir():
        shutil.copytree(IMAGENES, SITE / "imagenes")
    robots = "User-agent: *\n" + ("Allow: /\n" if INDEXAR else "Disallow: /\n")
    if INDEXAR:
        # Buscadores y asistentes de IA: bienvenidos a leer y citar (con enlace).
        robots += "".join(f"\nUser-agent: {bot}\nAllow: /\n" for bot in BOTS_IA)
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
    (SITE / "decisiones.html").write_text(pagina_decisiones(base, ediciones), encoding="utf-8")
    (SITE / "memoria.html").write_text(pagina_memoria(base, ediciones), encoding="utf-8")
    (SITE / "buscar.html").write_text(pagina_buscar(base), encoding="utf-8")
    (SITE / "buscar.json").write_text(indice_busqueda(ediciones), encoding="utf-8")
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
        urls += [("/archivo.html", ""), ("/sobre.html", ""), ("/buscar.html", "")]
        urls += [(f"/temas/{slug}.html", "") for slug in hilos]
        filas = "".join(f"<url><loc>{SITIO_URL}{u}</loc>" + (f"<lastmod>{f}</lastmod>" if f else "")
                        + "</url>\n" for u, f in urls)
        (SITE / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{filas}</urlset>\n',
            encoding="utf-8")

    if SITIO_URL:
        (SITE / "feed.xml").write_text(rss(ediciones), encoding="utf-8")
        (SITE / "llms.txt").write_text(llms_txt(ediciones, hilos), encoding="utf-8")

    if AYUDA.exists():
        (SITE / "ayuda.html").write_text(pagina_texto(
            base, AYUDA, "ayuda.html", "Cómo se usa",
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
