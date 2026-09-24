var __defProp = Object.defineProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });

// src/worker.js
var REPO = "MateoPosadaZea/otra-lectura";
var MAX_TEXTO = 4e3;
var worker_default = {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/api/ajuste") return recibirAjuste(request, env);
    return env.ASSETS.fetch(request);
  }
};
async function recibirAjuste(request, env) {
  if (request.method !== "POST") {
    return respuesta(405, "M\xE9todo no permitido", "Este enlace solo recibe el formulario de ajustes.", "/");
  }
  let datos;
  try {
    datos = await request.formData();
  } catch {
    return respuesta(400, "Formulario inv\xE1lido", "No se pudo leer el formulario.", "/");
  }
  const volver = limpiarRuta(datos.get("pagina"));
  const texto = String(datos.get("texto") || "").trim();
  const quien = String(datos.get("quien") || "").trim().slice(0, 80) || "Sin nombre";
  const titulo = String(datos.get("titulo") || "Otra lectura").trim().slice(0, 100);
  const clave = String(datos.get("clave") || "");
  if (!env.CLAVE_FAMILIA || !env.GITHUB_TOKEN) {
    return respuesta(
      503,
      "Formulario sin configurar",
      "Faltan los secretos GITHUB_TOKEN o CLAVE_FAMILIA en Cloudflare.",
      volver
    );
  }
  if (!await igualesSeguro(clave, env.CLAVE_FAMILIA)) {
    return respuesta(401, "Clave incorrecta", "Revise la clave e int\xE9ntelo de nuevo.", volver);
  }
  if (!texto) {
    return respuesta(400, "Ajuste vac\xEDo", "Escriba el ajuste antes de enviarlo.", volver);
  }
  if (texto.length > MAX_TEXTO) {
    return respuesta(400, "Ajuste demasiado largo", `El m\xE1ximo es de ${MAX_TEXTO} caracteres.`, volver);
  }
  const cuerpo = [
    `**P\xE1gina:** ${volver}`,
    `**Enviado por:** ${quien}`,
    `**Fecha:** ${(/* @__PURE__ */ new Date()).toISOString()}`,
    "",
    "---",
    "",
    texto
  ].join("\n");
  const gh = await fetch(`https://api.github.com/repos/${REPO}/issues`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${env.GITHUB_TOKEN}`,
      "Accept": "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "otra-lectura-ajustes",
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ title: `[Ajuste] ${titulo}`, body: cuerpo })
  });
  if (!gh.ok) {
    console.error("GitHub respondi\xF3", gh.status, await gh.text());
    return respuesta(
      502,
      "No se pudo guardar",
      "El ajuste no qued\xF3 registrado. Int\xE9ntelo de nuevo en unos minutos.",
      volver
    );
  }
  return respuesta(
    200,
    "Ajuste recibido",
    "Qued\xF3 registrado. Se aplica en la pr\xF3xima revisi\xF3n, cada hora entre las 6 a. m. y las 10 p. m.",
    volver
  );
}
__name(recibirAjuste, "recibirAjuste");
function limpiarRuta(valor) {
  const ruta = String(valor || "/");
  return /^\/[\w\-./]*$/.test(ruta) && !ruta.startsWith("//") ? ruta : "/";
}
__name(limpiarRuta, "limpiarRuta");
async function igualesSeguro(a, b) {
  const enc = new TextEncoder();
  const [ha, hb] = await Promise.all([
    crypto.subtle.digest("SHA-256", enc.encode(a)),
    crypto.subtle.digest("SHA-256", enc.encode(b))
  ]);
  const x = new Uint8Array(ha), y = new Uint8Array(hb);
  let dif = 0;
  for (let i = 0; i < x.length; i++) dif |= x[i] ^ y[i];
  return dif === 0;
}
__name(igualesSeguro, "igualesSeguro");
function escapar(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}
__name(escapar, "escapar");
function respuesta(estado, titulo, mensaje, volver) {
  const html = `<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>${escapar(titulo)} \xB7 Otra lectura</title>
<link rel="stylesheet" href="/estilo.css">
</head>
<body>
<header class="sitio"><p class="lado"></p><a class="cabezote" href="/index.html">Otra Lectura</a><p class="lado"></p></header>
<main>
<header class="cabecera">
<h1>${escapar(titulo)}</h1>
<p class="bajada">${escapar(mensaje)}</p>
</header>
<p style="text-align:center"><a href="${escapar(volver)}">Volver a la p\xE1gina</a></p>
</main>
</body>
</html>`;
  return new Response(html, {
    status: estado,
    headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" }
  });
}
__name(respuesta, "respuesta");

// ../../../root/.npm/_npx/c943b712072b77c4/node_modules/wrangler/templates/middleware/middleware-ensure-req-body-drained.ts
var drainBody = /* @__PURE__ */ __name(async (request, env, _ctx, middlewareCtx) => {
  try {
    return await middlewareCtx.next(request, env);
  } finally {
    try {
      if (request.body !== null && !request.bodyUsed) {
        const reader = request.body.getReader();
        while (!(await reader.read()).done) {
        }
      }
    } catch (e) {
      console.error("Failed to drain the unused request body.", e);
    }
  }
}, "drainBody");
var middleware_ensure_req_body_drained_default = drainBody;

// ../../../root/.npm/_npx/c943b712072b77c4/node_modules/wrangler/templates/middleware/middleware-miniflare3-json-error.ts
function reduceError(e) {
  return {
    name: e?.name,
    message: e?.message ?? String(e),
    stack: e?.stack,
    cause: e?.cause === void 0 ? void 0 : reduceError(e.cause)
  };
}
__name(reduceError, "reduceError");
var jsonError = /* @__PURE__ */ __name(async (request, env, _ctx, middlewareCtx) => {
  try {
    return await middlewareCtx.next(request, env);
  } catch (e) {
    const error = reduceError(e);
    const body = JSON.stringify(error);
    const headers = {
      "Content-Type": "application/json",
      "MF-Experimental-Error-Stack": "true"
    };
    const encoded = encodeURIComponent(body);
    if (encoded.length <= 8192) {
      headers["MF-Experimental-Error-Stack-Payload"] = encoded;
    }
    return new Response(body, { status: 500, headers });
  }
}, "jsonError");
var middleware_miniflare3_json_error_default = jsonError;

// .wrangler/tmp/bundle-KeLMra/middleware-insertion-facade.js
var __INTERNAL_WRANGLER_MIDDLEWARE__ = [
  middleware_ensure_req_body_drained_default,
  middleware_miniflare3_json_error_default
];
var middleware_insertion_facade_default = worker_default;

// ../../../root/.npm/_npx/c943b712072b77c4/node_modules/wrangler/templates/middleware/common.ts
var __facade_middleware__ = [];
function __facade_register__(...args) {
  __facade_middleware__.push(...args.flat());
}
__name(__facade_register__, "__facade_register__");
function __facade_invokeChain__(request, env, ctx, dispatch, middlewareChain) {
  const [head, ...tail] = middlewareChain;
  const middlewareCtx = {
    dispatch,
    next(newRequest, newEnv) {
      return __facade_invokeChain__(newRequest, newEnv, ctx, dispatch, tail);
    }
  };
  return head(request, env, ctx, middlewareCtx);
}
__name(__facade_invokeChain__, "__facade_invokeChain__");
function __facade_invoke__(request, env, ctx, dispatch, finalMiddleware) {
  return __facade_invokeChain__(request, env, ctx, dispatch, [
    ...__facade_middleware__,
    finalMiddleware
  ]);
}
__name(__facade_invoke__, "__facade_invoke__");

// .wrangler/tmp/bundle-KeLMra/middleware-loader.entry.ts
var __Facade_ScheduledController__ = class ___Facade_ScheduledController__ {
  constructor(scheduledTime, cron, noRetry) {
    this.scheduledTime = scheduledTime;
    this.cron = cron;
    this.#noRetry = noRetry;
  }
  scheduledTime;
  cron;
  static {
    __name(this, "__Facade_ScheduledController__");
  }
  #noRetry;
  noRetry() {
    if (!(this instanceof ___Facade_ScheduledController__)) {
      throw new TypeError("Illegal invocation");
    }
    this.#noRetry();
  }
};
function wrapExportedHandler(worker) {
  if (__INTERNAL_WRANGLER_MIDDLEWARE__ === void 0 || __INTERNAL_WRANGLER_MIDDLEWARE__.length === 0) {
    return worker;
  }
  for (const middleware of __INTERNAL_WRANGLER_MIDDLEWARE__) {
    __facade_register__(middleware);
  }
  const fetchDispatcher = /* @__PURE__ */ __name(function(request, env, ctx) {
    if (worker.fetch === void 0) {
      throw new Error("Handler does not export a fetch() function.");
    }
    return worker.fetch(request, env, ctx);
  }, "fetchDispatcher");
  return {
    ...worker,
    fetch(request, env, ctx) {
      const dispatcher = /* @__PURE__ */ __name(function(type, init) {
        if (type === "scheduled" && worker.scheduled !== void 0) {
          const controller = new __Facade_ScheduledController__(
            Date.now(),
            init.cron ?? "",
            () => {
            }
          );
          return worker.scheduled(controller, env, ctx);
        }
      }, "dispatcher");
      return __facade_invoke__(request, env, ctx, dispatcher, fetchDispatcher);
    }
  };
}
__name(wrapExportedHandler, "wrapExportedHandler");
function wrapWorkerEntrypoint(klass) {
  if (__INTERNAL_WRANGLER_MIDDLEWARE__ === void 0 || __INTERNAL_WRANGLER_MIDDLEWARE__.length === 0) {
    return klass;
  }
  for (const middleware of __INTERNAL_WRANGLER_MIDDLEWARE__) {
    __facade_register__(middleware);
  }
  return class extends klass {
    #fetchDispatcher = /* @__PURE__ */ __name((request, env, ctx) => {
      this.env = env;
      this.ctx = ctx;
      if (super.fetch === void 0) {
        throw new Error("Entrypoint class does not define a fetch() function.");
      }
      return super.fetch(request);
    }, "#fetchDispatcher");
    #dispatcher = /* @__PURE__ */ __name((type, init) => {
      if (type === "scheduled" && super.scheduled !== void 0) {
        const controller = new __Facade_ScheduledController__(
          Date.now(),
          init.cron ?? "",
          () => {
          }
        );
        return super.scheduled(controller);
      }
    }, "#dispatcher");
    fetch(request) {
      return __facade_invoke__(
        request,
        this.env,
        this.ctx,
        this.#dispatcher,
        this.#fetchDispatcher
      );
    }
  };
}
__name(wrapWorkerEntrypoint, "wrapWorkerEntrypoint");
var WRAPPED_ENTRY;
if (typeof middleware_insertion_facade_default === "object") {
  WRAPPED_ENTRY = wrapExportedHandler(middleware_insertion_facade_default);
} else if (typeof middleware_insertion_facade_default === "function") {
  WRAPPED_ENTRY = wrapWorkerEntrypoint(middleware_insertion_facade_default);
}
var middleware_loader_entry_default = WRAPPED_ENTRY;
export {
  __INTERNAL_WRANGLER_MIDDLEWARE__,
  middleware_loader_entry_default as default
};
//# sourceMappingURL=worker.js.map
