# Otra lectura

Archivo estático de las ediciones del radar de noticias. El contenido vive en
`ediciones/*.md`; `site/` es HTML generado a partir de ahí y no se edita a mano.

Requisitos: `bash`, `git` y `python3` (3.9 o más). El único conversor de
markdown es Python-Markdown, con la versión fijada en `requirements.txt`.
`build.sh` lo instala en `.venv/` la primera vez.

## Navegación

- **Portada** (`index.html`): el epígrafe y solo las ediciones del día más
  reciente, cada una con sus fricciones principales (enlazan a su ancla).
- **Días anteriores** (`archivo.html`): todas las fechas agrupadas por mes,
  con sus temas; con JavaScript, además, un selector "Ir a una fecha".
- **Un día** (`dias/AAAA-MM-DD.html`): las ediciones de esa fecha, con
  paso al día anterior y al siguiente.
- **Categorías** (`categorias/*.html`) y **¿Qué es esto?** (`sobre.html`,
  desde `sobre.md`) en la barra de secciones.

Accesibilidad y lectura (todo gratis y sin dependencias; lo que usa
JavaScript simplemente no aparece sin él):

- Al bajar, una barra fija con el logotipo pequeño y un botón **Arriba**
  (en el pie hay además un enlace "Volver arriba" que funciona sin JS).
- **Escuchar**: cada edición se puede oír en voz alta con la voz del
  propio dispositivo (Web Speech API, sin archivos de audio ni servicios
  pagos). Lee párrafo por párrafo, resalta el que suena, permite pausar,
  detener y cambiar la velocidad, y omite fuentes, gráficos y tablas. La
  calidad de la voz depende del teléfono o computador.
- Respeta `prefers-reduced-motion` y el modo claro/oscuro.

## Agregar una edición

El formato editorial está en `prompt.md` y el técnico en `ESPECIFICACION.md`.

1. Crea `ediciones/AAAA-MM-DD-radar.md`. Si hay dos el mismo día, usa los
   sufijos `-01` y `-02`. El frontmatter:

   ```yaml
   ---
   fecha: 2026-09-24                 # obligatorio, AAAA-MM-DD
   edicion: 4                        # obligatorio, entero
   titulo: "..."                     # obligatorio
   temas: [calor-salud, presupuesto-2027]
   categorias: [salud, economia]     # claves de CATEGORIAS (scripts/build.py)
   lugares: [Colombia, India]
   cruce_mattriz: [alerta de calor legible]
   seguimiento: [presupuesto-2027]   # temas de ediciones anteriores
   nota: "opcional, se muestra bajo el título"
   fuentes:
     - medio: "CEPAL"
       titulo: "Panorama Fiscal 2026"
       url: "https://..."            # obligatoria
   actualizaciones:                  # se agregan después de publicar
     - fecha: 2026-10-02
       friccion: "presupuesto-2027"  # opcional: slug de la fricción
       texto: "El Congreso aprobó el presupuesto el 1 de octubre..."
   correcciones:                     # se agregan después de publicar
     - fecha: 2026-09-30
       texto: "Se corrigió la cifra de ... : la fuente reporta ..."
   ---
   ```

   - `temas` es libre y específico; `categorias` agrupa el archivo en
     páginas navegables.
   - `seguimiento` se muestra como enlaces a las ediciones anteriores que
     tienen ese slug en `temas`.
   - `fuentes` sale como lista numerada al cierre (antes del glosario).
   - `actualizaciones` con `friccion` aparece al pie de esa fricción; sin
     `friccion`, al final de la edición. `correcciones` va siempre al final.
     **El texto original nunca se edita: la corrección se agrega.** El
     índice y la cabecera marcan las ediciones revisadas con la fecha del
     cambio más reciente.
   - Textos largos entre comillas pueden seguir en la línea siguiente,
     con más sangría.

