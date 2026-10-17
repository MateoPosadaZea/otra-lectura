"""Recorridos: historias que se cuentan al bajar, en vez de un bloque de texto.

Dos bloques en el markdown de las ediciones, con el mismo subconjunto de YAML
del frontmatter:

    ```cronologia
    titulo: "La reforma pensional, fecha por fecha"
    subtitulo: "Lo que se prometió y lo que pasó"      # opcional
    fuente: "Corte Constitucional; La República"
    hitos:
      - fecha: "Julio de 2024"
        titulo: "Se publica la Ley 2381"
        texto: "Promete una renta de 230.000 pesos al mes."   # opcional
        estado: hecho           # hecho (por omisión) | incumplido | pendiente
    ```

    ```pasos
    titulo: "Bolivia: de 14 a 91 de cada 100"
    fuente: "Udape; BID"
    pasos:
      - cifra: "14 de cada 100"
        proporcion: 14          # opcional, 0 a 100: pinta la cuadrícula de 100 puntos
        texto: "Mayores de 60 con pensión por haber cotizado."
    ```

La cronología es una línea del tiempo que se dibuja a medida que se baja; los
pasos dejan fija una cifra (y su cuadrícula de 100 puntos) mientras el texto
pasa por encima. Todo sale en HTML desde el build: sin JavaScript se lee
completo, como lista; el JavaScript de la plantilla solo agrega el movimiento
y se apaga con «reducir movimiento». El texto de estos bloques no cuenta para
el techo de palabras, así que va corto: una o dos frases por hito o paso.
"""

import html
import re

import markdown

from frontmatter import ErrorFrontmatter, parsear

RE_BLOQUE = re.compile(r"^```(cronologia|pasos)[ \t]*\n(.*?)^```[ \t]*$", re.M | re.S)
ESTADOS = {"hecho": "", "incumplido": "Plazo incumplido", "pendiente": "Pendiente"}
MAX_HITOS = 12
MAX_PASOS = 6
MAX_PALABRAS = 45  # por hito o paso: si hace falta más, va en el texto de la edición


class ErrorRecorrido(Exception):
    pass


def e(s):
    return html.escape(str(s), quote=True)


def linea(md):
    """Markdown de una línea (negrita, cursiva, enlaces), sin <p>."""
    h = markdown.markdown(str(md), output_format="html").strip()
    return h[3:-4] if h.startswith("<p>") and h.endswith("</p>") else h


def _texto(item, campo, donde, requerido=True):
    v = item.get(campo)
    if v is None or str(v).strip() == "":
        if requerido:
            raise ErrorRecorrido(f"{donde} necesita «{campo}»")
        return ""
    if "$" in str(v):
        raise ErrorRecorrido(f"{donde}.{campo}: sin el signo «$»; escriba «pesos»")
    if len(str(v).split()) > MAX_PALABRAS:
        raise ErrorRecorrido(f"{donde}.{campo}: más de {MAX_PALABRAS} palabras; acórtelo "
                             f"o páselo al texto de la edición")
    return str(v).strip()


def leer_spec(tipo, texto):
    try:
        spec, _ = parsear("---\n" + texto + "\n---\n")
    except ErrorFrontmatter as err:
        raise ErrorRecorrido(f"formato inválido: {err}")
    for campo in ("titulo", "fuente"):
        if not spec.get(campo):
            raise ErrorRecorrido(f"falta «{campo}»")
    r = {"tipo": tipo, "titulo": str(spec["titulo"]), "fuente": str(spec["fuente"]),
         "subtitulo": str(spec.get("subtitulo") or "")}
    clave, maximo = ("hitos", MAX_HITOS) if tipo == "cronologia" else ("pasos", MAX_PASOS)
    items = spec.get(clave)
    if not isinstance(items, list) or len(items) < 2:
        raise ErrorRecorrido(f"«{clave}» necesita al menos dos elementos")
    if len(items) > maximo:
        raise ErrorRecorrido(f"máximo {maximo} {clave}; si son más, la historia es otra")
    limpios = []
    for i, it in enumerate(items, 1):
        donde = f"{clave}[{i}]"
        if not isinstance(it, dict):
            raise ErrorRecorrido(f"{donde} debe ser un mapa")
        if tipo == "cronologia":
            estado = str(it.get("estado") or "hecho")
            if estado not in ESTADOS:
                raise ErrorRecorrido(f"{donde}.estado «{estado}» inválido "
                                     f"(válidos: {', '.join(ESTADOS)})")
            limpios.append({"fecha": _texto(it, "fecha", donde), "titulo": _texto(it, "titulo", donde),
                            "texto": _texto(it, "texto", donde, False), "estado": estado})
        else:
            prop = it.get("proporcion")
            if prop is not None and str(prop).strip() != "":
                try:
                    prop = float(str(prop).strip())
                except ValueError:
                    raise ErrorRecorrido(f"{donde}.proporcion «{prop}» no es un número")
                if not 0 <= prop <= 100:
                    raise ErrorRecorrido(f"{donde}.proporcion debe estar entre 0 y 100")
                prop = round(prop)
            else:
                prop = None
            limpios.append({"cifra": _texto(it, "cifra", donde), "texto": _texto(it, "texto", donde),
                            "proporcion": prop})
    r[clave] = limpios
    return r


