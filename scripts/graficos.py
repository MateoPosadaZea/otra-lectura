"""Gráficos de las ediciones: bloques ```grafico en el markdown → HTML/SVG.

Se dibujan en el build, sin dependencias ni JavaScript: el gráfico se ve
aunque el navegador no ejecute nada. El JavaScript de la plantilla solo
agrega el tooltip. Cada gráfico incluye su tabla de datos ("Ver datos").

Formato (el mismo subconjunto de YAML del frontmatter):

    ```grafico
    tipo: barras            # barras | columnas | lineas | puntos
    titulo: "Muertes por ciclones en Bangladés"
    subtitulo: "Personas fallecidas por ciclón"   # opcional
    unidad: "muertes"       # opcional, para el tooltip
    escala: log             # opcional, solo en puntos (magnitudes muy distintas)
    destacar: "Amphan, 2020"  # opcional: resalta una categoría, el resto en gris
    fuente: "Banco Mundial; Oficina de Meteorología de Bangladés"
    datos:                  # barras, columnas y puntos
      - etiqueta: "Bhola, 1970"
        valor: 500000
    eje_x: [2019, 2020, 2021]   # lineas
    series:                     # lineas, hasta 3
      - nombre: "Colombia"
        valores: [1.5, 2, 2.4]
    ```

Los números se escriben sin separador de miles y con punto decimal.
"""

import html
import math
import re

from frontmatter import ErrorFrontmatter, parsear

TIPOS = ("barras", "columnas", "lineas", "puntos")
MAX_SERIES = 3  # validado con daltonismo para todos los pares; más series → otro gráfico
MAX_CATEGORIAS = 16

RE_BLOQUE = re.compile(r"^```grafico[ \t]*\n(.*?)^```[ \t]*$", re.M | re.S)


class ErrorGrafico(Exception):
    pass


# --- Números -------------------------------------------------------------------

def numero(valor, donde):
    try:
        return float(str(valor).strip())
    except ValueError:
        raise ErrorGrafico(f"{donde}: «{valor}» no es un número (sin separador de miles, "
                           f"punto decimal)")


def fmt(v):
    """1234567.5 → '1.234.567,5' (miles con punto, decimales con coma)."""
    if abs(v - round(v)) < 1e-9:
        return f"{round(v):,}".replace(",", ".")
    s = f"{v:,.2f}".rstrip("0").rstrip(".")
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def fmt_corto(v):
    """Para marcas de eje: 1000 → '1 mil', 2500000 → '2,5 M'."""
    if abs(v) >= 1e6:
        return f"{fmt(v / 1e6)} M"
    if abs(v) >= 1e4:
        return f"{fmt(v / 1e3)} mil"
    return fmt(v)


def ticks_lineales(maximo, n=4):
    """Marcas redondas (1, 2, 5 × 10^k) desde 0 hasta cubrir el máximo."""
    if maximo <= 0:
        return [0, 1]
    bruto = maximo / n
    base = 10 ** math.floor(math.log10(bruto))
    paso = next(m * base for m in (1, 2, 2.5, 5, 10) if m * base >= bruto)
    tope = math.ceil(maximo / paso) * paso
    return [i * paso for i in range(int(round(tope / paso)) + 1)]


def ticks_log(minimo, maximo):
    return [10 ** k for k in range(math.floor(math.log10(minimo)), math.ceil(math.log10(maximo)) + 1)]


# --- Especificación ------------------------------------------------------------

