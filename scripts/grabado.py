#!/usr/bin/env python3
"""Baja un grabado de Wikimedia Commons y lo deja listo para una edición.

Uso:
    .venv/bin/python scripts/grabado.py "File:Nombre del archivo.png" <slug>

Guarda imagenes/<slug>.webp (tinta y papel del sitio, máx. 1200 px de ancho)
e imprime el bloque `grabado:` para el frontmatter, con autor, fecha y
licencia tomados de Commons. Solo acepta dominio público o CC BY / CC BY-SA.
"""
import io
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

RAIZ = Path(__file__).resolve().parent.parent
UA = "OtraLectura/1.0 (https://otralectura.co)"
TINTA, PAPEL = (28, 27, 25), (216, 209, 199)
ANCHOS = [1280, 960, 500]  # tamaños de miniatura que Commons sirve sin límite


def pedir(url):
    for intento in range(4):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read(), r.headers.get_content_type()
        except urllib.error.HTTPError as err:
            if err.code != 429 or intento == 3:
                raise
            time.sleep(20 * (intento + 1))


def texto(m, k):
    return re.sub(r"<[^>]+>", "", m.get(k, {}).get("value", "")).strip()


def main(titulo, slug):
    q = urllib.parse.urlencode({"action": "query", "prop": "imageinfo", "format": "json",
                                "iiprop": "url|size|extmetadata", "titles": titulo})
    datos, _ = pedir(f"https://commons.wikimedia.org/w/api.php?{q}")
    pagina = next(iter(json.loads(datos)["query"]["pages"].values()))
    if "imageinfo" not in pagina:
        sys.exit(f"No existe en Commons: {titulo}")
    ii = pagina["imageinfo"][0]
    m = ii["extmetadata"]
    licencia = texto(m, "LicenseShortName")
    if not re.match(r"(?i)(public domain|pd|cc0|cc by(-sa)? )", licencia + " "):
        sys.exit(f"Licencia no admitida: «{licencia}»")

    # Miniatura estándar (Commons limita las descargas del original).
    original = ii["url"].split("?", 1)[0]
    base = original.replace("/commons/", "/commons/thumb/", 1)
    nombre = original.rsplit("/", 1)[1]
    crudo = None
    for ancho in ANCHOS:
        try:
            crudo, tipo = pedir(f"{base}/{ancho}px-{nombre}")
        except urllib.error.HTTPError:
            continue
        if tipo.startswith("image/"):
            break
        crudo = None
    if crudo is None:
        sys.exit("No se pudo bajar la imagen.")

    im = Image.open(io.BytesIO(crudo)).convert("RGBA")
    fondo = Image.new("RGBA", im.size, (255, 255, 255, 255))
    fondo.alpha_composite(im)
    gris = ImageEnhance.Contrast(fondo.convert("L")).enhance(1.15)
    if gris.width > 1200:
        gris = gris.resize((1200, round(gris.height * 1200 / gris.width)), Image.LANCZOS)
    salida = RAIZ / "imagenes" / f"{slug}.webp"
    salida.parent.mkdir(exist_ok=True)
    ImageOps.colorize(gris, black=TINTA, white=PAPEL).save(salida, "WEBP", quality=82, method=6)

    autor = texto(m, "Artist") or "Autor desconocido"
    fecha = texto(m, "DateTimeOriginal")
    pagina_url = "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(titulo.replace(" ", "_"))
    print(f"Guardado {salida.relative_to(RAIZ)} ({salida.stat().st_size // 1024} KB, {gris.width}x{gris.height})")
    print(f"Descripción en Commons: {texto(m, 'ImageDescription')[:300]}\n")
    print("grabado:")
    print(f"  - archivo: \"{slug}.webp\"")
    print("    pie: \"<lugar y hecho que muestra, con el año>\"")
    print(f"    credito: \"{autor}{', ' + fecha[:4] if fecha else ''} · {licencia}, vía Wikimedia Commons\"")
    print(f"    url: \"{pagina_url}\"")
    print("    alt: \"<qué se ve en la imagen, para quien no la ve>\"")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
