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
6. **Revisar las decisiones en seguimiento** (campo `decisiones` de las
   ediciones anteriores). Para cada una en `pendiente` cuyo `plazo` ya
   pasó o esté a menos de siete días, o sin plazo y sin revisar hace más
   de un mes (`revisada`), buscar si hay noticia. Si la hay: cambiar
   `estado` (tomada, aplazada, sin_decision), escribir en `nota` qué pasó
   en una frase, poner `revisada` con la fecha de hoy y agregar una
   entrada en `actualizaciones` de esa edición. Si no hay noticia, solo
   poner `revisada`. No se cambia el texto de la edición. Memoria (desde
   el 2026-10-08): si el plazo venció sin decisión, sumar 1 a
   `incumplidos`; si la promesa venía de antes, poner `prometido_desde`
   con la fecha del primer anuncio. La página Memoria las muestra solas.
7. Si existe `borradores/<fecha>-*.md` (un borrador aprobado por los
   editores para hoy), no escribir otra edición: moverlo a `ediciones/`
   con `git mv`, poner en `edicion:` el número del paso 5, revisar que
   las cifras y fechas sigan vigentes (si algo cambió, corregirlo y
   decirlo en la nota metodológica), adaptar el texto a las reglas de
   estilo vigentes en AJUSTES.md (lenguaje sencillo), ejecutar `./build.sh` y publicar
   como siempre.

## 2. Leer antes de escribir

- `prompt.md`: formato editorial completo. Es obligatorio.
- `AJUSTES.md`: reglas de estilo y tono acumuladas a partir de los ajustes
  enviados desde el sitio. Tienen prioridad sobre `prompt.md` si chocan.
- `README.md`: tabla de convenciones de markdown que entiende la plantilla.
- `PULSO.md`: las valoraciones (Liviana / Justa / Pesada) que los lectores
  dejan al final de cada edición. Si las últimas dicen "Pesada", hacer la
  de hoy más corta (menos palabras); si dicen "Liviana"
  de forma sostenida, se puede profundizar un poco, sin pasar el techo.
- Las cinco ediciones más recientes: sus `temas`, `seguimiento`,
  `cruce_mattriz` y "Lo que descartamos", para no repetir temas (salvo como
  seguimiento) y mantener diversidad geográfica.

### Días livianos y domingo

- **Días livianos.** Si no hay novedades de fondo, se permite una edición
  corta: el nudo más breve, o un seguimiento de fondo de un tema ya
  tratado. Decirlo con franqueza en la nota
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
- **Primer sábado de cada mes: "Imaginemos"** (pedido de Mateo,
  2026-09-29, inspirado en *Imaginar la democracia*). Ese día no se busca
  un tema nuevo: se toma un nudo ya tratado (el de mayor puntaje o el que
  más se ha movido en el mes) y se diseña cómo podría funcionar mejor. Si
  el primer sábado cae un día 1 con otro compromiso, igual aplica.
  - `titulo: "Imaginemos: <la propuesta en pocas palabras>"`; en `temas`
    un slug nuevo `imaginemos-<tema>`; en `seguimiento` el slug del nudo
    original (así la edición enlaza a donde se trató).
  - Cuerpo: `### Imaginemos: <título> {#imaginemos-<tema>}` con estas
    etiquetas, en este orden:
    **El problema en una línea.** Lo que ya se contó, en dos frases.
    **Qué ya se probó.** Lo que funcionó o fracasó aquí y en otros países,
    con fuentes.
    **La propuesta.** Un diseño concreto: qué se hace, quién lo hace,
    con qué reglas. Una sola propuesta, no un menú.
    **Cuánto costaría y de dónde sale.** Cifras con fuente, o un orden de
    magnitud razonado y marcado como estimación.
    **Qué podría salir mal.** Los riesgos y quién se opondría, en su mejor
    argumento.
  - Luego las secciones de siempre: Quién decide y cuándo (aquí: quién
    tendría que aprobar la propuesta y por qué vía), La paradoja del día,
    Para conversar (¿usted la apoyaría? ¿qué le cambiaría?).
  - La propuesta es de Otra lectura y así se dice: un ejercicio para
    pensar, no una verdad. Pareja con todos los bandos; nada de
    propuestas de un partido presentadas como propias.
  - Mismo techo: unas 1.100 palabras.

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
Se elige **el de mayor puntaje** (máximo 21). Cada edición trata un solo
tema.

