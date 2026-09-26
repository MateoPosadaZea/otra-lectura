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
- `PULSO.md`: las valoraciones (Liviana / Justa / Pesada) que los lectores
  dejan al final de cada edición. Si las últimas dicen "Pesada", hacer la
  de hoy más corta (menos nudos, menos palabras); si dicen "Liviana"
  de forma sostenida, se puede profundizar un poco, sin pasar el techo.
- Las cinco ediciones más recientes: sus `temas`, `seguimiento`,
  `cruce_mattriz` y "Lo que descarté", para no repetir temas (salvo como
  seguimiento) y mantener diversidad geográfica.

### Días livianos y domingo

- **Días livianos.** Si no hay novedades de fondo, se permite una edición
  corta: un solo nudo, o solo seguimientos de temas ya tratados, o
  incluso solo el carril de Asombro. Decirlo con franqueza en la nota
  metodológica ("Hoy no hubo cambios de fondo; esto es lo que vale la pena").
  No inventar urgencia.
- **Domingo** (`TZ=America/Bogota date +%u` da 7): no se abren temas
  nuevos. La edición es **"La semana en limpio"**:
  - `titulo: "La semana en limpio · <fechas>"`; en `temas` y
    `seguimiento` van los slugs de la semana que se repasan (en `temas`
    solo si se escribe un nudo nuevo sobre ellos; lo normal es
    `seguimiento`).
  - Carril Radar con `### Seguimiento: …` por cada tema que tuvo
    movimiento: qué cambió desde que se trató y qué sigue abierto.
  - "Para conversar": una pregunta de fondo que conecte dos o más temas
    de la semana.
  - Máximo unas 1.000 palabras. Sin Asombro nuevo si no hace falta.

## 2b. Elegir los temas: los de mayor impacto en la sociedad

El sitio trata **los temas de mayor impacto en la sociedad**, no los más
comentados del día. Antes de escribir, reunir de 6 a 10 candidatos que
cumplan las **cuatro condiciones de nudo** de prompt.md (el que falle una
queda fuera, sin importar su puntaje) y puntuar cada uno de 1 a 3 en cinco
criterios:

| Criterio | Pregunta | 1 | 3 |
|---|---|---|---|
| Alcance | ¿A cuántas personas afecta? | miles | millones / todo un país |
| Gravedad | ¿Toca vida, salud, ingreso, derechos o seguridad? | molestia | vida o salud |
| Duración | ¿Es reversible o deja efectos por años? | pasajero | generaciones |
| Cercanía | ¿Qué tanto toca a Colombia o América Latina? | lejano | directo |
| Decisión | ¿Se está decidiendo algo ahora (ley, presupuesto, fallo, elección)? | nada en curso | decisión inminente |

**Gravedad y cercanía valen doble** (pedido de Mateo, 2026-09-25):
total = alcance + 2 × gravedad + duración + 2 × cercanía + decisión.
Se eligen los de mayor puntaje (máximo 21). Reglas:
- Al menos **un tema colombiano de alto impacto** por edición (si no hay
  novedad, un seguimiento de uno ya tratado).
- El tema puede ser **estructural y de largo plazo** (pensiones, salud,
  seguridad, empleo, clima, educación, agua, alimentación…): basta un
  **hecho reciente** que lo reactive (informe, cifra, votación, fallo,
  anuncio). No hace falta que sea "la noticia del día"; tampoco elegir un
  tema menor solo porque es reciente.
- La diversidad geográfica se busca entre temas de impacto comparable, no
  a costa del impacto.
- En la **Nota metodológica** va una tabla corta con el puntaje de los
  temas elegidos y de los principales descartados (los criterios en 1 a 3,
  y el total ya ponderado), para que el criterio se
  pueda discutir y calibrar.

## 3. Investigar (sin prisa: la calidad de las fuentes es lo que distingue al sitio)

El barrido puede tomar el tiempo que haga falta. La prensa sirve para
saber **qué pasó**; el análisis, las cifras de fondo, los casos de
solución y el contrapeso deben venir, siempre que existan, de fuentes
primarias y académicas. Muchos medios tienen posturas e intereses: se usan
para el hecho puntual, no para interpretarlo.

1. **El hecho (prensa).** Buscar con WebSearch, en español y en inglés,
   los hechos recientes (idealmente de las últimas 48 horas, o de la
   última semana si reactivan un tema estructural de alto impacto): mundo,
   América Latina y Colombia. Cruzar cada dato con al menos dos medios de líneas
   editoriales distintas; si solo hay uno, decirlo.
2. **El documento de origen (oficial).** Ir a la fuente primaria que la
   noticia cita: el informe, la ley, el proyecto de presupuesto, la
   sentencia, el boletín epidemiológico, el comunicado de la entidad
   (DANE, Banco de la República, Minhacienda, INS, Ideam, OMS, CEPAL, Banco
   Mundial…).
3. **El conocimiento (academia).** Para "Por qué se repite", "Quién lo está
   resolviendo", "El cómo" y "Contrapeso", buscar estudios: revistas
   revisadas por pares, evaluaciones de impacto, revisiones sistemáticas,
   documentos de trabajo de universidades y centros serios (PubMed/PMC,
   SciELO, Redalyc, NBER, SSRN, J-PAL, 3ie, Cochrane, Google Académico vía
   WebSearch con "site:", "pdf", "systematic review", "impact evaluation",
   "evaluación de impacto", "revisión sistemática"). Preferir evidencia de
   diseño fuerte (ensayos, cuasi-experimentos, revisiones) y decir el
   diseño en el texto.
