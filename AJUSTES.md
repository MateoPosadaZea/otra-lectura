# Ajustes de estilo y tono

Reglas que se van sumando a partir de los ajustes enviados desde el
formulario del sitio. La revisión horaria las agrega aquí cuando un ajuste
es general (no solo una corrección puntual), y la rutina diaria las aplica
al escribir cada edición. Si una regla choca con `prompt.md`, prevalece la
de este archivo.

Formato: una regla por viñeta, con la fecha y el ajuste que la originó.

## Reglas vigentes

- 2026-09-24 · Pedido de Mateo ("no queremos causar desgaste a nuestros
  lectores"): ediciones cortas (ver las reglas del 2026-09-28 y del 2026-10-05, que las
  reemplaza en largo y número de temas); cerrar con "Para
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
  - Dosis (ajustada el mismo día, pedido de Mateo): el humor acompaña toda
    la lectura, no solo el final. Repartido a lo largo de cada nudo (dos a
    cuatro toques: en el título si se presta, en «Qué pasó», en «Por qué se
    repite», en «Quién lo está resolviendo»…), también en Asombro y en la
    pregunta de «Para conversar». Frases cortas, que se lean de paso, sin
    frenar la explicación. Temas de violencia, muertes o tragedias van sin
    humor.
  - Cierre fijo antes de «Para conversar»: **La paradoja del día**, dos a
    cuatro líneas sobre lo más absurdo de la edición.
  - Lenguaje llano: nada de jerga académica («diferencias en diferencias»,
    «subcompensación», «margen operativo»); decir qué encontró el estudio
    en palabras de todos los días.
- 2026-09-26 · Pedido de Mateo: vuelve la corrección sobre el texto, y
  solo eso. Botón «Corregir» arriba; pide usuario y contraseña (la clave
  familiar) una vez; todo el texto de la página es editable; «Guardar»
  envía los cambios como «[Edición]» y la revisión horaria los aplica.
