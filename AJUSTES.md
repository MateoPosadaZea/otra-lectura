# Ajustes de estilo y tono

Reglas que se van sumando a partir de los ajustes enviados desde el
formulario del sitio. La revisión horaria las agrega aquí cuando un ajuste
es general (no solo una corrección puntual), y la rutina diaria las aplica
al escribir cada edición. Si una regla choca con `prompt.md`, prevalece la
de este archivo.

Formato: una regla por viñeta, con la fecha y el ajuste que la originó.

## Reglas vigentes

- 2026-09-24 · Pedido de Mateo ("no queremos causar desgaste a nuestros
  lectores"): ediciones de máximo unas 1.500 palabras de lectura y hasta
  tres nudos; cerrar con "Para
  conversar" (una pregunta y, si aplica, qué puede hacer un ciudadano).
  El objetivo es entender y conversar, no acumular información.
- 2026-09-25 · Pedido de Mateo ("quitar términos como descabezados, mucho
  cuidado con eso, ese tipo de términos no usarlos"): lenguaje sobrio y
  preciso, nunca bélico, crudo, despectivo ni de jerga policial o militar.
  No usar "descabezar/descabezamiento", "kingpin", "capo", "abatir", "dar de
  baja", "neutralizar", "golpe" (en sentido militar), "guerra contra…",
  "sicario" si hay alternativa descriptiva, ni coloquialismos como "plata".
  Decir, por ejemplo, "estrategia centrada en los jefes de los grupos
  criminales"; las muertes se nombran como hechos, sin dramatizar.
- 2026-09-25 · Mayúsculas según la RAE: títulos y subtítulos con mayúscula
  solo inicial (y nombres propios); meses, días y cargos en minúscula
  ("el presidente"); instituciones con mayúscula (Gobierno, Congreso, JEP).
- 2026-09-25 · Gráficos: cada nudo lleva un gráfico cuando el texto
  tiene cifras comparables (misma magnitud y misma base) o una evolución en
  el tiempo; nunca con cifras de bases distintas ni inventadas. Si no hay
  cifras que lo justifiquen, no se pone. Nombres de barras cortos.
- 2026-09-25 · Sin emojis ni iconos de ese tipo (💬, 🎤, ⏱, ▶, ✓…) ni en las
  ediciones ni en el sitio: solo texto.
- 2026-09-25 · Pedido de Mateo: la etiqueta del mecanismo se llama
  **El cómo, en síntesis.** (no "El cómo, en corto").
- 2026-09-25 · Pedido de Mateo ("queremos fomentar la profundidad, no la
  lectura rápida y efímera"): no hay sección "En tres minutos" ni
  resúmenes para leer de afán. La apuesta es la curaduría, el análisis, las
  fuentes y las ayudas (glosario, gráficos, historia); el techo de largo es
  para no desgastar, no para simplificar.
- 2026-09-25 · Pedido de Mateo: el "Cruce con Mattriz" no se muestra en las
  ediciones. Se sigue escribiendo en el markdown (y las ideas nuevas en
  `cruce_mattriz` y `candidatas.md`), pero la plantilla lo quita del
  artículo y lo archiva en la página de Candidatas. Si no hay cruce, basta
  omitirlo.
- 2026-09-25 · Pedido de Mateo ("fuentes de académicos, de papers
  científicos… que la mayoría no sean de la prensa de acá; muchas tienen
  sus posturas e ideologías; ir más allá"): el barrido puede tomar más
  tiempo. Prensa solo para el hecho; análisis, cifras de fondo, soluciones
  y contrapeso desde estudios revisados por pares, evaluaciones de impacto,
  documentos oficiales y bases de datos. Meta: cada nudo con al menos
  una fuente académica y una oficial o de datos, y al menos la mitad de las
  fuentes no de prensa. Cada fuente lleva `tipo`. Ver RUTINA.md, sección 3.
- 2026-09-25 · Pedido de Mateo ("temas de mayor impacto en la sociedad";
  en calibración): la selección se ordena por un puntaje de impacto
  (alcance, gravedad, duración, cercanía, decisión en curso; 1 a 3 cada
  uno; gravedad y cercanía valen doble, máximo 21). Al menos un tema
  colombiano de alto impacto. El tema puede ser estructural con un hecho
  reciente que lo reactive. La nota metodológica
  muestra el puntaje de elegidos y descartados. Ver RUTINA.md, sección 2b.
- 2026-09-25 · Pedido de Mateo: "fricción" pasa a llamarse **nudo**, con
  una definición precisa de cuatro condiciones (se repite o persiste,
  tiene un mecanismo, alguien lo puede cambiar, causa daño comprobable).
  Si falla una, no entra. El filtro va antes del puntaje de impacto. Ver
  prompt.md, "Definición de nudo". En el frontmatter, `actualizaciones`
  usa `nudo` (se acepta `friccion` en ediciones viejas).
- 2026-09-26 · Pedido de Mateo: se quitan del sitio las herramientas de
  comentar, hablar, corregir el texto y valorar la edición; los ajustes se
  hacen directamente con Claude. El sitio arranca en modo día (claro); el
  modo noche solo con el botón. La portada abre con la frase, una
  explicación corta y "Leer la edición de hoy".
- 2026-09-26 · Pedido de Mateo: sin título «Radar» en pantalla (los nudos
  abren la edición) y sin el paréntesis de lugares en los títulos
  («(Colombia → Países Bajos)»); los lugares se explican en el texto.
  Nada de citas de medios entre paréntesis dentro del texto («(Infobae)»,
  «(El Tiempo, Infobae…)»): la fuente se nombra con naturalidad cuando
  importa («según la Contraloría») y todas quedan en Fuentes. Cada sigla o
  entidad se explica la primera vez que aparece, dentro de la frase
  («la Adres, la entidad que administra el dinero de la salud pública»).
- 2026-09-26 · Pedido de Mateo: la nota metodológica (y "Lo que
  descartamos") se escribe en primera persona del plural: «hicimos»,
  «trabajamos», «no pudimos abrir». Sin jerga técnica (nada de
  «WebFetch», «la red bloqueó»): «no pudimos abrir el documento completo».
- 2026-09-26 · Pedido de Mateo: el botón de noche/día lleva ícono (luna y
  sol, dibujados en SVG, no emojis). Es la excepción a «sin íconos».
- 2026-09-26 · Pedido de Mateo: **tono con humor**. Crítico pero divertido,
  para recordar, comentar y opinar; fácil de entender, sin complicarlo.
  - La gracia sale de lo absurdo que ya traen los hechos, con ironía seca
    («el negocio ideal sería un seguro de salud sin enfermos»). Nada de
    chistes inventados.
  - Se ríe de los sistemas y las paradojas, nunca de las víctimas ni de
    personas por su aspecto, origen o condición. Parejo con todos los
    lados políticos.
  - Nunca a costa del dato: la frase irónica va junto a la cifra
    verificada, no en su lugar.
  - Dosis: una o dos frases por nudo, donde la paradoja lo permita. Temas
    de violencia, muertes o tragedias van sin humor.
  - Cierre fijo antes de «Para conversar»: **La paradoja del día**, dos a
    cuatro líneas sobre lo más absurdo de la edición.
  - Lenguaje llano: nada de jerga académica («diferencias en diferencias»,
    «subcompensación», «margen operativo»); decir qué encontró el estudio
    en palabras de todos los días.
