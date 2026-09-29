"""Imágenes para compartir (Open Graph, 1200 × 630), una por página.

Mismo diseño que plantilla/og.png: cabezote gótico arriba, un rótulo en rojo,
el título de la página en grande y una franja negra abajo. Se generan en el
build con Pillow; si Pillow no está, el sitio usa og.png para todo.
"""
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # sin Pillow: se queda la imagen fija
    Image = None

FUENTES = Path(__file__).resolve().parent.parent / "plantilla" / "fuentes-og"
ANCHO, ALTO = 1200, 630
PAPEL, TINTA, TENUE, ROJO = (216, 209, 199), (28, 27, 25), (87, 82, 75), (179, 64, 31)
MARGEN = 90


def disponible():
    return Image is not None


def _fuente(nombre, tam, peso=None):
    f = ImageFont.truetype(str(FUENTES / nombre), tam)
    if peso:
        try:
            f.set_variation_by_axes([peso])
        except Exception:
            pass
    return f


def _partir(draw, texto, fuente, ancho):
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = f"{actual} {palabra}".strip()
        if draw.textlength(prueba, font=fuente) <= ancho or not actual:
            actual = prueba
        else:
            lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    return lineas


def generar(destino, titulo, rotulo="", pie="UNA EDICIÓN CADA MAÑANA", bajada=""):
    """Escribe la imagen en `destino` (Path). Devuelve True si la generó."""
    if Image is None:
        return False
    img = Image.new("RGB", (ANCHO, ALTO), PAPEL)
    d = ImageDraw.Draw(img)

    # Cabezote
    gotica = _fuente("unifraktur.ttf", 70)
    w = d.textlength("Otra Lectura", font=gotica)
    d.text(((ANCHO - w) / 2, 28), "Otra Lectura", font=gotica, fill=TINTA)
    d.line([(0, 138), (ANCHO, 138)], fill=TINTA, width=2)

    # Franja de abajo
    banda = 74
    d.rectangle([(0, ALTO - banda), (ANCHO, ALTO)], fill=TINTA)
    sans_pie = _fuente("manrope.ttf", 22, 700)
    pie = pie.upper()
    wp = d.textlength(pie, font=sans_pie) + len(pie) * 3
    x = (ANCHO - wp) / 2
    for letra in pie:
        d.text((x, ALTO - banda + 24), letra, font=sans_pie, fill=PAPEL)
        x += d.textlength(letra, font=sans_pie) + 3

    # Rótulo + título, centrados en el espacio del medio
    arriba, abajo = 138, ALTO - banda
    ancho = ANCHO - 2 * MARGEN
    sans = _fuente("manrope.ttf", 22, 800)
    alto_rotulo = 44 if rotulo else 0
    cursiva = _fuente("instrument-serif-italic.ttf", 34)
    lineas_bajada = _partir(d, bajada, cursiva, ancho - 80)[:2] if bajada else []
    alto_bajada = (18 + 40 * len(lineas_bajada)) if lineas_bajada else 0
    alto_rotulo += 0
    for tam in (78, 70, 62, 56, 50, 44):
        serif = _fuente("instrument-serif.ttf", tam)
        lineas = _partir(d, titulo, serif, ancho)
        alto_linea = int(tam * 1.08)
        if len(lineas) <= 4 and len(lineas) * alto_linea + alto_rotulo + alto_bajada <= (abajo - arriba) - 50:
            break
    lineas = lineas[:4]
    total = alto_rotulo + len(lineas) * alto_linea + alto_bajada
    y = arriba + ((abajo - arriba) - total) / 2
    if rotulo:
        r = rotulo.upper()
        wr = d.textlength(r, font=sans) + len(r) * 3
        x = (ANCHO - wr) / 2
        for letra in r:
            d.text((x, y), letra, font=sans, fill=ROJO)
            x += d.textlength(letra, font=sans) + 3
        y += alto_rotulo
    for linea in lineas:
        wl = d.textlength(linea, font=serif)
        d.text(((ANCHO - wl) / 2, y), linea, font=serif, fill=TINTA)
        y += alto_linea
    if lineas_bajada:
        y += 18
        for linea in lineas_bajada:
            wl = d.textlength(linea, font=cursiva)
            d.text(((ANCHO - wl) / 2, y), linea, font=cursiva, fill=TENUE)
            y += 40

    destino.parent.mkdir(parents=True, exist_ok=True)
    img.save(destino, "PNG", optimize=True)
    return True