**Uno, dos o tres temas por día (desde el 2026-10-05, pedido de Mateo).**
El día no tiene que ser de un solo tema. Después del principal, entra un
segundo y un tercero solo si también mueven la aguja: **17 puntos o más**
y que no sea el mismo asunto que otro del día ni uno tratado en los
últimos siete días (salvo novedad de fondo). Si solo uno llega, se
publica uno y ya: no se rellena. Reglas:
- Además de los nudos, puede entrar **un tema de contexto** al día
  (prompt.md, «Temas de contexto»): un hecho que no es nudo pero toca a
  Colombia por canales concretos (por ejemplo, las elecciones de Brasil
  y lo que se juega en comercio, Amazonía, agua, Venezuela y frontera).
  Se puntúa igual; las cuatro condiciones de nudo no aplican.
- **Temas del mundo (desde el 2026-10-07, pedido de Mateo: "no veo mucho
  noticias del mundo… que muevan la aguja… si hay algo importante, si no
  no").** El barrido incluye siempre el mundo, no solo como fuente de
  casos. Un hecho de otro país entra (como nudo o como tema de contexto)
  con los mismos filtros y el mismo umbral de 17 puntos. Para que la
  geografía no lo deje fuera por defecto, la **cercanía** de un tema del
  mundo se puntúa por el canal real por el que llega a Colombia, no por
  la distancia: 3 si cambia ya precios, clima, salud, migración,
  seguridad o tecnología que se usan aquí; 2 si los cambiará en meses;
  1 si no hay canal claro. Siempre se dice ese canal en «En pocas
  palabras» (qué tiene que ver con nosotros). Como máximo uno al día;
  si ninguno llega a 17, no entra. Nunca se rellena.
- Cada tema va en su propia edición, con su número, su grabado y su
  «Para leer más». El principal es `ediciones/<fecha>-radar.md` y lleva
  el número más bajo del día (abre la retícula de la portada); los demás
  van en `ediciones/<fecha>-<tema-corto>.md`, con los números siguientes.
- Cada edición respeta el techo de palabras. Con dos o tres temas, los
  secundarios van más cortos (unas 900 palabras de lectura), para que el
  día completo se pueda leer sin cansancio.
- La tabla de puntaje de la nota metodológica va en la edición principal
  y cubre todos los elegidos y los descartados.

Reglas de selección:
- A igualdad de puntaje, preferir el **tema colombiano** (si no hay
  novedad, un seguimiento de fondo de uno ya tratado).
- El tema puede ser **estructural y de largo plazo** (pensiones, salud,
  seguridad, empleo, clima, educación, agua, alimentación…): basta un
  **hecho reciente** que lo reactive (informe, cifra, votación, fallo,
  anuncio). No hace falta que sea "la noticia del día"; tampoco elegir un
  tema menor solo porque es reciente.
- La diversidad geográfica se busca entre temas de impacto comparable, no
  a costa del impacto.
- En la **Nota metodológica** va una tabla corta con el puntaje de los
  tema elegido y de los principales descartados (los criterios en 1 a 3,
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
  en la nota metodológica, en plural y en lenguaje llano («no pudimos abrir
  el documento completo»); no atribuir a un estudio más de lo que dice su
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
titulo: "Titular del nudo del día"
temas: [tema-uno]
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
nudo):

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

### Título del nudo {#tema-uno}

**En pocas palabras.** Dos o tres frases: de qué se trata y por qué
importa. Quien lea solo esto ya entendió.
**Qué pasó.** Con un ejemplo cotidiano que haga de puente (la tienda de
barrio, la recarga del celular) y luego los hechos.
**Cómo llegamos aquí.** El mecanismo, en pocas viñetas cortas.
**Ya pasó antes.** El antecedente, si lo hay. *(Conocimiento general.)*
**¿Hay salida?** Lo que ha funcionado en otras partes, dicho simple.
**Pero ojo.** El contrapeso: por qué no es mágico.
**Cruce con Mattriz.** … (solo si aplica)

Escribir como si se le explicara a un niño (AJUSTES.md, 2026-09-30):
frases cortas, una idea por frase, cifras a escala humana ("de cada 100
pesos, cobra 76"), cada término técnico explicado ahí mismo. Menos datos,
mejor elegidos. Modelo: `ediciones/2026-09-30-radar.md`.

## Dos lecturas          ← solo si el tema divide opiniones

**<La primera postura, en pocas palabras>.** Su mejor argumento, en dos o
tres frases, como lo diría alguien que la defiende de buena fe.

**<La postura contraria>.** Igual: su mejor argumento, no su caricatura.

## Quién decide y cuándo

**Quién decide.** La institución o persona que tiene la decisión (Congreso,
concejo, ministerio, entidad, juez), en una o dos frases.

**Cuándo.** La fecha o el plazo, si existe; si no hay fecha, decirlo.

**Cómo participar.** Por dónde puede entrar un ciudadano: audiencia,
consulta, derecho de petición, votación, transmisión pública. Si no hay un
canal real, decirlo con franqueza, sin inventar.

## La paradoja del día

Dos a cuatro líneas sobre lo más absurdo de la edición, contado con
ironía seca y con los hechos tal cual (ver AJUSTES.md, «Tono con humor»).
Si hoy no hay una paradoja clara, se omite la sección.

## Qué hacer con esto      ← obligatorio desde el 2026-10-08; el sitio lo muestra arriba, después de «En pocas palabras»

**Para ir pensando.** Qué decisión de la casa, el bolsillo, el negocio o
el voto conviene ir pensando por este tema, con plazo si lo hay.

**Cómo prepararse.** Lo concreto que se puede hacer ya. Si no hay nada
urgente, decirlo y señalar qué hay que vigilar.

**Ojo con el cuento.** Un patrón para no dejarse meter el cuento: cómo
reconocer una promesa vacía o un anuncio que no es una medida. Dos a
cuatro líneas, con el ejemplo de esta edición. Se recopila sola en la
página Memoria.

**Qué podríamos exigir.** Opcional: lo que ya funcionó en Colombia o en
otro país, dicho como exigencia razonable.

## Para conversar

**La pregunta.** Una sola pregunta abierta, sin respuesta obvia, para
discutir en la sobremesa.

## Para leer más       ← uno a tres libros; ver «Para leer más» abajo

## Descartes          ← no se muestra en el sitio; sirve para no repetir temas

## Glosario

## Nota metodológica
```

- **Largo (para no desgastar):** la edición completa, sin contar Descartes,
  Glosario ni Nota metodológica, no pasa de unas 1.200 palabras (unos 5
  minutos de lectura). El build avisa si se pasa: en ese caso recortar,
  no justificar. Un solo tema bien entendido, que el lector alcance a
  llegar a la paradoja y a Para conversar.
- Sin resúmenes rápidos al comienzo ("En tres minutos" ya no existe): el
  sitio apuesta por la profundidad. El índice de la edición lo genera la
  plantilla a partir de los títulos de los nudos.
- **Dos lecturas** (pedido de Mateo, 2026-09-29, idea de *Imaginar la
  democracia*): cuando el tema divide opiniones (una política, una ley, un
  límite, un programa), después del nudo van las dos posturas principales,
  cada una en su mejor versión y con el mismo espacio (unas 40 a 60
  palabras cada una). Los rótulos son las posturas mismas, no partidos ni
  personas. No se dice cuál gana: lo decide el lector. Si el tema no
  divide (un dato técnico, un desastre), se omite. El humor no va aquí.
- **Seguimiento de decisiones**: cada edición lleva en el frontmatter el
  campo `decisiones` con las decisiones pendientes que cuenta la sección
  «Quién decide y cuándo» (`nudo`, `quien`, `que`, `plazo` si hay fecha,
  `estado: pendiente`, `nota` opcional; `prometido_desde` con la fecha
  del primer anuncio si la promesa es vieja, e `incumplidos` con el
  número de plazos que ya pasaron sin cumplirse). La plantilla las muestra en la
  edición y en la página Decisiones. Si no hay una decisión concreta en
  curso, se omite el campo.
- **Quién decide y cuándo** es obligatorio en cada edición (pedido de
  Mateo, 2026-09-29, inspirado en *Imaginar la democracia*): tres líneas
  cortas, unas 60 a 90 palabras, después del nudo y antes de la paradoja.
  Solo con datos verificables; lo que sea conocimiento general se marca.
- **Para conversar** cierra la parte de lectura: una pregunta que invite a
  pensar (no a indignarse) y, cuando exista, una acción ciudadana concreta.
- Un solo nudo por edición (pedido de Mateo, 2026-09-28): sin segundo nudo, sin
  Asombro, sin seguimientos de otros temas. Cada subtítulo es una negrita al inicio del
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
  novedad: una entrada en `actualizaciones` de la
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

### Para leer más (rige desde el 3 de octubre de 2026)

Toda edición (también «De lo que nadie habla», Imaginemos y La semana si
viene al caso) cierra con uno a tres libros que ayuden a entender el tema.
Reglas, en este orden:

1. **Primero el libro, después la tienda.** Se elige el libro que mejor
   ayude a entender el tema, esté o no en Santo & Seña. Nunca se elige un
   libro porque está en el inventario.
2. **Datos verificados.** Autor, año y editorial confirmados en una fuente
   (ficha de la editorial, catálogo de biblioteca, resultados de búsqueda).
   Una o dos frases de por qué ayuda, sin citar páginas ni frases textuales
   que no se hayan leído.
3. **Revisar el catálogo.** Buscar cada libro en
   `https://casasantoysena.com/tienda?q=<título o autor>` y abrir su ficha
   (`https://casasantoysena.com/tienda/<slug>`): si está y dice «Añadir al
   carrito», enlazar con el texto «Disponible en Santo & Seña». Si no está,
   se recomienda igual, sin enlace de compra. Si hay una versión gratuita y
   legal (licencia libre, dominio público), decirlo.
4. **Sin línea de aviso en la edición** (pedido de Mateo, 2 de octubre):
   la relación con Santo & Seña se explica una sola vez, en «¿Qué es
   esto?».
5. En la nota metodológica, una línea: cuántos libros están en Santo & Seña
   y cómo se verificaron los datos.
6. No cuenta para el techo de palabras si se mantiene corta (unas 150).

### Grabado de época (rige desde el 3 de octubre de 2026)

Cada edición lleva, bajo el título, un grabado antiguo que evoque el tema:
ilustraciones de periódicos y libros del siglo XIX y comienzos del XX (el
referente visual es el de los periódicos de Red Dead Redemption).

1. **Buscar en Wikimedia Commons** (API:
   `https://commons.wikimedia.org/w/api.php?action=query&list=search&srnamespace=6&srsearch=<términos>&format=json`),
   en inglés y en español: el hecho o el lugar más «engraving», «wood
   engraving», «grabado», «Harper's Weekly», «Le Tour du monde»,
   «L'Illustration». Preferir escenas de Colombia, los Andes o América
   Latina; si no hay, una escena universal del mismo asunto.
2. **Solo grabados, litografías o dibujos de época**, no fotos, y solo
   dominio público o CC BY / CC BY-SA. Nada de imágenes de juegos, de
   bancos de imágenes ni de prensa actual.
3. **Debe evocar, no engañar.** La imagen es de otra época y el pie lo
   dice: lugar, hecho y año. Nunca se presenta como foto del hecho de hoy.
   Nada morboso: en temas de violencia, víctimas o niños, se elige algo
   simbólico (un lugar, un objeto) o la edición sale sin grabado.
4. **Preparar la imagen** con
   `.venv/bin/python scripts/grabado.py "File:<nombre en Commons>" <slug-de-la-edición>`.
   Deja `imagenes/<slug>.webp` en tinta y papel del sitio e imprime el
   bloque `grabado:` para el frontmatter. Completar `pie` y `alt` en
   español (el `alt` describe lo que se ve) y traducir el crédito
   («Grabado de <autor>, <año> · Dominio público, vía Wikimedia Commons»).
5. Commons limita las descargas seguidas (error 429): el script espera y
   reintenta; no insistir más de tres veces.
6. Si no aparece un grabado que encaje bien, la edición sale sin grabado.
   Mejor ninguno que uno forzado. Una línea en la nota metodológica dice
   de dónde salió (o por qué no hay).

## 5. Publicar

1. `./build.sh` debe terminar sin error y crear
   `site/ediciones/<fecha>-radar.html`. Si el build se detiene, leer el
   mensaje (archivo, campo y motivo), corregir el frontmatter y repetir;
   no publicar nunca con el build fallando. Revisar que el HTML tenga los
   carriles, los nudos y las fuentes numeradas.
2. Commit solo de `ediciones/`, `imagenes/`, `site/` y, si cambiaron,
   `candidatas.md` y `AJUSTES.md`, con el mensaje `Edición N · <fecha>`
   (o `Ediciones N y M · <fecha>` si el día tiene más de un tema).
3. `git push origin main`. Si falla por red, reintentar hasta cuatro veces
   con espera creciente (2, 4, 8 y 16 segundos).
4. Cloudflare publica solo al recibir el push.

## 6. Viernes: La semana

Los viernes, después de publicar la edición del día, escribir una segunda
edición `ediciones/<fecha>-semana.md` (número siguiente) que redondee la
semana, de lunes a viernes. Modelo: `ediciones/2026-10-02-semana.md`.

- No es una edición nueva de noticias: no se investiga ni se agregan
  datos. Todo sale de las ediciones de la semana y sus fuentes.
- Estructura práctica, sin tesis ni moraleja: **En pocas palabras** (una
  o dos frases), **Lo que pasó esta semana** (una viñeta por edición, con
  enlace), **Para tener presente** (tres a cinco cosas concretas para
  recordar) y **Lo que viene** (decisiones pendientes con fecha y quién
  decide). Luego «## Para conversar» con una pregunta sencilla y una nota
  metodológica corta.
- Lenguaje sencillo (AJUSTES.md, 2026-09-30), unas 400 a 600 palabras.
- `seguimiento` lleva los `temas` de las ediciones de la semana; sin
  `decisiones` (ya están en sus ediciones).
- Se publica en el mismo commit o en uno aparte: `Edición N · <fecha> · La semana`.

## 7. De lo que nadie habla

Sección para los temas que no se tocan en la mesa porque incomodan,
pueden ofender o son muy emocionales (violencia sexual, salud mental,
suicidio, racismo, abuso en la familia y parecidos). Se publica cuando
los editores la piden o cuando la rutina encuentra un tema así que
cumple las cuatro condiciones de nudo. Archivo:
`ediciones/<fecha>-nadie-habla.md`; título que empiece por «De lo que
nadie habla: ». Modelo: `ediciones/2026-10-02-nadie-habla.md`.

- El objetivo es aprender a hablar del tema de una forma que construya:
  el patrón y el porqué, no el escándalo ni el caso a caso.
- Nunca identificar víctimas ni dar detalles morbosos; no culpar a la
  víctima ni generalizar sobre grupos enteros.
- Siempre cierra con **Qué puede hacer usted** (acciones concretas por
  rol) y un recuadro **Si usted o alguien cercano lo necesita** con
  líneas de ayuda verificadas.
- La pregunta de «Para conversar» abre una conversación en familia, sin
  sermón ni culpa.
- Mismo lenguaje sencillo y mismo rigor de fuentes que las demás.

No modificar la plantilla, el build, `prompt.md` ni este archivo durante
la rutina.