def leer_spec(texto):
    try:
        spec, _ = parsear("---\n" + texto + "\n---\n")
    except ErrorFrontmatter as err:
        raise ErrorGrafico(f"formato inválido: {err}")
    tipo = str(spec.get("tipo") or "")
    if tipo not in TIPOS:
        raise ErrorGrafico(f"tipo «{tipo}» inválido (válidos: {', '.join(TIPOS)})")
    for campo in ("titulo", "fuente"):
        if not spec.get(campo):
            raise ErrorGrafico(f"falta «{campo}»")
    escala = str(spec.get("escala") or "lineal")
    if escala not in ("lineal", "log"):
        raise ErrorGrafico("escala debe ser «lineal» o «log»")
    if escala == "log" and tipo != "puntos":
        raise ErrorGrafico("la escala log solo se permite en «puntos» (una barra en escala "
                           "logarítmica exagera o esconde las diferencias)")

    if tipo == "lineas":
        eje = spec.get("eje_x")
        series = spec.get("series")
        if not isinstance(eje, list) or not eje:
            raise ErrorGrafico("lineas necesita «eje_x» como lista")
        if not isinstance(series, list) or not series:
            raise ErrorGrafico("lineas necesita «series»")
        if len(series) > MAX_SERIES:
            raise ErrorGrafico(f"máximo {MAX_SERIES} series por gráfico; divida en varios gráficos")
        limpias = []
        for i, s in enumerate(series, 1):
            if not isinstance(s, dict) or not s.get("nombre") or not isinstance(s.get("valores"), list):
                raise ErrorGrafico(f"series[{i}] necesita «nombre» y «valores» (lista)")
            if len(s["valores"]) != len(eje):
                raise ErrorGrafico(f"series[{i}] tiene {len(s['valores'])} valores y eje_x tiene {len(eje)}")
            vals = [None if str(v).strip() in ("", "null", "-") else numero(v, f"series[{i}]")
                    for v in s["valores"]]
            limpias.append({"nombre": str(s["nombre"]), "valores": vals})
        datos = {"eje": [str(x) for x in eje], "series": limpias}
    else:
        filas = spec.get("datos")
        if not isinstance(filas, list) or not filas:
            raise ErrorGrafico("falta «datos»")
        if len(filas) > MAX_CATEGORIAS:
            raise ErrorGrafico(f"máximo {MAX_CATEGORIAS} categorías; agrupe o use una tabla")
        limpias = []
        for i, f in enumerate(filas, 1):
            if not isinstance(f, dict) or "etiqueta" not in f or "valor" not in f:
                raise ErrorGrafico(f"datos[{i}] necesita «etiqueta» y «valor»")
            v = numero(f["valor"], f"datos[{i}].valor")
            if escala == "log" and v <= 0:
                raise ErrorGrafico(f"datos[{i}]: en escala log los valores deben ser mayores que 0")
            if tipo != "puntos" and v < 0:
                raise ErrorGrafico(f"datos[{i}]: valores negativos no soportados en {tipo}")
            limpias.append({"etiqueta": str(f["etiqueta"]), "valor": v, "nota": str(f.get("nota") or "")})
        datos = {"filas": limpias}

    return {
        "tipo": tipo, "escala": escala,
        "titulo": str(spec["titulo"]), "subtitulo": str(spec.get("subtitulo") or ""),
        "unidad": str(spec.get("unidad") or ""), "fuente": str(spec["fuente"]),
        "destacar": str(spec.get("destacar") or ""), **datos,
    }


# --- Piezas comunes --------------------------------------------------------------

def e(s):
    return html.escape(str(s), quote=True)


def tip(valor, unidad, etiqueta, nota=""):
    """Texto del tooltip: el valor primero, la categoría después."""
    linea = f"{fmt(valor)} {unidad}".strip()
    return f"{linea}\n{etiqueta}" + (f"\n{nota}" if nota else "")


