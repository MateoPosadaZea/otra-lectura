// Worker de Otra lectura.
// Sirve site/ como estáticos y recibe los ajustes (contenido, estilo o
// funciones del sitio) en
// POST /api/ajuste. Cada ajuste queda como issue "[Ajuste] …" en GitHub;
// la revisión horaria de Claude los aplica y los cierra.
//
// Secretos (Cloudflare → Worker → Settings → Variables and Secrets):
//   GITHUB_TOKEN   token fine-grained con permiso Issues: Read and write
//                  sobre el repo otra-lectura.
//   CLAVE_FAMILIA  clave que se escribe en el formulario.

const REPO = "MateoPosadaZea/otra-lectura";
const MAX_TEXTO = 4000;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/api/ajuste") return recibirAjuste(request, env);
    return env.ASSETS.fetch(request);
  },
};

async function recibirAjuste(request, env) {
  if (request.method !== "POST") {
    return respuesta(405, "Método no permitido", "Este enlace solo recibe el formulario de ajustes.", "/");
  }

  let datos;
  try {
    datos = await request.formData();
  } catch {
    return respuesta(400, "Formulario inválido", "No se pudo leer el formulario.", "/");
  }

  const volver = limpiarRuta(datos.get("pagina"));
  const texto = String(datos.get("texto") || "").trim();
  const quien = String(datos.get("quien") || "").trim().slice(0, 80) || "Sin nombre";
  const titulo = String(datos.get("titulo") || "Otra lectura").trim().slice(0, 100);
  const clave = String(datos.get("clave") || "");

  if (!env.CLAVE_FAMILIA || !env.GITHUB_TOKEN) {
    return respuesta(503, "Formulario sin configurar",
      "Faltan los secretos GITHUB_TOKEN o CLAVE_FAMILIA en Cloudflare.", volver);
  }
  if (!(await igualesSeguro(clave, env.CLAVE_FAMILIA))) {
    return respuesta(401, "Clave incorrecta", "Revise la clave e inténtelo de nuevo.", volver);
  }
  if (!texto) {
    return respuesta(400, "Ajuste vacío", "Escriba el ajuste antes de enviarlo.", volver);
  }
  if (texto.length > MAX_TEXTO) {
    return respuesta(400, "Ajuste demasiado largo", `El máximo es de ${MAX_TEXTO} caracteres.`, volver);
  }

  const cuerpo = [
    `**Página:** ${volver}`,
    `**Enviado por:** ${quien}`,
    `**Fecha:** ${new Date().toISOString()}`,
    "",
    "---",
    "",
    texto,
  ].join("\n");

  const gh = await fetch(`https://api.github.com/repos/${REPO}/issues`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${env.GITHUB_TOKEN}`,
      "Accept": "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "otra-lectura-ajustes",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ title: `[Ajuste] ${titulo}`, body: cuerpo }),
  });

  if (!gh.ok) {
    console.error("GitHub respondió", gh.status, await gh.text());
    return respuesta(502, "No se pudo guardar",
      "El ajuste no quedó registrado. Inténtelo de nuevo en unos minutos.", volver);
  }

  return respuesta(200, "Ajuste recibido",
    "Quedó registrado. Se revisa en la próxima hora, entre las 6 a. m. y las 10 p. m.", volver);
}

// Solo rutas internas del sitio, para no redirigir a otro dominio.
function limpiarRuta(valor) {
  const ruta = String(valor || "/");
  return /^\/[\w\-./]*$/.test(ruta) && !ruta.startsWith("//") ? ruta : "/";
}

// Compara las claves por su hash para no filtrar información por tiempos.
async function igualesSeguro(a, b) {
  const enc = new TextEncoder();
  const [ha, hb] = await Promise.all([
    crypto.subtle.digest("SHA-256", enc.encode(a)),
    crypto.subtle.digest("SHA-256", enc.encode(b)),
  ]);
  const x = new Uint8Array(ha), y = new Uint8Array(hb);
  let dif = 0;
  for (let i = 0; i < x.length; i++) dif |= x[i] ^ y[i];
  return dif === 0;
}

function escapar(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

function respuesta(estado, titulo, mensaje, volver) {
  const html = `<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>${escapar(titulo)} · Otra lectura</title>
<link rel="stylesheet" href="/estilo.css">
</head>
<body>
<header class="sitio"><p class="lado"></p><a class="cabezote" href="/index.html">Otra Lectura</a><p class="lado"></p></header>
<main>
<header class="cabecera">
<h1>${escapar(titulo)}</h1>
<p class="bajada">${escapar(mensaje)}</p>
</header>
<p style="text-align:center"><a href="${escapar(volver)}">Volver a la página</a></p>
</main>
</body>
</html>`;
  return new Response(html, {
    status: estado,
    headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" },
  });
}
