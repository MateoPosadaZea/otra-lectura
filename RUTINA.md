# Rutina diaria de Otra lectura

Instrucciones para la sesión automática que genera y publica una edición
cada mañana (5:00 a. m. hora Colombia, lista antes de las 6:00). Este
archivo es la fuente de verdad de la rutina: para cambiar cómo trabaja,
se edita aquí, no en la tarea programada.

Lectores: Mateo y su papá. Lo que más importa es el contexto, la historia
y las soluciones: qué pasó, por qué se repite, quién lo está resolviendo,
con qué contrapeso y qué patrón histórico ayuda a entenderlo.

## 1. Preparar

1. Si el repo no está en el directorio de trabajo, clonarlo:
   `git clone https://github.com/MateoPosadaZea/otra-lectura`.
2. Trabajar en `main`: `git checkout main && git pull origin main`.
   La publicación es directa a `main`; no abrir ramas ni pull requests.
3. Fecha de hoy en Colombia: `TZ=America/Bogota date +%F`.
4. Si ya existe `ediciones/<fecha>-radar*.md`, terminar sin hacer nada.
5. Número de edición: el mayor `edicion:` de `ediciones/*.md` más uno.

## 2. Leer antes de escribir

- `prompt.md`: formato editorial completo. Es obligatorio.
- `README.md`: tabla de convenciones de markdown que entiende la plantilla.
- Las cinco ediciones más recientes: sus `temas`, `seguimiento`,
  `cruce_mattriz` y "Lo que descarté", para no repetir temas (salvo como
  seguimiento) y mantener diversidad geográfica.

## 3. Investigar

- Buscar con WebSearch, en español y en inglés, noticias de las últimas
  24 a 48 horas: mundo, América Latina y Colombia.
- Intentar abrir los artículos con WebFetch. Si la red lo bloquea,
  trabajar con los resultados de búsqueda y cruzar cada cifra clave con al
  menos dos resultados distintos.
- Para "Quién lo está resolviendo", buscar casos documentados con
  resultados medibles, en cualquier país.
- Buscar activamente críticas y resultados mixtos para "Contrapeso".
- Lo que no se pueda confirmar en fuentes va marcado
  *(Conocimiento general.)* o *(Conocimiento general, no verificado.)*.
  Nunca presentar como verificado algo que no lo está.

## 4. Escribir `ediciones/<fecha>-radar.md`

Frontmatter:

```yaml
---
fecha: AAAA-MM-DD
edicion: N
titulo: "Titular que resuma las fricciones del día"
temas: [tema-uno, tema-dos]
categorias: [economia, salud]
lugares: [Colombia, ...]
cruce_mattriz: []
seguimiento: []
---
```

`categorias` usa solo estas claves (una o varias por edición, según las
fricciones y el carril de Asombro):

| Clave | Categoría |
|---|---|
| `economia` | Economía |
| `salud` | Salud |
| `ambiente` | Ambiente y clima |
| `energia` | Energía |
| `justicia` | Justicia y Estado |
| `territorio` | Ciudades y territorio |
| `sociedad` | Sociedad |
| `ciencia` | Ciencia y tecnología |

`temas` sigue siendo libre y específico (sirve para no repetir); las
categorías son para navegar el archivo.

Cuerpo, en este orden (ver `prompt.md` para el contenido de cada parte):

```markdown
# Radar · 24 de septiembre de 2026

## Carril 1: Radar

### 1. Título de la fricción (lugar → lugar de la solución)

**Qué pasó.** …
**Quién lo está resolviendo.** …
**El cómo, en corto.** …
**Contrapeso.** …
**Qué dice la historia.** *(Conocimiento general.)* …
**Cruce con Mattriz.** …

### Seguimiento: tema   ← solo si hay novedad sin cambio de fondo

## Carril 2: Asombro

**Titular corrido.** texto…

## Lo que descarté

## Glosario

## Lo que hice y para qué

## Fuentes
```

- De dos a cuatro fricciones. Cada subtítulo es una negrita al inicio del
  párrafo que termina en punto; así lo reconoce la plantilla.
- Si no hay solución documentada, usar **Sin salida conocida.** (máximo una
  o dos por edición, nunca todas).
- Conflicto de interés (noticias sobre Anthropic, sus competidores o la IA
  en general): **Conflicto de interés declarado:** al inicio del ítem.
- "Lo que hice y para qué": cuántas búsquedas, qué se priorizó, qué quedó
  marcado como no verificado y si la red permitió abrir los artículos.
- "Fuentes": lista de enlaces markdown a las fuentes usadas, agrupadas por
  fricción.
- Tono profesional y académico según la sección "Tono" de `prompt.md`:
  registro formal, redacción impersonal, atribución explícita de fuentes y
  cifras con unidad, periodo y fuente. Cerrar con una decisión o una
  pregunta analítica abierta, nunca con un llamado a la acción.

## 5. Publicar

1. `./build.sh` debe terminar sin error y crear
   `site/ediciones/<fecha>-radar.html`. Revisar que el HTML tenga los
   carriles y las fricciones.
2. Commit solo de `ediciones/` y `site/`, con el mensaje
   `Edición N · <fecha>`.
3. `git push origin main`. Si falla por red, reintentar hasta cuatro veces
   con espera creciente (2, 4, 8 y 16 segundos).
4. Cloudflare publica solo al recibir el push.

No modificar la plantilla, el build, `prompt.md` ni este archivo durante
la rutina.