def tabla(g):
    if g["tipo"] == "lineas":
        cab = "".join(f"<th scope=\"col\">{e(s['nombre'])}</th>" for s in g["series"])
        filas = "".join(
            f"<tr><th scope=\"row\">{e(x)}</th>"
            + "".join(f"<td>{'—' if s['valores'][i] is None else fmt(s['valores'][i])}</td>" for s in g["series"])
            + "</tr>" for i, x in enumerate(g["eje"]))
        cabecera = f"<tr><th></th>{cab}</tr>"
    else:
        cabecera = f"<tr><th></th><th scope=\"col\">{e(g['unidad'] or 'Valor')}</th></tr>"
        filas = "".join(
            f"<tr><th scope=\"row\">{e(f['etiqueta'])}</th><td>{fmt(f['valor'])}"
            f"{' (' + e(f['nota']) + ')' if f['nota'] else ''}</td></tr>" for f in g["filas"])
    return (f'<details class="g-tabla"><summary>Ver datos</summary>'
            f"<table><thead>{cabecera}</thead><tbody>{filas}</tbody></table></details>")


def envolver(g, cuerpo, leyenda=""):
    sub = f'<span class="g-sub">{e(g["subtitulo"])}</span>' if g["subtitulo"] else ""
    return (f'<figure class="grafico g-{g["tipo"]}">\n'
            f'<figcaption><strong>{e(g["titulo"])}</strong>{sub}</figcaption>\n'
            f"{leyenda}{cuerpo}\n"
            f'<p class="g-fuente">Fuente: {e(g["fuente"])}</p>\n{tabla(g)}\n</figure>')


def clase_serie(f, g, i=0):
    if g["destacar"]:
        return "g-s1" if f["etiqueta"] == g["destacar"] else "g-gris"
    return f"g-s{i + 1}"


# --- Barras horizontales y puntos (HTML: se adaptan solos al ancho) ------------

def barras(g):
    maximo = max(f["valor"] for f in g["filas"]) or 1
    filas = []
    for f in g["filas"]:
        ancho = f["valor"] / maximo * 100
        filas.append(
            f'<div class="g-fila" tabindex="0" data-tip="{e(tip(f["valor"], g["unidad"], f["etiqueta"], f["nota"]))}">'
            f'<span class="g-etq">{e(f["etiqueta"])}</span>'
            f'<span class="g-pista"><span class="g-barra {clase_serie(f, g)}" style="width:{ancho:.2f}%">'
            f'</span></span>'
            f'<span class="g-val">{fmt(f["valor"])}</span></div>')
    return envolver(g, '<div class="g-filas">' + "".join(filas) + "</div>")


def puntos(g):
    vals = [f["valor"] for f in g["filas"]]
    if g["escala"] == "log":
        marcas = ticks_log(min(vals), max(vals))
        lo, hi = math.log10(marcas[0]), math.log10(marcas[-1])
        pos = lambda v: (math.log10(v) - lo) / (hi - lo) * 100
    else:
        marcas = ticks_lineales(max(vals))
        pos = lambda v: v / marcas[-1] * 100
    reglas = "".join(f'<span class="g-regla" style="left:{pos(m):.2f}%"></span>' for m in marcas)
    filas = []
    for f in g["filas"]:
        filas.append(
            f'<div class="g-fila" tabindex="0" data-tip="{e(tip(f["valor"], g["unidad"], f["etiqueta"], f["nota"]))}">'
            f'<span class="g-etq">{e(f["etiqueta"])}</span>'
            f'<span class="g-pista">{reglas}<span class="g-punto {clase_serie(f, g)}" '
            f'style="left:{pos(f["valor"]):.2f}%"></span></span>'
            f'<span class="g-val">{fmt(f["valor"])}</span></div>')
    eje = "".join(f'<span style="left:{pos(m):.2f}%">{fmt_corto(m)}</span>' for m in marcas)
    nota_log = ('<p class="g-nota">Escala logarítmica: cada marca vale diez veces la anterior.</p>'
                if g["escala"] == "log" else "")
    cuerpo = (f'<div class="g-filas">{"".join(filas)}'
              f'<div class="g-fila g-eje"><span></span><span class="g-pista">{eje}</span><span></span></div>'
              f"</div>{nota_log}")
    return envolver(g, cuerpo)


# --- Columnas y líneas (SVG con viewBox; el texto va en HTML aparte si hace falta) ---