2. En el cuerpo, la plantilla reconoce estas marcas:

   | Markdown | Se muestra como |
   |---|---|
   | `# Radar · 24 de septiembre de 2026` | se omite (la cabecera sale del frontmatter) |
   | `## Carril 1: Radar`, `## Carril 2: Asombro`, `## Descartes`, `## Glosario` | divisor de carril |
   | `### 1. Nombre de la fricción {#slug}` | fricción; `{#slug}` es opcional y es lo que usa `actualizaciones.friccion` (sin él, el slug sale del título) |
   | `### Seguimiento: tema` | nota corta de seguimiento |
   | `**Qué ocurrió.** texto` | subtítulo de la fricción |
   | `**Contrapeso.**` | tarjeta con doble borde |
   | `**Antecedente histórico.** *(Conocimiento general.)* …` | sello rojo y fondo rayado (todo el párrafo) |
   | `… *(Conocimiento general:* texto *)*` a mitad de párrafo | solo ese tramo resaltado |
   | `**Sin salida conocida.**` | etiqueta en rojo |
   | `**Conflicto de interés declarado:**` | nota enmarcada |
   | `## Glosario` con `- **Término:** definición` | además, glosario flotante a la derecha (en móvil, botón "Glosario") |

   Una etiqueta es una negrita al inicio del párrafo que termina en punto o
   dos puntos. En el carril de Asombro esa negrita se muestra como título
   corrido.

3. Revisa el resultado con `./build.sh` y abre `site/index.html`.

## Gráficos

Un bloque ` ```grafico ` en el cuerpo de una edición se convierte en un
gráfico interactivo, dibujado en el build: se ve sin JavaScript, sigue el
modo claro u oscuro, muestra el valor al pasar el mouse o tocar, y trae su
tabla en "Ver datos". Tipos: `barras`, `columnas`, `lineas` (hasta 3
series) y `puntos` (admite `escala: log`). Los colores de las series
(`--s1` a `--s3` en `estilo.css`) están validados para daltonismo en ambos
modos. Formato completo en `scripts/graficos.py`:

````markdown
```grafico
tipo: barras
titulo: "Gasto por principio activo"
unidad: "miles de millones"
destacar: "Pembrolizumab"
fuente: "Ministerio de Salud, 2025"
datos:
  - etiqueta: "Pembrolizumab"
    valor: 919
  - etiqueta: "Nivolumab"
    valor: 300
```
````

## Verificación

`./build.sh` se detiene, sin publicar nada, y dice archivo, campo y motivo si:

- el frontmatter es inválido: falta `fecha`, `edicion` o `titulo`, una
  fecha no existe, hay un campo desconocido, una categoría no existe, o la
  sintaxis está mal (comillas sin cerrar, sangría inesperada);
- una fuente no tiene `url` (o no es http/https);
- un slug de `seguimiento` no aparece en `temas` de ninguna edición
  anterior;
- una actualización apunta a una fricción que no existe en esa edición;
- un bloque `grafico` está mal escrito (tipo, campos o números);
- en `candidatas.md` una candidata no empieza con `Estado:` o tiene un
  estado inválido.

## Candidatas

`site/candidatas.html` reúne las ideas del campo `cruce_mattriz` de todas
las ediciones, con la edición de origen, la fecha, el estado y su
desarrollo. Se lleva a mano en `candidatas.md`: una sección `## Idea` por
candidata, con la línea `Estado: pendiente | evaluada | descartada | activa`
y los bloques **Qué resolvería.**, **Cómo.**, **Por dónde empezar.** y
**Entregable posible.** Si una candidata no está en el archivo, se muestra
como `pendiente` y sin desarrollo. La página se enlaza desde el pie.

## Indexación

Mientras el proyecto está en calibración, el sitio pide no ser indexado:
`site/robots.txt` con `Disallow: /` y `<meta name="robots" content="noindex,
nofollow">` en todas las páginas. Ambos salen de una sola constante: para
abrirlo a buscadores, cambia `INDEXAR = False` a `True` en
`scripts/build.py` y publica.

