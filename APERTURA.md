# Abrir Otra lectura al público

Todo está listo pero apagado. Mientras no se haga esto, el sitio sigue
como hoy: comentar y corregir exige la clave familiar, y los buscadores no
lo indexan.

## Qué cambia al abrirlo

- **Cualquier lector puede comentar** (seleccionar una frase → 💬 Comentar,
  el recuadro de comentarios, 🎤 Hablar y "¿Cómo le quedó?") poniendo solo
  su nombre. Una verificación de Cloudflare Turnstile, casi siempre
  invisible, filtra los robots.
- Los comentarios de lectores llegan como issues **`[Lector] …`** y **no se
  aplican solos**: la revisión horaria no los toca. Los leen ustedes y
  deciden (si uno vale, se copia como ajuste o se aplica a mano).
- Límite para lectores: 5 comentarios de hasta 1.500 caracteres por envío.
- **Corregir el texto directamente queda solo para los editores**: el
  texto se vuelve editable únicamente en los aparatos que tienen la clave
  familiar guardada. En los demás, tocar el texto no abre el teclado.
- Mateo y su papá siguen igual, con su clave: sus notas son `[Ajuste]` y
  sus correcciones `[Edición]`, y se aplican cada hora.

## Pasos (unos 10 minutos)

1. **Crear el widget de Turnstile** (gratis): en el panel de Cloudflare →
   *Turnstile* → *Add widget*. Nombre: "Otra lectura". Dominio: el del
   sitio (`….workers.dev`). Modo: *Managed*. Cloudflare entrega dos claves:
   una **site key** (pública) y una **secret key** (privada).
2. **Guardar la secret key en el Worker**: Workers → otra-lectura →
   *Settings* → *Variables and Secrets* → *Add* → tipo **Secret**, nombre
   `TURNSTILE_SECRET`, valor: la secret key. (Igual que se hizo con
   `GITHUB_TOKEN`; debe ser variable de ejecución, no de build.)
3. **Pasarle a Claude la site key** (la pública) para ponerla en
   `scripts/build.py`:
   ```python
   COMENTARIOS_ABIERTOS = True
   TURNSTILE_SITEKEY = "0x4AAAA…"
   ```
4. **Buscadores** (opcional, al mismo tiempo o después): en
   `scripts/build.py`, `INDEXAR = True` y `SITIO_URL = "https://….workers.dev"`
   (con la dirección real). Eso activa el sitemap, la dirección canónica y
   la imagen de vista previa al compartir.
5. Publicar (`./deploy.sh` o push a `main`). Cloudflare despliega solo.

## Para volver a cerrarlo

`COMENTARIOS_ABIERTOS = False` en `scripts/build.py` y publicar. Si además
se borra `TURNSTILE_SECRET` del Worker, el Worker vuelve a exigir la clave
aunque alguien intente enviar sin ella.
