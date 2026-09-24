# Candidatas

Ideas de cruce con Mattriz que aparecen en el campo `cruce_mattriz` de las
ediciones. `./build.sh` genera `site/candidatas.html` a partir de este
archivo. Candidatas, no tareas.

Cómo se edita:

- Una sección `## Idea` por candidata, con el mismo texto que en el
  frontmatter (no importan mayúsculas ni espacios extra).
- Primera línea: `Estado: pendiente`, `evaluada`, `descartada` o `activa`.
- Después, en markdown: **Qué resolvería.**, **Cómo.**, **Por dónde
  empezar.** y **Entregable posible.**
- Una candidata que aparezca en una edición y no esté aquí se muestra como
  `pendiente`, sin desarrollo.

## Alerta de calor legible cruzada con datos de salud

Estado: pendiente

**Qué resolvería.** En Colombia la alerta por calor es meteorológica: dice
cuánto calor hace, no a quién hay que buscar ni qué hacer. Los picos de
consultas en Barranquilla y Cartagena durante El Niño muestran que el
riesgo se concentra en adultos mayores, niños y personas con enfermedades
crónicas, y la humedad del Caribe lo agrava.

**Cómo.** Un semáforo diario por municipio que combine el pronóstico de
temperatura y humedad (índice de calor) con umbrales definidos a partir de
la literatura, como el plan de Ahmedabad, y, donde existan, datos
agregados de consultas por calor. Cada nivel dice qué hacer y a quién
priorizar, en lenguaje directo.

**Por dónde empezar.**

1. Revisar qué pronósticos por municipio publica el IDEAM en formato
   abierto y con qué frecuencia (a verificar).
2. Revisar qué datos agregados de salud existen y con qué rezago
   (SIVIGILA, secretarías de salud; a verificar).
3. Hablar con una secretaría de salud del Caribe para validar umbrales,
   mensajes y a quién llegarían.

**Entregable posible.** Piloto de un mes en una ciudad: página de una
sola vista con el nivel del día, qué hacer y a quién llamar, más un
boletín para redes o WhatsApp. Al cierre, una nota con qué se aprendió y
si vale la pena escalarlo.

## Visualización pública que cambia comportamiento

Estado: pendiente

**Qué resolvería.** Los datos de consumo de agua o energía existen, pero
no llegan a la gente como una señal clara y colectiva. En Ciudad del Cabo,
un tablero semanal con una meta simple (87 litros por persona al día) y la
fecha estimada del Día Cero ayudó a bajar el consumo a menos de la mitad.

**Cómo.** Una sola métrica, una meta colectiva y una actualización
periódica, sin exponer datos de hogares. Hay que diseñar para dos públicos
distintos: según la evidencia de Ciudad del Cabo, los hogares de ingresos
altos respondieron a la presión social y los de ingresos bajos al precio.

**Por dónde empezar.**

1. Elegir un recurso y una ciudad con datos públicos periódicos, por
   ejemplo agua en Bogotá o energía en el Caribe (a verificar).
2. Definir la métrica y la meta con la entidad que publica el dato.
3. Revisar privacidad desde el inicio: el mapa de Ciudad del Cabo recibió
   críticas por exponer consumos de hogares.

**Entregable posible.** Prototipo de tablero ciudadano de una métrica, con
actualización semanal y una pieza para compartir, más una propuesta corta
para presentarla a la empresa de servicios o a la alcaldía.

## Tablero de contratos de reconstrucción

Estado: pendiente

**Qué resolvería.** Los regímenes especiales de contratación para
emergencias reducen requisitos justo cuando hay más recursos y más
presión. Los datos de contratación son públicos, pero casi nadie los
traduce a algo legible, y la vigilancia llega tarde.

**Cómo.** Tomar los contratos del régimen especial de la reconstrucción
desde los datos abiertos de compras públicas (SECOP II), compararlos
contra precios de referencia de ítems similares y señalar alertas simples:
contratación directa, adiciones, plazos atípicos, concentración en pocos
contratistas.

**Por dónde empezar.**

1. Identificar en datos.gov.co el conjunto de SECOP II y cómo distinguir
   los contratos del régimen especial (a verificar).
2. Hacer un prototipo con un solo departamento afectado.
3. Definir cinco a diez alertas, apoyándose en metodologías existentes de
   indicadores de riesgo en contratación.

**Entregable posible.** Tablero público de una página, actualizado cada
semana, con la lista de contratos, las alertas y la comparación de
precios, más una nota metodológica que explique qué significa cada
alerta y qué no significa.
