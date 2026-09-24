"""Frontmatter de las ediciones: un subconjunto de YAML, sin dependencias.

Soporta lo que usan las ediciones:
  clave: valor                 escalar, con o sin comillas
  clave: "texto largo que      escalar entre comillas en varias líneas
          sigue aquí"          (las líneas se unen con un espacio)
  clave: [a, b, "c, d"]        lista en línea
  clave:                       lista de escalares
    - a
  clave:                       lista de mapas
    - fecha: 2026-10-02
      texto: "…"
  # comentario                 comentarios de línea completa o al final

Todos los escalares se devuelven como texto. Cualquier cosa fuera de este
subconjunto es un error con número de línea, no una suposición.
"""

import re

RE_CLAVE = re.compile(r"^([A-Za-z_][\w-]*)\s*:(?:\s+(.*))?$")


class ErrorFrontmatter(Exception):
    pass


def separar(texto):
    """Devuelve (lineas_del_frontmatter, cuerpo, numero_de_la_primera_linea)."""
    lineas = texto.split("\n")
    if not lineas or lineas[0].strip() != "---":
        raise ErrorFrontmatter("línea 1: falta el frontmatter (debe empezar con '---')")
    for i, l in enumerate(lineas[1:], 1):
        if l.strip() in ("---", "..."):
            return lineas[1:i], "\n".join(lineas[i + 1:]), 2
    raise ErrorFrontmatter("el frontmatter no se cierra con '---'")


def _sin_comentario(s):
    """Quita un comentario final (' #…') que no esté dentro de comillas."""
    comilla = None
    for i, c in enumerate(s):
        if comilla:
            if c == comilla and s[i - 1] != "\\":
                comilla = None
        elif c in "\"'":
            comilla = c
        elif c == "#" and (i == 0 or s[i - 1] in " \t"):
            return s[:i].rstrip()
    return s.rstrip()


def parsear(texto):
    """Devuelve (meta, cuerpo). Lanza ErrorFrontmatter si algo no cuadra."""
    crudas, cuerpo, primera = separar(texto)
    lineas = []
    for n, linea in enumerate(crudas, primera):
        if "\t" in linea[: len(linea) - len(linea.lstrip())]:
            raise ErrorFrontmatter(f"línea {n}: usa espacios, no tabuladores, para indentar")
        contenido = _sin_comentario(linea.strip())
        if contenido:
            lineas.append([n, len(linea) - len(linea.lstrip()), contenido])
    if not lineas:
        return {}, cuerpo
    p = _Parser(lineas)
    valor = p.bloque(0, lineas[0][1])
    if p.i < len(lineas):
        n = lineas[p.i][0]
        raise ErrorFrontmatter(f"línea {n}: indentación inesperada")
    if not isinstance(valor, dict):
        raise ErrorFrontmatter(f"línea {lineas[0][0]}: el frontmatter debe ser una lista de 'clave: valor'")
    return valor, cuerpo


class _Parser:
    def __init__(self, lineas):
        self.l = lineas
        self.i = 0

    def _actual(self):
        return self.l[self.i] if self.i < len(self.l) else None

    def bloque(self, i, indent):
        self.i = i
        n, ind, cont = self.l[i]
        if cont == "-" or cont.startswith("- "):
            return self.lista(indent)
        return self.mapa(indent)

    def mapa(self, indent):
        mapa = {}
        while (lin := self._actual()) and lin[1] == indent:
            n, _, cont = lin
            m = RE_CLAVE.match(cont)
            if not m:
                raise ErrorFrontmatter(f"línea {n}: se esperaba 'clave: valor' y hay «{cont}»")
            clave, resto = m.group(1).lower(), m.group(2)
            if clave in mapa:
                raise ErrorFrontmatter(f"línea {n}: la clave '{clave}' está repetida")
            self.i += 1
            if resto is None or resto == "":
                sig = self._actual()
                mapa[clave] = self.bloque(self.i, sig[1]) if sig and sig[1] > indent else None
            else:
                mapa[clave] = self.escalar(resto, n, indent)
        lin = self._actual()
        if lin and lin[1] > indent:
            raise ErrorFrontmatter(f"línea {lin[0]}: indentación inesperada")
        return mapa

    def lista(self, indent):
        lista = []
        while (lin := self._actual()) and lin[1] == indent and (lin[2] == "-" or lin[2].startswith("- ")):
            n, _, cont = lin
            item = cont[1:].lstrip()
            if not item:
                self.i += 1
                sig = self._actual()
                if not sig or sig[1] <= indent:
                    raise ErrorFrontmatter(f"línea {n}: elemento de lista vacío")
                lista.append(self.bloque(self.i, sig[1]))
            elif RE_CLAVE.match(item) and not item.startswith(("'", '"')):
                # "- clave: valor": un mapa cuyas claves siguen alineadas con "clave".
                sangria = indent + (len(cont) - len(item))
                self.l[self.i] = [n, sangria, item]
                lista.append(self.mapa(sangria))
            else:
                self.i += 1
                lista.append(self.escalar(item, n, indent))
        return lista

    def escalar(self, texto, n, indent):
        # Continuaciones: líneas más indentadas que la clave o el guion.
        partes = [texto]
        abierta = texto[:1] in "\"'" and not _cierra(texto)
        while (lin := self._actual()) and lin[1] > indent:
            if not abierta and (lin[2].startswith("- ") or RE_CLAVE.match(lin[2])):
                break
            partes.append(lin[2])
            self.i += 1
            if abierta and _cierra(" ".join(partes)):
                abierta = False
                break
        if abierta:
            raise ErrorFrontmatter(f"línea {n}: falta cerrar la comilla")
        return _convertir(" ".join(partes), n)


def _cierra(s):
    q = s[0]
    return len(s) >= 2 and s.endswith(q) and not s.endswith("\\" + q)


def _convertir(s, n):
    if s[:1] in "\"'":
        if not _cierra(s):
            raise ErrorFrontmatter(f"línea {n}: comillas mal cerradas en «{s}»")
        interior = s[1:-1]
        return interior.replace('\\"', '"').replace("\\\\", "\\") if s[0] == '"' else interior.replace("''", "'")
    if s.startswith("["):
        if not s.endswith("]"):
            raise ErrorFrontmatter(f"línea {n}: la lista en línea no se cierra con ']'")
        return [_convertir(x.strip(), n) for x in _partir_comas(s[1:-1]) if x.strip()]
    return s


def _partir_comas(s):
    partes, actual, comilla = [], "", None
    for c in s:
        if comilla:
            comilla = None if c == comilla else comilla
        elif c in "\"'":
            comilla = c
        elif c == ",":
            partes.append(actual)
            actual = ""
            continue
        actual += c
    partes.append(actual)
    return partes