ANCHO, ALTO = 420, 230
M_IZQ, M_DER, M_SUP, M_INF = 44, 12, 14, 30


def eje_y(marcas, y):
    lineas = []
    for m in marcas:
        yy = y(m)
        lineas.append(f'<line class="g-grid" x1="{M_IZQ}" x2="{ANCHO - M_DER}" y1="{yy:.1f}" y2="{yy:.1f}"/>'
                      f'<text class="g-tick" x="{M_IZQ - 6}" y="{yy + 4:.1f}" text-anchor="end">{fmt_corto(m)}</text>')
    return "".join(lineas)


def columnas(g):
    filas = g["filas"]
    marcas = ticks_lineales(max(f["valor"] for f in filas))
    alto_util = ALTO - M_SUP - M_INF
    y = lambda v: M_SUP + alto_util - v / marcas[-1] * alto_util
    banda = (ANCHO - M_IZQ - M_DER) / len(filas)
    ancho = min(24, banda * 0.6)
    etiquetar = len(filas) <= 8
    partes = [eje_y(marcas, y)]
    for i, f in enumerate(filas):
        cx = M_IZQ + banda * (i + 0.5)
        x0, y0, yb = cx - ancho / 2, y(f["valor"]), y(0)
        r = min(4, ancho / 2, max(0, yb - y0))
        d = (f"M{x0:.1f},{yb:.1f} V{y0 + r:.1f} Q{x0:.1f},{y0:.1f} {x0 + r:.1f},{y0:.1f} "
             f"H{x0 + ancho - r:.1f} Q{x0 + ancho:.1f},{y0:.1f} {x0 + ancho:.1f},{y0 + r:.1f} V{yb:.1f} Z")
        partes.append(
            f'<g class="g-marca" tabindex="0" data-tip="{e(tip(f["valor"], g["unidad"], f["etiqueta"], f["nota"]))}">'
            f'<rect class="g-hit" x="{cx - banda / 2:.1f}" y="{M_SUP}" width="{banda:.1f}" height="{alto_util}"/>'
            f'<path class="{clase_serie(f, g)}" d="{d}"><title>{e(f["etiqueta"])}: {e(fmt(f["valor"]))}</title></path>'
            + (f'<text class="g-cap" x="{cx:.1f}" y="{y0 - 5:.1f}" text-anchor="middle">{fmt(f["valor"])}</text>'
               if etiquetar or f["etiqueta"] == g["destacar"] else "")
            + f'<text class="g-tick" x="{cx:.1f}" y="{ALTO - M_INF + 16}" text-anchor="middle">{e(f["etiqueta"])}</text></g>')
    svg = (f'<svg class="g-svg" viewBox="0 0 {ANCHO} {ALTO}" role="img" '
           f'aria-label="{e(g["titulo"])}">{"".join(partes)}</svg>')
    return envolver(g, svg)


