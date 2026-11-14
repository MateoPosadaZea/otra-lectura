# Instagram de Otra Lectura: kit para abrir la cuenta

Preparado el 14 de noviembre de 2026. Las imágenes están en esta carpeta y se
regeneran con `NODE_PATH=$(npm root -g) node scripts/instagram.cjs`.

## 1. Datos del perfil

| Campo | Qué poner |
|---|---|
| Usuario | **@otralectura.co** (cuenta creada el 14 de noviembre de 2026; enlazada desde el pie del sitio) |
| Nombre | **Otra Lectura** |
| Foto | `perfil-c-sello.png` (recomendada), `perfil-a-nombre.png` o `perfil-b-monograma.png` |
| Descripción | ver abajo (máximo 150 caracteres) |
| Enlace | **https://otralectura.co** |
| Tipo de cuenta | Profesional, categoría **Medio de comunicación/noticias** (da las estadísticas para validar el público, ver PUBLICO.md) |
| Pronombres, contacto, botones | Vacíos por ahora |

### Descripción (elegir una)

1. Recomendada, 119 caracteres:

   > Un periódico pequeño para entender los temas de gran impacto.
   > Una edición cada mañana, con sus fuentes.
   > Desde Colombia.

2. Con el horizonte, 114 caracteres:

   > Lo que puede cambiar cómo viviremos en 10 a 50 años, contado desde Colombia.
   > Una edición cada mañana, con fuentes.

3. Más corta, 102 caracteres:

   > Para entender, no solo enterarse.
   > Una edición cada mañana antes de las 6, con fuentes.
   > Desde Colombia.

Los saltos de línea se escriben en la app tal cual. Sin emojis.

## 2. Historias destacadas

Cuatro portadas, en el orden en que se crean:

| Portada | Nombre | Qué guardar ahí |
|---|---|---|
| `destacada-quienes-somos.png` | Quiénes somos | El reel de presentación |
| `destacada-mapas.png` | Mapas | Las escenas de mapas de cada nota |
| `destacada-graficos.png` | Gráficos | Las gráficas que más se compartan |
| `destacada-para-conversar.png` | Para conversar | La pregunta de cada edición |

Una destacada solo se puede crear desde una historia publicada: se sube la
historia, se agrega a destacada y se le cambia la portada por la imagen.

## 3. Las tres primeras publicaciones

Se publican en este orden, para que la cuadrícula del perfil abra con la
presentación arriba a la izquierda. Cada una es un reel (`reel.mp4`); el
carrusel (`carrusel-N.png`) sirve como alternativa o para historias.

1. **Catastro** (`redes/salida/2026-11-13-radar/`), texto en `pie.txt`.
2. **Maíz y bacterias** (`redes/salida/2026-11-14-radar/`), texto en `pie.txt`.
3. **Quiénes somos** (`redes/salida/quienes-somos/`), texto en `pie.txt`.
   Fijarla arriba del perfil (los tres puntos del reel, «Fijar en tu perfil»).

Al subir cada reel:

- Portada del reel: elegir el cuadro del titular (la primera pantalla).
- Música: opcional, instrumental y suave, a volumen bajo. Los reels salen sin
  sonido para que se entiendan igual sin él.
- Texto alternativo (Configuración avanzada): una frase con el titular.
- «Compartir también en Facebook»: no, por ahora.

## 4. Ritmo

- Un reel por edición, publicado entre las 7 y las 8 de la mañana (hora de
  Colombia), cuando la edición ya está en el sitio.
- La pregunta de «Para conversar» como historia, con el sticker de pregunta o
  de encuesta, a mediodía.
- Las notas antiguas sirven: dos o tres a la semana, mientras el perfil se
  llena.

## 5. Cómo vamos a saber si funciona

A las tres o cuatro semanas, en las estadísticas de la cuenta profesional:
edad y ciudad de quienes siguen (¿coincide con PUBLICO.md?), qué reels se
guardan y se comparten, y cuántas visitas llegan al sitio desde Instagram.
