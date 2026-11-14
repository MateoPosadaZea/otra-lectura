#!/usr/bin/env python3
"""Prepara las capitulares ornamentadas para el sitio.

Fuente: «Les Œuvres de François Rabelais», edición de Marty-Laveaux
(1868-1903), lettrines escaneadas en Wikimedia Commons (dominio público):
https://commons.wikimedia.org/wiki/Category:Les_Œuvres_de_François_Rabelais_-_Marty-Laveaux_-_Lettrines

Uso:
    .venv/bin/python scripts/capitulares.py <carpeta con A.jpg, B.jpg…>

Deja plantilla/capitulares/<letra>.png: solo la tinta, como máscara (el fondo
transparente), para que el sitio la pinte con su color en claro y en oscuro.
"""
import sys
from pathlib import Path

from PIL import Image, ImageOps, ImageFilter

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "plantilla" / "capitulares"
LADO = 240  # px; se muestra a ~100 px, así queda nítida en pantallas densas


def preparar(origen: Path, destino: Path):
    img = Image.open(origen).convert("L")
    # Recorta el borde blanco del escaneo y deja la letra cuadrada.
    caja = ImageOps.invert(img).point(lambda v: 255 if v > 60 else 0).getbbox()
    if caja:
        img = img.crop(caja)
    lado = max(img.size)
    lienzo = Image.new("L", (lado, lado), 255)
    lienzo.paste(img, ((lado - img.width) // 2, (lado - img.height) // 2))
    img = lienzo.resize((LADO, LADO), Image.LANCZOS)
    # Tinta = opacidad: lo oscuro queda opaco, el papel transparente.
    img = ImageOps.autocontrast(img, cutoff=2)
    alfa = ImageOps.invert(img).point(lambda v: 0 if v < 40 else min(255, int((v - 40) * 1.4)))
    alfa = alfa.filter(ImageFilter.SMOOTH)
    salida = Image.new("RGBA", (LADO, LADO), (0, 0, 0, 0))
    salida.putalpha(alfa)
    salida.save(destino, optimize=True)


def main(carpeta):
    SALIDA.mkdir(parents=True, exist_ok=True)
    hechas = []
    for f in sorted(Path(carpeta).glob("*.jpg")):
        letra = f.stem.lower()
        try:
            preparar(f, SALIDA / f"{letra}.png")
        except OSError:
            print(f"  {f.name}: no es una imagen (¿descarga incompleta?), se omite")
            continue
        hechas.append(letra.upper())
    print("capitulares:", " ".join(hechas))


if __name__ == "__main__":
    main(sys.argv[1])
