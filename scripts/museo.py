#!/usr/bin/env python3
"""Busca y baja obras de dominio público de museos con acceso abierto.

Fuentes (todas gratis, sin clave):
  aic        Art Institute of Chicago (solo obras marcadas de dominio público)
  cleveland  Cleveland Museum of Art (solo CC0)
  met        Metropolitan Museum of Art (solo Open Access, dominio público)

Uso:
    .venv/bin/python scripts/museo.py buscar "<términos en inglés>" [aic|cleveland|met|todas]
    .venv/bin/python scripts/museo.py bajar <fuente>:<id> <slug>            # imagen de una edición
    .venv/bin/python scripts/museo.py bajar <fuente>:<id> banco/<carpeta>   # banco para los reels

`bajar` deja la imagen en tinta y papel del sitio (máx. 1200 px de ancho) en
imagenes/<slug>.webp, o en redes/banco/<carpeta>/<fuente>-<id>.webp, y para
una edición imprime el bloque `grabado:` del frontmatter con el crédito.
"""
import io
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

RAIZ = Path(__file__).resolve().parent.parent
UA = "OtraLectura/1.0 (https://otralectura.co)"
TINTA, PAPEL = (22, 19, 15), (239, 231, 214)


def pedir(url, intentos=3):
    for i in range(intentos):
        req = urllib.request.Request(url, headers={"User-Agent": UA, "AIC-User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read()
        except urllib.error.HTTPError as err:
            if err.code not in (429, 502, 503) or i == intentos - 1:
                raise
            time.sleep(10 * (i + 1))


def jpedir(url):
    return json.loads(pedir(url))


# Cada fuente devuelve fichas: {id, titulo, autor, fecha, tecnica, imagen, pagina, licencia}.

def aic_ficha(d):
    return {
        "id": f"aic:{d['id']}", "titulo": d.get("title") or "", "autor": (d.get("artist_display") or "").split("\n")[0],
        "fecha": d.get("date_display") or "", "tecnica": d.get("medium_display") or "",
        "imagen": f"https://www.artic.edu/iiif/2/{d['image_id']}/full/1200,/0/default.jpg" if d.get("image_id") else "",
        "pagina": f"https://www.artic.edu/artworks/{d['id']}", "licencia": "Dominio público",
        "museo": "Art Institute of Chicago",
    }


CAMPOS_AIC = "id,title,artist_display,date_display,medium_display,image_id,is_public_domain"


def aic_buscar(q, n):
    url = ("https://api.artic.edu/api/v1/artworks/search?" + urllib.parse.urlencode(
        {"q": q, "limit": n * 3, "fields": CAMPOS_AIC}))
    return [aic_ficha(d) for d in jpedir(url)["data"] if d.get("is_public_domain") and d.get("image_id")][:n]


def aic_uno(i):
    d = jpedir(f"https://api.artic.edu/api/v1/artworks/{i}?fields={CAMPOS_AIC}")["data"]
    if not d.get("is_public_domain"):
        sys.exit("Esa obra del Art Institute no es de dominio público.")
    return aic_ficha(d)


def cle_ficha(d):
    autor = (d.get("creators") or [{}])[0].get("description", "") or (d.get("culture") or [""])[0]
    return {
        "id": f"cleveland:{d['id']}", "titulo": d.get("title") or "", "autor": autor.split(" (")[0],
        "fecha": d.get("creation_date") or "", "tecnica": d.get("technique") or d.get("type") or "",
        "imagen": ((d.get("images") or {}).get("print") or (d.get("images") or {}).get("web") or {}).get("url", ""),
        "pagina": d.get("url") or "", "licencia": "CC0 (dominio público)", "museo": "Cleveland Museum of Art",
    }


def cle_buscar(q, n):
    url = "https://openaccess-api.clevelandart.org/api/artworks/?" + urllib.parse.urlencode(
        {"q": q, "cc0": 1, "has_image": 1, "limit": n})
    return [cle_ficha(d) for d in jpedir(url)["data"]]


def cle_uno(i):
    d = jpedir(f"https://openaccess-api.clevelandart.org/api/artworks/{i}")["data"]
    if d.get("share_license_status") != "CC0":
        sys.exit("Esa obra de Cleveland no es CC0.")
    return cle_ficha(d)


def met_ficha(d):
    return {
        "id": f"met:{d['objectID']}", "titulo": d.get("title") or "", "autor": d.get("artistDisplayName") or d.get("culture") or "",
        "fecha": d.get("objectDate") or "", "tecnica": d.get("medium") or "",
        "imagen": d.get("primaryImage") or d.get("primaryImageSmall") or "",
        "pagina": d.get("objectURL") or "", "licencia": "Dominio público", "museo": "The Metropolitan Museum of Art",
    }


def met_uno(i):
    d = jpedir(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{i}")
    if not d.get("isPublicDomain"):
        sys.exit("Esa obra del Met no es de dominio público.")
    return met_ficha(d)


def met_buscar(q, n):
    url = "https://collectionapi.metmuseum.org/public/collection/v1.1/search?" + urllib.parse.urlencode(
        {"q": q, "hasImages": "true", "limit": n * 3})
    fichas = []
    for i in jpedir(url).get("objectIDs") or []:
        try:
            d = jpedir(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{i}")
        except Exception:
            continue
        if d.get("isPublicDomain") and (d.get("primaryImage") or d.get("primaryImageSmall")):
            fichas.append(met_ficha(d))
        if len(fichas) >= n:
            break
    return fichas


FUENTES = {"aic": (aic_buscar, aic_uno), "cleveland": (cle_buscar, cle_uno), "met": (met_buscar, met_uno)}


def buscar(q, cual="todas", n=6):
    for nombre in (FUENTES if cual == "todas" else [cual]):
        try:
            fichas = FUENTES[nombre][0](q, n)
        except Exception as err:
            print(f"[{nombre}] no respondió: {err}")
            continue
        for f in fichas:
            print(f"{f['id']:<18} {f['titulo'][:70]} · {f['autor'][:40]} · {f['fecha']} · {f['tecnica'][:40]}")


def entintar(crudo):
    im = Image.open(io.BytesIO(crudo)).convert("RGBA")
    fondo = Image.new("RGBA", im.size, (255, 255, 255, 255))
    fondo.alpha_composite(im)
    gris = ImageEnhance.Contrast(fondo.convert("L")).enhance(1.15)
    if gris.width > 1200:
        gris = gris.resize((1200, round(gris.height * 1200 / gris.width)), Image.LANCZOS)
    return ImageOps.colorize(gris, black=TINTA, white=PAPEL)


def bajar(ref, destino):
    fuente, _, i = ref.partition(":")
    if fuente not in FUENTES or not i:
        sys.exit("La referencia es <fuente>:<id>, por ejemplo aic:9381.")
    f = FUENTES[fuente][1](i)
    if not f["imagen"]:
        sys.exit("La obra no trae imagen descargable.")
    try:
        crudo = pedir(f["imagen"])
    except urllib.error.HTTPError as err:
        # El Art Institute sirve algunas obras solo hasta 843 px de ancho.
        if err.code != 403 or "/full/1200," not in f["imagen"]:
            raise
        crudo = pedir(f["imagen"].replace("/full/1200,", "/full/843,"))
    im = entintar(crudo)
    if destino.startswith("banco/"):
        salida = RAIZ / "redes" / destino / f"{fuente}-{i}.webp"
    else:
        salida = RAIZ / "imagenes" / f"{destino}.webp"
    salida.parent.mkdir(parents=True, exist_ok=True)
    im.save(salida, "WEBP", quality=82, method=6)
    print(f"Guardado {salida.relative_to(RAIZ)} ({salida.stat().st_size // 1024} KB, {im.width}x{im.height})")
    print(f"Obra: {f['titulo']} · {f['autor']} · {f['fecha']} · {f['tecnica']}\n")
    if destino.startswith("banco/"):
        return
    print("grabado:")
    print(f"  - archivo: \"{destino}.webp\"")
    print("    pie: \"<qué muestra, autor y año>\"")
    print(f"    credito: \"{f['autor'] or 'Autor desconocido'}, {f['fecha']} · {f['licencia']}, {f['museo']}\"")
    print(f"    url: \"{f['pagina']}\"")
    print("    alt: \"<qué se ve en la imagen, para quien no la ve>\"")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == "buscar":
        buscar(a[1], a[2] if len(a) > 2 else "todas")
    elif len(a) == 3 and a[0] == "bajar":
        bajar(a[1], a[2])
    else:
        sys.exit(__doc__)