Cada página lleva además descripción, Open Graph y tarjeta de X (vista
previa al compartir por WhatsApp, LinkedIn o X), datos estructurados
JSON-LD (`Article` en las ediciones) y la imagen `plantilla/og.png`. La
imagen, la url canónica y `sitemap.xml` necesitan la dirección pública:
pon la url del sitio en `SITIO_URL` (`scripts/build.py`).

## Desplegar

```sh
./deploy.sh "Edición del 23 de septiembre"   # el mensaje es opcional
```

El script hace build, commit (de `ediciones/`, `site/`, `candidatas.md` y
`AJUSTES.md`) y push. Si la verificación falla, no publica nada. Cloudflare
Workers detecta el push y ejecuta `npx wrangler deploy`, que publica `site/`
tal cual según `wrangler.jsonc`. No hay build en Cloudflare: el HTML ya viene
generado.

El sitio es público. Si algún día se quiere privado, se pone Cloudflare
Access delante del Worker; no hay que tocar el código.

## Ajustes

Cada página tiene el panel **Notas**: fijo a la izquierda en pantallas
anchas y como botón flotante abajo a la izquierda en el celular. Se escriben
notas mientras se lee (seleccionando un fragmento del texto, la nota lo
cita), se acumulan en ese navegador aunque se cambie de página, y se envían
todas juntas. Nombre y clave se recuerdan en el dispositivo si se deja
marcada la casilla. Sin JavaScript, el panel funciona como formulario de
una sola nota. El Worker (`src/worker.js`) valida la clave familiar y guarda
cada envío, con todas sus notas, como un issue `[Ajuste] …` en GitHub. Cada hora, de 6 a. m. a 10 p. m. (Colombia),
Claude revisa esos issues:

- corrección de contenido → se agrega en `correcciones` de la edición
  (el texto original no se edita);
- regla de estilo o tono → se agrega a `AJUSTES.md` y rige desde la
  edición siguiente;
- cambio de diseño o funciones del sitio → se implementa en la plantilla,
  el CSS o el build, se prueba y se publica, siempre que sea acotado y
  respete los principios (costo cero, sin frameworks, contenido en
  markdown).

Los cambios grandes o riesgosos (secretos, despliegue, rutinas, borrar
contenido, servicios externos) no se aplican solos: quedan abiertos con
una propuesta para que Mateo decida. Tras cada ajuste aplicado, Claude
comenta en el issue qué cambió y lo cierra.

Configuración, una sola vez, en Cloudflare → Worker `otra-lectura` →
Settings → Runtime variables and secrets (tipo Secret; no en la sección
Build, que solo existe durante el build):

- `GITHUB_TOKEN`: token fine-grained de GitHub, solo para este repo, con
  permiso *Issues: Read and write*.
- `CLAVE_FAMILIA`: la clave que se escribe en el formulario.

## Estructura

```
ediciones/          fuente: una edición por archivo .md
prompt.md           formato editorial del radar
RUTINA.md           instrucciones de la edición diaria automática (5:00 a. m. Colombia)
ESPECIFICACION.md   especificación técnica
plantilla/          base.html, estilo.css y fuentes/ (Instrument Serif, UnifrakturMaguntia y Manrope, OFL)
scripts/build.py    markdown → HTML, verificación, candidatas
scripts/frontmatter.py  lector del frontmatter (subconjunto de YAML, sin dependencias)
scripts/graficos.py bloques ```grafico → gráficos HTML/SVG
ayuda.md            página "Cómo participar" (instrucciones para lectores)
sobre.md            página "¿Qué es esto?"
candidatas.md       estado de las candidatas (editable a mano)
build.sh            prepara .venv y ejecuta el build
deploy.sh           build + commit + push
site/               salida generada (se publica tal cual)
wrangler.jsonc      Cloudflare Workers: site/ como estáticos y /api/* al Worker
src/worker.js       recibe el formulario de ajustes y crea el issue en GitHub
AJUSTES.md          reglas de estilo acumuladas a partir de los ajustes
```