def lineas(g):
    eje, series = g["eje"], g["series"]
    todos = [v for s in series for v in s["valores"] if v is not None]
    marcas = ticks_lineales(max(todos))
    m_der = 92  # espacio para la etiqueta final de cada línea
    alto_util = ALTO - M_SUP - M_INF
    y = lambda v: M_SUP + alto_util - v / marcas[-1] * alto_util
    paso = (ANCHO - M_IZQ - m_der) / max(1, len(eje) - 1)
    x = lambda i: M_IZQ + paso * i if len(eje) > 1 else (ANCHO - m_der + M_IZQ) / 2
    partes = [eje_y(marcas, y).replace(f'x2="{ANCHO - M_DER}"', f'x2="{ANCHO - m_der}"')]
    cada = max(1, math.ceil(len(eje) / 8))
    for i, et in enumerate(eje):
        if i % cada == 0 or i == len(eje) - 1:
            partes.append(f'<text class="g-tick" x="{x(i):.1f}" y="{ALTO - M_INF + 16}" text-anchor="middle">{e(et)}</text>')
    finales = []
    for k, s in enumerate(series):
        tramos, actual = [], []
        for i, v in enumerate(s["valores"]):
            if v is None:
                if actual:
                    tramos.append(actual)
                actual = []
            else:
                actual.append(f"{x(i):.1f},{y(v):.1f}")
        if actual:
            tramos.append(actual)
        for t in tramos:
            partes.append(f'<polyline class="g-linea g-s{k + 1}" points="{" ".join(t)}"/>')
        ult = max(i for i, v in enumerate(s["valores"]) if v is not None)
        vy = y(s["valores"][ult])
        partes.append(f'<circle class="g-fin g-s{k + 1}" cx="{x(ult):.1f}" cy="{vy:.1f}" r="4"/>')
        finales.append([vy, k, s, ult])
    # Etiquetas finales: si chocan, se separan con una línea guía hacia su punto.
    finales.sort(key=lambda f: f[0])
    pos = []
    for vy, k, s, ult in finales:
        ly = max(vy, pos[-1] + 16) if pos else vy
        pos.append(ly)
        if abs(ly - vy) > 1:
            partes.append(f'<line class="g-guia" x1="{x(ult) + 6:.1f}" y1="{vy:.1f}" x2="{ANCHO - m_der + 4:.1f}" y2="{ly:.1f}"/>')
        partes.append(f'<text class="g-cap" x="{ANCHO - m_der + 8:.1f}" y="{ly + 4:.1f}">'
                      f'{fmt(s["valores"][ult])}'
                      + (f' <tspan class="g-tick g-nombre">{e(s["nombre"][:14])}</tspan>' if len(series) > 1 else "")
                      + "</text>")
    # Capa de lectura: por cada X, una franja que muestra la cruz y todos los valores.
    for i, et in enumerate(eje):
        lineas_tip = [f"{'—' if s['valores'][i] is None else fmt(s['valores'][i])} {s['nombre']}"
                      for s in series]
        partes.append(
            f'<g class="g-marca g-x" tabindex="0" data-tip="{e(et + chr(10) + chr(10).join(lineas_tip))}">'
            f'<rect class="g-hit" x="{x(i) - paso / 2:.1f}" y="{M_SUP}" width="{paso:.1f}" height="{alto_util}"/>'
            f'<line class="g-cruz" x1="{x(i):.1f}" x2="{x(i):.1f}" y1="{M_SUP}" y2="{ALTO - M_INF}"/></g>')
    leyenda = ""
    if len(series) > 1:
        leyenda = ('<ul class="g-leyenda">' + "".join(
            f'<li><span class="g-clave g-s{k + 1}"></span>{e(s["nombre"])}</li>'
            for k, s in enumerate(series)) + "</ul>")
    svg = (f'<svg class="g-svg" viewBox="0 0 {ANCHO} {ALTO}" role="img" '
           f'aria-label="{e(g["titulo"])}">{"".join(partes)}</svg>')
    return envolver(g, svg, leyenda)


DIBUJAR = {"barras": barras, "columnas": columnas, "lineas": lineas, "puntos": puntos}


def extraer(md):
    """Reemplaza cada bloque ```grafico por un marcador y devuelve (md, [html])."""
    graficos = []

    def cambiar(m):
        try:
            g = leer_spec(m.group(1))
        except ErrorGrafico as err:
            n = md[:m.start()].count("\n") + 1
            raise ErrorGrafico(f"gráfico en la línea {n} del cuerpo: {err}")
        graficos.append(DIBUJAR[g["tipo"]](g))
        return f'\n<div class="grafico-marcador" data-n="{len(graficos) - 1}"></div>\n'

    return RE_BLOQUE.sub(cambiar, md), graficos


def insertar(cuerpo_html, graficos):
    return re.sub(r'<div class="grafico-marcador" data-n="(\d+)"></div>',
                  lambda m: graficos[int(m.group(1))], cuerpo_html)