4. **Los datos.** Cuando una cifra se pueda tomar de una base de datos
   (DANE, datos.gov.co, Our World in Data, Banco Mundial), tomarla de ahí.
5. **Centros de pensamiento y ONG**: útiles, pero con postura; si se
   citan, decir quiénes son y, si aplica, su orientación.

Metas por edición (guía, no excusa para rellenar):
- Cada nudo con al menos **una fuente académica** y **una oficial o de
  datos**, además de la prensa.
- Al menos la **mitad de las fuentes no son de prensa**. Si para un tema
  solo hay prensa, se dice en la nota metodológica ("para este tema no se
  encontró evidencia académica").
- Wikipedia y enciclopedias solo para orientarse, nunca como fuente de una
  cifra.

- Intentar abrir los documentos con WebFetch. Si la red lo bloquea,
  trabajar con los resultados de búsqueda (resúmenes, abstracts) y decirlo
  en la nota metodológica; no atribuir a un estudio más de lo que dice su
  resumen.
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
titulo: "Titular que resuma los nudos del día"
temas: [tema-uno, tema-dos]
categorias: [economia, salud]
lugares: [Colombia, ...]
cruce_mattriz: []
seguimiento: []
fuentes:
  - medio: "Institución, revista o medio"
    titulo: "Título del documento o artículo"
    url: "https://…"
    tipo: academica   # academica | oficial | datos | organizacion | prensa | referencia
---
```

`categorias` usa solo estas claves (una o varias por edición, según los
nudos y el carril de Asombro):

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

## Carril 1: Radar

### 1. Título del nudo (lugar → lugar de la intervención) {#tema-uno}

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

## Descartes          ← no se muestra en el sitio; sirve para no repetir temas

## Glosario

## Nota metodológica
```

- **Largo (para no desgastar):** la edición completa, sin contar Descartes,
  Glosario ni Nota metodológica, no pasa de unas 1.500 palabras (unos 7
  minutos de lectura). El build avisa si se pasa: en ese caso recortar,
  no justificar. Mejor tres temas bien entendidos que cinco a medias. Un
  día sin novedades de fondo puede tener un solo nudo, o solo
  seguimientos.
- Sin resúmenes rápidos al comienzo ("En tres minutos" ya no existe): el
  sitio apuesta por la profundidad. El índice de la edición lo genera la
  plantilla a partir de los títulos de los nudos.
- **Para conversar** cierra la parte de lectura: una pregunta que invite a
  pensar (no a indignarse) y, cuando exista, una acción ciudadana concreta.
- Hasta tres nudos (dos es un buen número). Cada subtítulo es una negrita al inicio del
  párrafo que termina en punto; así lo reconoce la plantilla.
- Si no hay intervención documentada, usar **Sin salida conocida.**
  (máximo una o dos por edición, nunca todas).
- Conflicto de interés (en particular en inteligencia artificial):
  **Conflicto de interés declarado:** al inicio del ítem.
- Lo que no provenga de una fuente verificada en la edición se marca en
  cursiva y entre paréntesis: *(Conocimiento general.)* o
  *(Fuente única; no verificado.)*. Así la plantilla lo muestra con el
  sello de no verificado.
- Fuentes: van en el campo `fuentes` del frontmatter (medio, título, url
  obligatoria y `tipo`), no en el cuerpo; la plantilla las numera al
  cierre y muestra cuántas son académicas, oficiales, de datos, de
  organizaciones y de prensa.
  Toda cifra del cuerpo debe poder rastrearse ahí.
- Cada nudo lleva un slug `{#…}` al final del título, igual a su
  entrada en `temas`. Así las ediciones siguientes pueden hacerle
  seguimiento y agregarle actualizaciones.
- `seguimiento` solo admite slugs que estén en `temas` de una edición
  anterior (el build falla si no). Cuando un nudo ya tratado tiene
  novedad: nota breve en `### Seguimiento: …` de la edición de hoy, su
  slug en `seguimiento` y, además, una entrada en `actualizaciones` de la
  edición original (`fecha`, `nudo` con su slug y `texto` de una o dos
  frases). Nunca se edita el texto de una edición ya publicada; los
  errores detectados se agregan en su campo `correcciones`. (La excepción
  son los cambios que los editores hacen con "Editar el texto" en el
  sitio; esos los aplica la revisión horaria.)
- "Nota metodológica": número aproximado de consultas, criterios de
  priorización, qué quedó como no verificado y si la red permitió abrir
  los artículos.
- Registro y estilo según `prompt.md`: formal, tercera persona,
  atribución con institución, fecha y tipo de documento, diseño de la
  evidencia nombrado y lenguaje calibrado ante la incertidumbre. El cierre
  y el glosario van en registro directo.
- Aplicar además las reglas vigentes de `AJUSTES.md`.
- Gráficos (ver también AJUSTES.md): cuando una comparación o una evolución se entiende mejor
  viéndola (no por decorar), agregar un bloque ` ```grafico ` justo después
  del párrafo que da las cifras. Solo con cifras que estén en el texto y en
  `fuentes`; como máximo uno por nudo. Tipos: `barras` (comparar
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
   carriles, los nudos y las fuentes numeradas.
2. Commit solo de `ediciones/`, `site/` y, si cambiaron, `candidatas.md`
   y `AJUSTES.md`, con el mensaje
   `Edición N · <fecha>`.
3. `git push origin main`. Si falla por red, reintentar hasta cuatro veces
   con espera creciente (2, 4, 8 y 16 segundos).
4. Cloudflare publica solo al recibir el push.

No modificar la plantilla, el build, `prompt.md` ni este archivo durante
la rutina.