def cabecera(r):
    sub = f'<span class="g-sub">{e(r["subtitulo"])}</span>' if r["subtitulo"] else ""
    return f'<figcaption><strong>{e(r["titulo"])}</strong>{sub}</figcaption>\n'


def cronologia(r):
    hitos = []
    for h in r["hitos"]:
        aviso = ESTADOS[h["estado"]]
        marca = f'<span class="cr-estado">{aviso}</span>' if aviso else ""
        texto = f'<p class="cr-texto">{linea(h["texto"])}</p>' if h["texto"] else ""
        hitos.append(f'<li class="cr-hito cr-{h["estado"]}"><p class="cr-fecha">{e(h["fecha"])}{marca}</p>'
                     f'<p class="cr-titulo">{linea(h["titulo"])}</p>{texto}</li>')
    return (f'<figure class="recorrido cronologia" data-recorrido="cronologia">\n{cabecera(r)}'
            f'<div class="cr-cuerpo"><span class="cr-avance" aria-hidden="true"></span>'
            f'<ol class="cr-lista">\n' + "\n".join(hitos) + '\n</ol></div>\n'
            f'<p class="g-fuente">Fuente: {e(r["fuente"])}</p>\n</figure>')


def puntos(proporcion):
    """Cuadrícula de 100 puntos; los primeros `proporcion` van llenos."""
    llenos = -1 if proporcion is None else proporcion
    celdas = "".join(('<i class="on"' if k < llenos else "<i") + f' style="--k:{k}"></i>' for k in range(100))
    clase = "ps-puntos" + (" ps-sin" if proporcion is None else "")
    return f'<span class="{clase}" aria-hidden="true">{celdas}</span>'


def pasos(r):
    hay_puntos = any(p["proporcion"] is not None for p in r["pasos"])
    items = []
    for p in r["pasos"]:
        prop = "" if p["proporcion"] is None else f' data-proporcion="{p["proporcion"]}"'
        mini = puntos(p["proporcion"]) if hay_puntos and p["proporcion"] is not None else ""
        items.append(f'<li class="ps-paso" data-cifra="{e(p["cifra"])}"{prop}>'
                     f'<div class="ps-tarjeta"><p class="ps-cifra-paso">{e(p["cifra"])}</p>{mini}'
                     f'<p class="ps-texto">{linea(p["texto"])}</p></div></li>')
    primero = r["pasos"][0]
    panel = (f'<div class="ps-panel" aria-hidden="true"><p class="ps-cifra">{e(primero["cifra"])}</p>'
             + (puntos(primero["proporcion"]) if hay_puntos else "") + "</div>")
    return (f'<figure class="recorrido pasos" data-recorrido="pasos">\n{cabecera(r)}'
            f'<div class="ps-cuerpo">{panel}<ol class="ps-lista">\n' + "\n".join(items) + "\n</ol></div>\n"
            f'<p class="g-fuente">Fuente: {e(r["fuente"])}</p>\n</figure>')


DIBUJAR = {"cronologia": cronologia, "pasos": pasos}


def extraer(md):
    """Reemplaza cada bloque por un marcador y devuelve (md, [html])."""
    hechos = []

    def cambiar(m):
        try:
            r = leer_spec(m.group(1), m.group(2))
        except ErrorRecorrido as err:
            n = md[:m.start()].count("\n") + 1
            raise ErrorRecorrido(f"{m.group(1)} en la línea {n} del cuerpo: {err}")
        hechos.append(DIBUJAR[r["tipo"]](r))
        return f'\n<div class="recorrido-marcador" data-n="{len(hechos) - 1}"></div>\n'

    return RE_BLOQUE.sub(cambiar, md), hechos


def insertar(cuerpo_html, hechos):
    return re.sub(r'<div class="recorrido-marcador" data-n="(\d+)"></div>',
                  lambda m: hechos[int(m.group(1))], cuerpo_html)