- 2026-09-28 · Pedido de Mateo ("la paradoja del día y Para conversar se
  pierden, no se llega hasta abajo"): **un solo tema por edición**, el de
  mayor impacto. Sin segundo nudo, sin Asombro y sin seguimientos de otros
  temas (las novedades de temas viejos van como `actualizaciones` en su
  edición original). Orden: el tema → La paradoja del día → Para
  conversar. Después, un recuadro plegado «¿Le interesa ver las fuentes?»
  y, solo si existe una edición relacionada con el tema, «¿Le gustaría
  seguir leyendo?» con esa lectura; si no la hay, «Eso es todo por hoy» y
  ninguna otra noticia. Techo: unas 1.000 palabras de lectura.
- 2026-09-29 · Pedido de Mateo: se quita la opción Escuchar (las voces del
  dispositivo sonaban robóticas). Si vuelve, que sea una sola voz pausada,
  colombiana y natural, grabada o generada por edición; no las voces del
  navegador. También: letra de 18 px en móvil para leer más fácil.
- 2026-09-29 · Pedido de Mateo (idea del libro *Imaginar la democracia*):
  cada edición lleva la sección «## Quién decide y cuándo», entre el nudo y
  la paradoja, con tres etiquetas: **Quién decide.** **Cuándo.** **Cómo
  participar.** El objetivo es que el lector sepa dónde se toma la decisión
  y por dónde puede entrar. Si no hay fecha o canal de participación, se
  dice con franqueza. Techo de la edición: unas 1.100 palabras.
- 2026-09-29 · Pedido de Mateo: el primer sábado de cada mes la edición es
  «Imaginemos»: se toma un nudo ya tratado y se propone un diseño concreto
  de cómo podría funcionar mejor (qué se probó, la propuesta, cuánto
  costaría, qué podría salir mal, quién tendría que aprobarla). Ver
  RUTINA.md, «Días livianos y domingo». La primera sale el sábado 3 de
  octubre de 2026.
- 2026-09-29 · Los editores aprobaron el borrador «Imaginemos: una regla del
  gas que dure más que un gobierno» (borradores/2026-10-03-imaginemos-gas.md)
  como la edición del sábado 3 de octubre de 2026. Ese día la rutina lo
  publica en vez de escribir otra (ver RUTINA.md, paso 1.7).
- 2026-09-29 · Pedido de Mateo (idea 4 de *Imaginar la democracia*):
  seguimiento de decisiones. Cada edición registra en `decisiones` quién
  tiene que decidir qué y para cuándo; la rutina diaria revisa las que
  vencen y anota si se tomaron, se aplazaron o nadie las tomó. El sitio
  tiene una página «Decisiones» (enlace al pie) con todas, agrupadas por
  estado, y cada edición muestra el estado de la suya.
- 2026-09-29 · Pedido de Mateo (idea 2 de *Imaginar la democracia*): en
  temas que dividen opiniones, la sección «## Dos lecturas» después del
  nudo, con las dos posturas principales en su mejor versión, mismo
  espacio y sin decir cuál gana. Techo de la edición: unas 1.200 palabras.
- 2026-09-29 · Pedido de Mateo: la imagen para compartir (Open Graph) cambia
  según la página. Cada edición muestra su título, número, fecha y
  categorías; cada día, el título de su edición; las demás páginas, su
  título y descripción. La portada conserva la imagen general. Se generan
  solas en el build (scripts/og.py, con Pillow); no hay que hacer nada.
- 2026-09-30 · Pedido de Mateo: explicar como si el lector fuera un niño
  (rige desde el 1 de octubre; modelo: la edición 11, sobre Air-e). Cada
  nudo empieza con **En pocas palabras** (dos o tres frases que dicen de
  qué se trata). Luego un ejemplo cotidiano que haga de puente (la tienda
  de barrio, la recarga del celular), frases cortas, una idea por frase,
  cifras traducidas a escala humana ("de cada 100 pesos, cobra 76"; "más
  de cinco veces") y cada término técnico explicado ahí mismo, no solo en
  el glosario. Etiquetas sencillas: En pocas palabras, Qué pasó, Cómo
  llegamos aquí, Ya pasó antes, ¿Hay salida?, Pero ojo. Menos datos, mejor
  elegidos: si una cifra o un estudio no ayuda a entender, va a la nota
  metodológica o se queda por fuera. El rigor no baja: mismas fuentes,
  mismas marcas de no verificado.
- 2026-10-01 · Pedido de Mateo: el sitio se abre a los buscadores
  (`INDEXAR = True`): robots.txt permite rastrear, el sitemap se anuncia y
  se quita el noindex. Search Console verificado por Mateo con el dominio.
  Los comentarios siguen cerrados al público (ver APERTURA.md).
- 2026-10-02 · Pedido de Mateo: cada viernes, además de la edición del
  día, sale «La semana»: una síntesis que redondea las ediciones de lunes
  a viernes, el hilo que las une, lo que hay que tener presente y las
  decisiones que vienen. Sin datos nuevos. Ver RUTINA.md, sección 6.
- 2026-10-02 · Pedido de Mateo: se quitan del pie de página los enlaces
  «Cómo se usa» y «Candidatas» (las páginas siguen existiendo).
- 2026-10-02 · Mateo: «La semana» debe ser práctica, no pretenciosa. Nada
  de «el hilo que las une» ni moralejas: repaso de lo que pasó, qué
  recordar y qué viene, con una pregunta sencilla. Unas 400 a 600 palabras.
- 2026-10-02 · Pedido de Mateo: nueva sección «De lo que nadie habla»,
  para temas que incomodan o duelen y que no se tocan en la mesa. Se
  tratan buscando entender el patrón y qué se puede hacer, sin escándalo,
  sin identificar víctimas y siempre con líneas de ayuda. Ver RUTINA.md,
  sección 7. Primera edición: violencia sexual y el silencio de quienes
  saben (2 de octubre).
- 2026-10-02 · Pedido de Mateo: cada edición cierra con «Para leer más»
  (uno a tres libros sobre el tema). Primero se elige el libro por el
  tema; si está en Santo & Seña (librería de la familia del editor), se
  enlaza allí, y siempre se dice esa relación en una línea. Ver RUTINA.md,
  «Para leer más». Rige desde el 3 de octubre; prueba en la edición 15.
- 2026-10-02 · Mateo: en «Para leer más» no va la línea de aviso sobre
  Santo & Seña en cada edición; basta con la explicación en «¿Qué es esto?».
- 2026-10-02 · Pedido de Mateo: cada edición lleva un grabado de época bajo
  el título, en tinta y papel del sitio, con pie (lugar, hecho, año) y
  crédito con enlace a la fuente. Referente: los periódicos de Red Dead
  Redemption. Solo dominio público o licencia libre (Wikimedia Commons);
  nunca se presenta como imagen del hecho actual. Ver RUTINA.md, «Grabado
  de época». Primera: edición 13 (Ibarra, 1868, de Édouard Riou).
- 2026-10-05 · Pedido de Mateo ("si es un tema, un tema; si realmente con
  este criterio son dos, dos; si son tres, tres"): el día puede tener de
  uno a tres temas, cada uno en su edición, solo si cada uno mueve la
  aguja (17 puntos o más); nunca se rellena. Puede entrar un tema de
  contexto que no es nudo pero toca a Colombia por canales concretos
  (ejemplo: las elecciones de Brasil). La portada los muestra en retícula
  de periódico: el principal arriba, los demás en columnas. Ver RUTINA.md,
  sección 2b, y prompt.md, «Temas de contexto». Primera: 5 de octubre
  (agua y El Niño; Brasil).
- 2026-10-07 · Pedido de Mateo (sobre la edición de desaparecidos: "es de
  esas noticias que son más desesperanzadoras"): en los temas duros, el
  título no se queda solo en la brecha o el daño, y «En pocas palabras»
  dice también lo que sí funciona o la salida posible, con su fuente.
  Sin maquillar el problema ni prometer lo que no está probado. Cuando
  hay una decisión pendiente, se le hace seguimiento y se cuenta el
  resultado, también si es bueno. Rige desde la edición 24.
- 2026-10-07 · Pedido de Mateo ("no veo mucho noticias del mundo… con los
  mismos filtros y explicaciones… que muevan la aguja… si hay algo
  importante, si no no"): el barrido incluye siempre el mundo. Un tema de
  otro país entra con los mismos filtros y el umbral de 17 puntos; su
  cercanía se puntúa por el canal real por el que llega a Colombia
  (precios, clima, salud, migración, seguridad, tecnología), no por la
  distancia, y ese canal se explica en «En pocas palabras». Máximo uno al
  día; si ninguno llega, no entra. Ver RUTINA.md, sección 2b, y prompt.md,
  «Temas del mundo».
- 2026-10-08 · Pedido de Mateo ("lo más importante es cómo se ha resuelto
  esto en otras partes del mundo"; "¿por qué se conecta esto con esto?";
  "en algunos temas, un poco más de humor"). Tres reglas, desde la
  edición siguiente:
  1. Soluciones primero: el problema va corto y la salida lleva más
     espacio, con lo que ya funcionó en la historia de Colombia y en
     otros países. «En pocas palabras» cierra con la salida y «Para
     conversar» agrega «Qué podríamos hacer».
  2. «Cómo se conecta»: toda edición con seguimiento, o con un tema
     vecino el mismo día, explica en una o dos frases por qué se conecta,
     con enlace. El build avisa si falta.
  3. Humor donde cabe: ironía sobre instituciones y sobre nosotros
     mismos, y analogías cotidianas, en temas que no duelen. Nunca contra
     víctimas, nunca en violencia, muertes, desaparecidos, salud mental
     ni «De lo que nadie habla». El humor no reemplaza datos. Mateo
     (2026-10-08): «que se siga viendo elegante, con los términos»:
     vocabulario preciso, sin muletillas ni frases dirigidas al lector;
     una ironía bien puesta, no un chiste por párrafo.
  Prueba: la edición 25 (diésel) se reescribió con las tres reglas.
  Ver prompt.md, «Soluciones primero», «Cómo se conecta» y «Registro y
  estilo».
- 2026-10-08 · Pedido de Mateo ("¿para qué me sirve a mí esto?"; "qué
  hacer, qué decisiones hay que ir pensando, cómo prepararse, no dejarse
  meter el cuento, patrones, memoria, que no se nos olvide"). Desde la
  edición siguiente:
  1. Sección obligatoria «Qué hacer con esto»: Para ir pensando, Cómo
     prepararse, Ojo con el cuento y, si cabe, Qué podríamos exigir.
     Reemplaza el «Qué puede hacer usted» de Para conversar.
  2. Escepticismo con los anuncios: un anuncio no es un hecho; si la
     promesa es vieja, se dice desde cuándo y cuántos plazos incumplió
     (`prometido_desde` e `incumplidos` en `decisiones`).
  3. Página Memoria (memoria.html): reúne sola las promesas que siguen
     esperando y todos los «Ojo con el cuento» de las ediciones, para que
     no se olviden con los días. Enlazada en el pie y en Decisiones.
  Prueba: ediciones 24 y 25.
