#!/usr/bin/env python3
"""Convierte los límites de Natural Earth (dominio público) en un mapa liviano
de Colombia para las piezas de redes: redes/mapas/colombia.json.

Se corre una sola vez, o cuando se quiera cambiar el detalle:

  python3 scripts/mapa-colombia.py ne_10m_admin_1_states_provinces.geojson \
      ne_10m_admin_0_countries.geojson

Los .geojson se bajan de github.com/nvkelso/natural-earth-vector (carpeta
geojson). No se guardan en el repositorio: pesan 50 MB. El resultado sí.

Proyección: equirectangular con la escala horizontal corregida por el coseno
de la latitud media (Colombia está cerca del ecuador; la deformación es
mínima). Simplificación: Douglas-Peucker, sin dependencias.
"""

import json
import math
import sys
import unicodedata

LON_MIN, LON_MAX = -79.6, -66.4   # Colombia continental, con un poco de aire
LAT_MIN, LAT_MAX = -4.6, 13.0
ANCHO = 800                        # ancho del viewBox
TOLERANCIA = 0.7                   # en unidades del viewBox
VECINOS = {"VEN": "Venezuela", "ECU": "Ecuador", "PER": "Perú", "BRA": "Brasil", "PAN": "Panamá"}

# Capitales de departamento y otras ciudades que suelen salir en las notas.
CIUDADES = {
    "Bogotá": (4.711, -74.072), "Medellín": (6.244, -75.581), "Cali": (3.452, -76.532),
    "Barranquilla": (10.964, -74.796), "Cartagena": (10.391, -75.479), "Bucaramanga": (7.119, -73.123),
    "Cúcuta": (7.894, -72.504), "Pereira": (4.814, -75.694), "Manizales": (5.070, -75.514),
    "Armenia": (4.534, -75.681), "Ibagué": (4.438, -75.232), "Neiva": (2.927, -75.282),
    "Pasto": (1.214, -77.281), "Popayán": (2.444, -76.614), "Santa Marta": (11.241, -74.199),
    "Valledupar": (10.463, -73.253), "Montería": (8.748, -75.881), "Sincelejo": (9.304, -75.398),
    "Riohacha": (11.544, -72.907), "Quibdó": (5.694, -76.661), "Villavicencio": (4.142, -73.627),
    "Tunja": (5.535, -73.367), "Yopal": (5.337, -72.395), "Arauca": (7.084, -70.759),
    "Florencia": (1.614, -75.606), "Mocoa": (1.152, -76.652), "Leticia": (-4.215, -69.940),
    "San José del Guaviare": (2.571, -72.645), "Mitú": (1.198, -70.173), "Inírida": (3.865, -67.924),
    "Puerto Carreño": (6.189, -67.486), "Buenaventura": (3.883, -77.031), "Tumaco": (1.799, -78.765),
    "San Andrés": (12.584, -81.701),
}

LAT0 = math.radians((LAT_MIN + LAT_MAX) / 2)
KX = math.cos(LAT0)
ESCALA = ANCHO / ((LON_MAX - LON_MIN) * KX)
ALTO = round((LAT_MAX - LAT_MIN) * ESCALA)


def proyectar(lon, lat):
    return ((lon - LON_MIN) * KX * ESCALA, (LAT_MAX - lat) * ESCALA)


def dp_anillo(pts, tol):
    """Un anillo cerrado se parte en el punto más lejano del inicio: si no, el
    segmento base mide cero y Douglas-Peucker lo borra todo."""
    if pts[0] == pts[-1]:
        pts = pts[:-1]
    if len(pts) < 4:
        return pts
    x0, y0 = pts[0]
    lejos = max(range(len(pts)), key=lambda i: (pts[i][0] - x0) ** 2 + (pts[i][1] - y0) ** 2)
    return dp(pts[: lejos + 1], tol)[:-1] + dp(pts[lejos:] + [pts[0]], tol)[:-1]


def dp(pts, tol):
    """Douglas-Peucker iterativo."""
    if len(pts) < 3:
        return pts
    guardar = [False] * len(pts)
    guardar[0] = guardar[-1] = True
    pila = [(0, len(pts) - 1)]
    while pila:
        a, b = pila.pop()
        (x1, y1), (x2, y2) = pts[a], pts[b]
        dx, dy = x2 - x1, y2 - y1
        largo = math.hypot(dx, dy) or 1e-9
        mejor, idx = 0, None
        for i in range(a + 1, b):
            x, y = pts[i]
            d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / largo
            if d > mejor:
                mejor, idx = d, i
        if idx is not None and mejor > tol:
            guardar[idx] = True
            pila += [(a, idx), (idx, b)]
    return [p for p, g in zip(pts, guardar) if g]


def anillos(geom):
    polis = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poli in polis:
        yield poli[0]  # solo el borde exterior: los huecos no se ven a esta escala


def camino(geom, filtro=None):
    trozos = []
    for anillo in anillos(geom):
        if filtro and not filtro(anillo):
            continue
        pts = dp_anillo([proyectar(lon, lat) for lon, lat in anillo], TOLERANCIA)
        if len(pts) < 3:
            continue
        trozos.append("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z")
    return "".join(trozos)


def continental(anillo):
    return min(lon for lon, _ in anillo) > -80.5


def visible(anillo):
    lons = [lon for lon, _ in anillo]
    lats = [lat for _, lat in anillo]
    return max(lons) > LON_MIN - 3 and min(lons) < LON_MAX + 3 and max(lats) > LAT_MIN - 3 and min(lats) < LAT_MAX + 3


def clave(nombre):
    s = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode().lower()
    return "-".join(s.replace(".", "").split())


def main(adm1, adm0):
    deps = {}
    for f in json.load(open(adm1, encoding="utf-8"))["features"]:
        p = f["properties"]
        if p.get("adm0_a3") != "COL" or not p.get("name"):
            continue
        nombre = {"Bogota": "Bogotá", "San Andrés y Providencia": "San Andrés y Providencia"}.get(p["name"], p["name"])
        if nombre == "San Andrés y Providencia":
            continue  # queda lejos del continente; se dibuja aparte cuando haga falta
        deps[clave(nombre)] = {"nombre": nombre, "d": camino(f["geometry"])}
    contorno, vecinos = "", []
    for f in json.load(open(adm0, encoding="utf-8"))["features"]:
        p = f["properties"]
        a3 = p.get("ADM0_A3")
        if a3 == "COL":
            contorno = camino(f["geometry"], continental)
        elif a3 in VECINOS:
            vecinos.append({"nombre": VECINOS[a3], "d": camino(f["geometry"], visible)})
    ciudades = {}
    for nombre, (lat, lon) in CIUDADES.items():
        x, y = proyectar(lon, lat)
        ciudades[clave(nombre)] = {"nombre": nombre, "x": round(x, 1), "y": round(y, 1)}
    salida = {
        "fuente": "Natural Earth (dominio público), simplificado por scripts/mapa-colombia.py",
        "viewBox": f"0 0 {ANCHO} {ALTO}",
        "proyeccion": {"lonMin": LON_MIN, "latMax": LAT_MAX, "kx": round(KX, 6), "escala": round(ESCALA, 4)},
        "contorno": contorno,
        "departamentos": deps,
        "vecinos": vecinos,
        "ciudades": ciudades,
    }
    with open("redes/mapas/colombia.json", "w", encoding="utf-8") as fh:
        json.dump(salida, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(deps)} departamentos, {len(vecinos)} vecinos, viewBox {salida['viewBox']}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
