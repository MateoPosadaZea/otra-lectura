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
- `AJUSTES.md`: reglas de estilo y tono acumuladas a partir de los ajustes
  enviados desde el sitio. Tienen prioridad sobre `prompt.md` si chocan.
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
fuentes:
  - medio: "Institución o medio"
    titulo: "Título del documento o artículo"
    url: "https://…"
---
```

`categorias` usa solo estas claves (una o varias por edición, según las
fricciones y el carril de Asombro):

| Clave | Categoría | Incluye |
|---|---|---|
| `economia` | Economía | economía, finanzas públicas, trabajo |
| `salud` | Salud | salud pública, medicamentos, sistemas de salud |
| `ambiente` | Ambiente | clima, agua, energía, minería, biodiversidad |
| `sociedad` | Sociedad | justicia, seguridad, Estado, ciudades, territorio, educación |
| `ciencia` | Ciencia | ciencia, tecnología, inteligencia artificial, descubrimientos |

`temas` sigue siendo libre y específico (sirve para no repetir); las
categorías son para navegar el archivo.

Cuerpo, en este orden (ver `prompt.md` 2.0 para el contenido de cada parte):

```markdown
# Radar · 25 de septiembre de 2026

## En tres minutos

- **Tema uno en pocas palabras.** Qué pasó y quién lo está resolviendo, en una o dos frases.
- **Tema dos…** (una viñeta por fricción, y una más si hay seguimiento)

## Carril 1: Radar

### 1. Título de la fricción (lugar → lugar de la intervención) {#tema-uno}

**Qué ocurrió.** …
**Quién lo está abordando.** …
**Mecanismo en versión breve.** …
**Contrapeso.** …
**Antecedente histórico.** *(Conocimiento general.)* …
**Cruce con Mattriz.** …

### Seguimiento: tema   ← solo si hay novedad sin cambio sustantivo

Nota breve. El enlace a la edición donde se trató lo pone la plantilla a
partir del campo `seguimiento`.

## Carril 2: Asombro

**Titular corrido.** texto…

## Para conversar

**La pregunta.** Una sola pregunta abierta, sin respuesta obvia, para
discutir en la sobremesa.

**Qué puede hacer usted.** Solo si hay algo concreto, posible y
cercano (preguntar, participar, votar, revisar). Si no lo hay, se omite.

## Descartes

## Glosario

## Nota metodológica
```

- **Largo (para no desgastar):** la edición completa, sin contar Descartes,
  Glosario ni Nota metodológica, no pasa de unas 1.500 palabras (unos 7
  minutos de lectura). El build avisa si se pasa: en ese caso recortar,
  no justificar. Mejor tres temas bien entendidos que cinco a medias. Un
  día sin novedades de fondo puede tener una sola fricción, o solo
  seguimientos.
- **En tres minutos** va primero: una viñeta por fricción, en registro
  directo y sin cifras de más. Quien solo lea eso debe quedar informado.
- **Para conversar** cierra la parte de lectura: una pregunta que invite a
  pensar (no a indignarse) y, cuando exista, una acción ciudadana concreta.
- Hasta tres fricciones (dos es un buen número). Cada subtítulo es una negrita al inicio del
  párrafo que termina en punto; así lo reconoce la plantilla.
- Si no hay intervención documentada, usar **Sin salida conocida.**
  (máximo una o dos por edición, nunca todas).
- Conflicto de interés (en particular en inteligencia artificial):
  **Conflicto de interés declarado:** al inicio del ítem.
- Lo que no provenga de una fuente verificada en la edición se marca en
  cursiva y entre paréntesis: *(Conocimiento general.)* o
  *(Fuente única; no verificado.)*. Así la plantilla lo muestra con el
  sello de no verificado.
- Fuentes: van en el campo `fuentes` del frontmatter (medio, título y
  url obligatoria), no en el cuerpo; la plantilla las numera al cierre.
  Toda cifra del cuerpo debe poder rastrearse ahí.
- Cada fricción lleva un slug `{#…}` al final del título, igual a su
  entrada en `temas`. Así las ediciones siguientes pueden hacerle
  seguimiento y agregarle actualizaciones.
- `seguimiento` solo admite slugs que estén en `temas` de una edición
  anterior (el build falla si no). Cuando una fricción ya tratada tiene
  novedad: nota breve en `### Seguimiento: …` de la edición de hoy, su
  slug en `seguimiento` y, además, una entrada en `actualizaciones` de la
  edición original (`fecha`, `friccion` con su slug y `texto` de una o dos
  frases). Nunca se edita el texto de una edición ya publicada; los
  errores detectados se agregan en su campo `correcciones`.
- "Nota metodológica": número aproximado de consultas, criterios de
  priorización, qué quedó como no verificado y si la red permitió abrir
  los artículos.
- Registro y estilo según `prompt.md`: formal, tercera persona,
  atribución con institución, fecha y tipo de documento, diseño de la
  evidencia nombrado y lenguaje calibrado ante la incertidumbre. El cierre
  y el glosario van en registro directo.
- Aplicar además las reglas vigentes de `AJUSTES.md`.
- Gráficos: cuando una comparación o una evolución se entiende mejor
  viéndola (no por decorar), agregar un bloque ` ```grafico ` justo después
  del párrafo que da las cifras. Solo con cifras que estén en el texto y en
  `fuentes`; como máximo uno por fricción. Tipos: `barras` (comparar
  magnitudes), `columnas` (pocos periodos), `lineas` (tendencia, hasta 3
  series), `puntos` con `escala: log` (magnitudes muy distintas). Formato
  y ejemplo en `scripts/graficos.py`; el build falla si el bloque está mal.
- Cada idea nueva en `cruce_mattriz` se agrega también a `candidatas.md`
  como sección `## Idea` (mismo texto), con `Estado: pendiente` y cuatro
  bloques breves: **Qué resolvería.**, **Cómo.**, **Por dónde empezar.**
  (dos o tres pasos concretos; marcar "a verificar" lo que dependa de
  datos no confirmados) y **Entregable posible.** (algo pequeño y
  demostrable). Si la idea ya existe, no se duplica.

## 5. Publicar

1. `./build.sh` debe terminar sin error y crear
   `site/ediciones/<fecha>-radar.html`. Si el build se detiene, leer el
   mensaje (archivo, campo y motivo), corregir el frontmatter y repetir;
   no publicar nunca con el build fallando. Revisar que el HTML tenga los
   carriles, las fricciones y las fuentes numeradas.
2. Commit solo de `ediciones/`, `site/` y, si cambiaron, `candidatas.md`
   y `AJUSTES.md`, con el mensaje
   `Edición N · <fecha>`.
3. `git push origin main`. Si falla por red, reintentar hasta cuatro veces
   con espera creciente (2, 4, 8 y 16 segundos).
4. Cloudflare publica solo al recibir el push.

No modificar la plantilla, el build, `prompt.md` ni este archivo durante
la rutina.
