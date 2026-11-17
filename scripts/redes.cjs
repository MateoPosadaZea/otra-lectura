// Piezas para redes a partir de un guion (redes/guiones/<slug>.json):
//   - reel.mp4: video vertical 1080 × 1920, animado, sin audio (la música se
//     pone en Instagram al subirlo).
//   - carrusel-N.png: una lámina 1080 × 1350 por escena, en su estado final.
//   - pie.txt: el texto del post.
//
// Uso: NODE_PATH=$(npm root -g) node scripts/redes.cjs redes/guiones/<slug>.json [--solo-carrusel] [--cuadro=MS]
// Sale en redes/salida/<slug>/. No forma parte del build del sitio: necesita
// Chromium (Playwright) y ffmpeg, que no existen en el build de Cloudflare.

const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");
const { chromium } = require("playwright");
const V = require("./redes-visuales.cjs");
const A = require("./redes-anatomia.cjs");
const M = require("./redes-montaje.cjs");

const RAIZ = path.resolve(__dirname, "..");
const FPS = 30;
const CAPTURA = 60; // dos capturas por cuadro final: desenfoque de movimiento

const TIPOS = {
  // titular, texto. Las fuentes viven en plantilla/fuentes y redes/fuentes (sin red).
  actual: { titular: "'Instrument Serif'", peso: 400, texto: "'Inter Tight'" },
};

function esc(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function numero(v, dec) {
  return v.toLocaleString("es-CO", { minimumFractionDigits: dec, maximumFractionDigits: dec });
}

// Palabras con su retraso; ==así== marca lo que se subraya.
function palabras(texto, inicio, paso, punto = true) {
  const total = contar(texto);
  const partes = texto.split(/(==[^=]+==)/).filter(Boolean);
  let i = 0;
  let html = "";
  const marcas = [];
  for (const p of partes) {
    const marcado = p.startsWith("==");
    const limpio = marcado ? p.slice(2, -2) : p;
    const ws = limpio.split(/(\s+)/);
    let trozo = "";
    for (const w of ws) {
      if (!w) continue;
      if (/^\s+$/.test(w)) { trozo += " "; continue; }
      const t = Math.round(inicio + i * paso);
      const final = punto && i === total - 1 && /[^.]\.$/.test(w);
      const txt = final ? `${esc(w.slice(0, -1))}<span class="punto" data-t="${t + 350}"></span>` : esc(w);
      trozo += `<span class="wm"><span class="w" style="animation-delay:${t}ms">${txt}</span></span>`;
      i++;
    }
    if (marcado) {
      const id = marcas.length;
      marcas.push(id);
      trozo = `<mark class="m" style="animation-delay:${Math.round(inicio + i * paso + 250)}ms">${trozo}</mark>`;
    }
    html += trozo;
  }
  return { html, n: i, fin: inicio + i * paso };
}

// Para textos sin animación por palabra: el punto final en rojo.
function puntoFinal(texto, t) {
  return /[^.]\.$/.test(texto) ? `${esc(texto.slice(0, -1))}<span class="punto" data-t="${t}"></span>` : esc(texto);
}

function contar(texto) {
  return texto.replace(/==/g, "").split(/\s+/).filter(Boolean).length;
}

// Tiempo para leer: una letra cada 1/15 s más 1,5 s de respiro (regla de
// lectura de las guías de dirección de cine explicativo).
// Aquí las palabras entran de a una y se leen mientras aparecen, así que la
// cuenta empieza cuando arranca el texto, no cuando termina de entrar.
function lectura(texto, inicio, paso) {
  const limpio = (texto || "").replace(/==/g, "");
  return inicio + (limpio.length / 15) * 1000 + 1500 + 300;
}

function duracion(e) {
  return Math.round(Math.max(duracionBase(e), duracionLectura(e)));
}

function duracionLectura(e) {
  switch (e.tipo) {
    case "portada": return lectura(e.titulo, 700, 110);
    case "frase": return lectura(e.texto, 350, 140);
    case "cifra": return lectura(e.texto, 1700, 90);
    case "cita": return lectura(e.texto, 300, 120);
    case "explica": return lectura(e.texto, 1400, 120);
    case "giro": return lectura(e.texto, 600, 140);
    default: return 0;
  }
}

function duracionBase(e) {
  switch (e.tipo) {
    case "portada": return 5200;
    case "frase": return Math.max(3400, 1300 + contar(e.texto) * 330);
    case "cifra": return 5000;
    case "grafico": return e.meta ? 8600 : 6800;
    case "cierre": return 4600;
    case "firma": return 2800;
    case "logo": return 4200;
    case "cita": return Math.max(5200, 1600 + contar(e.texto) * 300);
    case "montaje": return M.duracionMontaje(e);
    case "pausa": return e.ms || 1500;
    case "giro": return Math.max(4200, 1400 + contar(e.texto) * 330);
    case "anatomia": return 500 + A.tiempos(e).fin + 400;
    case "explica": return Math.max(e.visual && e.visual.tipo === "mapa" ? (e.visual.zoom ? 7600 : 6000) : 5200, 2600 + contar(e.texto) * 300);
    default: return 4000;
  }
}

function escena(e, t0, d, g, ultima, primera, n, paso) {
  // Sale acelerando hacia arriba; la siguiente ya viene entrando (se solapan).
  const sale = ultima ? "" : `, sale 420ms var(--salida) ${t0 + d - 420}ms forwards`;
  const ent = primera ? t0 : t0 - 140;
  const base = `id="esc-${n}" class="esc esc-${e.tipo}" style="animation: entra 1000ms var(--suave) ${ent}ms both${sale}"`;
  // La portada queda quieta: el grabado no se mueve.
  let html = escenaHtml(e, t0, d, g, base);
  html = e.tipo === "portada" ? html : cam(html, t0, d);
  // «3 / 9»: cuántos pasos lleva la historia; ayuda a quedarse hasta el final.
  if (paso) html = html.replace(/<\/section>$/, `<div class="paso">${paso[0]} / ${paso[1]}</div></section>`);
  return html;
}

// Cámara viva: cada pantalla se acerca muy despacio mientras se lee.
function cam(html, t0, d) {
  return html.replace(/^(<section [^>]*>)([\s\S]*)(<\/section>)$/, (m, a, b, c) =>
    `${a}<div class="cam" style="animation: deriva ${d + 600}ms linear ${t0 - 140}ms both">${b}</div>${c}`);
}

function escenaHtml(e, t0, d, g, base) {
  if (e.tipo === "portada") {
    const p = palabras(e.titulo, t0 + 700, 110);
    return `<section ${base}>
      <div class="foto"><img src="${g.imagenUrl}"></div>
      <div class="rot" style="animation: sube 600ms var(--suave) ${t0 + 300}ms both">${esc(e.rotulo)} · ${esc(g.fecha)}</div>
      <h1 class="tit">${p.html}</h1>
    </section>`;
  }
  if (e.tipo === "montaje") {
    return `<section ${base}>${M.montaje(e, t0)}</section>`;
  }
  if (e.tipo === "pausa") {
    return `<section ${base}><div class="pausa-punto" style="animation: late 900ms linear ${t0 + 200}ms infinite"></div></section>`;
  }
  if (e.tipo === "giro") {
    const p = palabras(e.texto, t0 + 600, 140);
    const n = contar(e.texto);
    const tam = n <= 8 ? "corta" : n <= 16 ? "media" : "larga";
    return `<section ${base}><div class="giro-fondo" style="animation: llena 800ms var(--suave) ${t0}ms both"></div><p class="frase ${tam}">${p.html}</p></section>`;
  }
  if (e.tipo === "frase") {
    const p = palabras(e.texto, t0 + 350, 140);
    const n = contar(e.texto);
    const tam = n <= 8 ? "corta" : n <= 16 ? "media" : "larga";
    return `<section ${base}><p class="frase ${tam}">${p.html}</p></section>`;
  }
  if (e.tipo === "cifra") {
    const dec = String(e.valor).includes(".") ? String(e.valor).split(".")[1].length : 0;
    const p = palabras(e.texto, t0 + 1700, 90);
    return `<section ${base}>
      <div class="cifra" style="animation: escala 1300ms var(--muelle) ${t0 + 200}ms both"><span class="cuenta" data-hasta="${e.valor}" data-dec="${dec}" data-ini="${t0 + 300}" data-dur="1400">0</span><span class="suf" style="animation: sube 500ms var(--suave) ${t0 + 1500}ms both">${esc(e.sufijo || "")}</span></div>
      <p class="cifra-txt">${p.html}</p>
    </section>`;
  }
  if (e.tipo === "grafico") {
    // "meta": {"valor", "etiqueta"} dibuja la promesa como línea punteada;
    // "brecha": texto que marca lo que falta sobre la barra destacada.
    const meta = e.meta && +e.meta.valor;
    const max = Math.max(meta || 0, ...e.datos.map((x) => x.valor));
    const n = e.datos.length, tMeta = t0 + 900 + n * 450 + 300;
    const cols = e.datos.map((x, i) => {
      const t = t0 + 900 + i * 450;
      const alto = (x.valor / max) * 100;
      const dest = x.etiqueta === e.destacar ? " dest" : "";
      const dec = String(x.valor).includes(".") ? 1 : 0;
      return `<div class="col${dest}">
        <div class="barra-c"><div class="val" style="bottom:calc(${alto}% + 10px);animation: sube 400ms var(--suave) ${t + 500}ms both">${numero(x.valor, dec)}${esc(e.unidad || "")}</div><div class="barra" style="height:${alto}%;animation: crece 1300ms var(--muelle) ${t}ms both"></div>${
          meta && i === 0 ? `<div class="g-meta" style="bottom:${(meta / max) * 100}%;width:calc(${n} * 100% + ${(n - 1) * 34}px);animation: dibuja-x 1100ms var(--trazo) ${tMeta}ms both"><span style="animation: sube 700ms var(--suave) ${tMeta + 700}ms both">${esc(e.meta.etiqueta || "")}</span></div>` : ""}${
          meta && e.brecha && dest ? `<div class="g-brecha" style="bottom:calc(${alto}% + 66px);height:calc(${((meta - x.valor) / max) * 100}% - 66px);animation: crece 900ms var(--trazo) ${tMeta + 1100}ms both"><span style="animation: sube 700ms var(--suave) ${tMeta + 1700}ms both">${esc(e.brecha)}</span></div>` : ""}</div>
        <div class="etq">${esc(x.etiqueta)}</div></div>`;
    }).join("");
    return `<section ${base}>
      <h2 class="g-tit" style="animation: sube 500ms var(--suave) ${t0 + 200}ms both">${esc(e.titulo)}</h2>
      <div class="cols">${cols}</div>
      <div class="g-fuente" style="animation: sube 500ms var(--suave) ${t0 + 900}ms both">Fuente: ${esc(e.fuente || "")}</div>
    </section>`;
  }
  if (e.tipo === "logo") {
    return `<section ${base}>
      <div class="logo-xl"><span class="logo-anim" style="animation: logo 1800ms var(--suave) ${t0 + 200}ms both">Otra Lectura</span></div>
      <p class="logo-bajada" style="animation: sube 600ms var(--suave) ${t0 + 1500}ms both">${puntoFinal(e.texto || "", t0 + 1700)}</p>
    </section>`;
  }
  if (e.tipo === "cita") {
    // Comillas: "cursiva" (una “ grande en la serif cursiva), "latinas" (« »
    // finas, colgadas al margen) o "gotica" (la “ de la letra del logo).
    const estilo = e.comillas || "cursiva";
    const p = palabras(e.texto, t0 + 300, 120);
    const marca = { cursiva: "“", latinas: "«", gotica: "“" }[estilo];
    return `<section ${base}>
      <div class="comillas com-${estilo}" style="animation: llega 1200ms var(--suave) ${t0}ms both">${marca}</div>
      <p class="cita cita-${estilo}">${p.html}</p>
      <p class="autor" style="animation: sube 500ms var(--suave) ${p.fin + 300}ms both">${esc(e.autor || "")}</p>
    </section>`;
  }
  if (e.tipo === "anatomia") {
    const p = palabras(e.titulo, t0 + 150, 110, false);
    const fig = A.anatomia(e, t0 + 500, t0);
    return `<section ${base}>
      <h2 class="an-tit">${p.html}</h2>
      <p class="an-bajada" style="animation: sube 600ms var(--suave) ${t0 + 700}ms both">${esc(e.bajada || "")}</p>
      <div class="an-fig">${fig.svg}</div>
    </section>`;
  }
  if (e.tipo === "explica") {
    const vis = V.visual(e.visual, t0 + 250);
    const p = palabras(e.texto, t0 + 1400, 120);
    return `<section ${base}>
      <div class="vis">${vis}</div>
      <p class="exp">${p.html}</p>
    </section>`;
  }
  if (e.tipo === "cierre") {
    return `<section ${base}>
      <p class="cierre-txt" style="animation: sube 500ms var(--suave) ${t0 + 200}ms both">${esc(e.texto)}</p>
      <div class="url" style="animation: sube 600ms var(--suave) ${t0 + 800}ms both">otralectura<span class="punto" data-t="${t0 + 1100}"></span>co</div>
      <div class="ed" style="animation: sube 500ms var(--suave) ${t0 + 1300}ms both">${g.edicion ? `Edición ${esc(g.edicion)} · ${esc(g.fecha)}` : esc(e.bajada || "Una edición cada mañana")}</div>
    </section>`;
  }
  if (e.tipo === "firma") {
    // Lámina final. "lema": logo y lema; "grabado": sobre un grabado tenue;
    // "marco": filete doble de portadilla. Se pueden combinar: "grabado marco".
    const estilo = e.estilo || g.firma || "lema";
    const fondo = estilo.includes("grabado") && g.fondoUrl
      ? `<div class="firma-fondo" style="background-image:url('${g.fondoUrl}');animation: llega 1600ms var(--suave) ${t0}ms both"></div>` : "";
    const marco = estilo.includes("marco") ? `<div class="firma-marco" style="animation: llega 1200ms var(--suave) ${t0 + 200}ms both"></div>` : "";
    return `<section ${base}>${fondo}${marco}
      <div class="logo-xl" style="margin:0"><span class="logo-anim" style="animation: logo 1600ms var(--suave) ${t0 + 100}ms both">Otra Lectura</span></div>
      <p class="firma-lema" style="animation: sube 900ms var(--suave) ${t0 + 700}ms both">${puntoFinal("Un periódico pequeño para entender los temas de gran impacto.", 0)}</p>
    </section>`;
  }
  throw new Error(`tipo de escena desconocido: ${e.tipo}`);
}

function html(guion, alto, tipo) {
  const f = (n) => "file://" + path.join(RAIZ, "plantilla", "fuentes", n);
  let t = 0;
  const tiempos = [];
  const g = {
    fecha: guion.fecha,
    edicion: guion.edicion,
    imagenUrl: guion.imagen ? "file://" + path.join(RAIZ, guion.imagen) : "",
    // Grabado de la lámina final: el de la edición o, si no hay, el de la
    // Comisión Corográfica (Ed. 66).
    fondoUrl: "file://" + path.join(RAIZ, guion.imagen || "imagenes/2026-11-13-radar.webp"),
    firma: guion.firma,
  };
  const escenas = guion.escenas.slice();
  if (escenas.length && escenas[escenas.length - 1].tipo === "cierre") escenas.push({ tipo: "firma" });
  const cuentan = (e) => !["cierre", "firma", "logo", "montaje", "pausa", "giro"].includes(e.tipo);
  const totalPasos = escenas.filter(cuentan).length;
  let paso = 0;
  const secciones = escenas.map((e, i) => {
    const d = duracion(e);
    tiempos.push({ ini: t, dur: d, tipo: e.tipo });
    const s = escena(e, t, d, g, i === escenas.length - 1, i === 0, i, cuentan(e) ? [++paso, totalPasos] : null);
    t += d;
    return s;
  }).join("\n");
  const total = t;
  // En la portada con logo y en el cierre sobran el logo de arriba y el pie: los dice la propia escena.
  const ini = tiempos[0];
  const anim = [];
  if (ini && ini.tipo === "logo") anim.push(`llega 450ms var(--suave) ${ini.ini + ini.dur}ms both`);
  const cierre = tiempos.find((x) => x.tipo === "cierre");
  if (cierre) anim.push(`sale 420ms var(--salida) ${cierre.ini - 420}ms ${anim.length ? "forwards" : "both"}`);
  const ocultar = anim.length ? ` style="animation: ${anim.join(", ")}"` : "";
  const ty = TIPOS[tipo] || TIPOS.actual;
  const reel = alto === 1920;
  const doc = `<!doctype html><html lang="es"><head><meta charset="utf-8"><style>
@font-face{font-family:"Instrument Serif";src:url(${f("instrument-serif.woff2")})}
@font-face{font-family:"Instrument Serif";font-style:italic;src:url(${f("instrument-serif-italic.woff2")})}
@font-face{font-family:"Inter Tight";src:url(${"file://" + path.join(RAIZ, "redes", "fuentes", "inter-tight.ttf")});font-weight:100 900}
@font-face{font-family:"Unifraktur";src:url(${f("unifraktur.woff2")})}
:root{--papel:#efe7d6;--tinta:#16130f;--tenue:#5a5145;--rojo:#a1231b;--gris:#a39c92;
  --tit:${ty.titular};--tw:${ty.peso};--sans:${ty.texto}}
*{box-sizing:border-box;margin:0}
html,body{width:1080px;height:${alto}px;overflow:hidden;background:var(--papel);color:var(--tinta);font-family:var(--sans)}
body::after{content:"";position:absolute;inset:0;pointer-events:none;opacity:.5;
  background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 .09 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}
/* Reel: todo dentro de la zona que Instagram no recorta en el feed (4:5 al
   centro, de y = 285 a 1635) ni tapa con su barra; sin logo arriba, que el
   perfil ya lo muestra. */
.cab{position:absolute;top:${reel ? 90 : 56}px;display:${reel ? "none" : "block"};left:90px;right:90px;text-align:center;font-family:Unifraktur;font-size:${reel ? 64 : 52}px;padding-bottom:18px;z-index:2}
.prog{position:absolute;top:${reel ? 190 : 140}px;left:90px;right:90px;height:6px;background:rgba(22,19,15,.12);z-index:2}
.prog i{display:block;height:100%;background:var(--rojo);transform-origin:left;animation:prog ${total}ms linear 0ms both}
.pie{position:absolute;bottom:${reel ? 330 : 60}px;left:90px;right:90px;display:flex;justify-content:space-between;font-family:var(--tit);font-style:italic;font-size:42px;color:var(--tenue);z-index:2}
.paso{position:absolute;right:0;bottom:-${reel ? 80 : 80}px;font-family:var(--tit);font-style:italic;font-size:42px;color:var(--tenue);line-height:1}
/* Marcas de corte, como en las pruebas de imprenta: enmarcan la zona segura. */
.marcas i{position:absolute;width:34px;height:34px;border:0 solid rgba(22,19,15,.45);z-index:2}
.marcas i:nth-child(1){left:48px;top:${reel ? 330 : 30}px;border-left-width:2px;border-top-width:2px}
.marcas i:nth-child(2){right:48px;top:${reel ? 330 : 30}px;border-right-width:2px;border-top-width:2px}
.marcas i:nth-child(3){left:48px;bottom:${reel ? 300 : 30}px;border-left-width:2px;border-bottom-width:2px}
.marcas i:nth-child(4){right:48px;bottom:${reel ? 300 : 30}px;border-right-width:2px;border-bottom-width:2px}
.esc{position:absolute;inset:${reel ? 430 : 200}px 90px ${reel ? 410 : 140}px;display:flex;flex-direction:column;justify-content:center}
.cam{width:100%;height:100%;display:flex;flex-direction:column;justify-content:inherit;align-items:inherit;text-align:inherit;will-change:transform}
.punto{display:inline-block;width:.2em;height:.2em;margin-left:.03em;border-radius:50%;background:var(--rojo)}
.cifra{transform-origin:left center}.logo-anim{display:inline-block;white-space:nowrap}
.foto{height:${reel ? 480 : 470}px;overflow:hidden;margin-bottom:56px;border:2px solid var(--tinta)}
.foto img{width:100%;height:100%;object-fit:cover;filter:sepia(.2) contrast(1.05);mix-blend-mode:multiply}
.rot{color:var(--rojo);font-weight:600;font-size:34px;letter-spacing:.16em;text-transform:uppercase;margin-bottom:20px}
.tit{font-family:var(--tit);font-weight:var(--tw);font-size:${reel ? 104 : 84}px;line-height:1.08;letter-spacing:-.01em}
.frase{font-family:var(--tit);font-weight:var(--tw);line-height:1.16}
.frase.corta{font-size:${reel ? 150 : 124}px;line-height:1.06}
.frase.media{font-size:${reel ? 112 : 94}px}
.frase.larga{font-size:${reel ? 96 : 80}px}
.wm{display:inline-block;overflow:hidden;vertical-align:bottom;padding:.14em .06em .2em;margin:-.14em -.06em -.2em}
.w{display:inline-block;animation:palabra 900ms var(--suave) both}
.m{background:linear-gradient(transparent 58%,rgba(161,35,27,.28) 58%) no-repeat 0 0/0% 100%;animation:marca 650ms var(--trazo) both;color:inherit}
.cifra{font-family:var(--tit);font-weight:var(--tw);color:var(--rojo);font-size:${reel ? 300 : 250}px;line-height:1}
.suf{font-size:${reel ? 96 : 80}px;display:inline-block}
.cifra-txt{font-size:${reel ? 64 : 54}px;line-height:1.25;margin-top:36px;font-weight:500}
.g-tit{text-wrap:balance;font-family:var(--tit);font-weight:var(--tw);font-size:${reel ? 76 : 64}px;line-height:1.05;margin-bottom:40px}
.cols{display:flex;gap:34px;align-items:flex-end;height:${reel ? 680 : 640}px;border-bottom:3px solid var(--tinta)}
.col{flex:1;display:flex;flex-direction:column;height:100%;justify-content:flex-end;align-items:stretch;text-align:center}
.barra-c{flex:1;display:flex;align-items:flex-end;max-height:${reel ? 540 : 520}px;position:relative}
.g-meta{position:absolute;left:0;border-top:3px dashed var(--tinta);transform-origin:left;z-index:1}
.g-meta span{position:absolute;left:0;bottom:12px;font-weight:500;font-size:${reel ? 34 : 30}px;white-space:nowrap;text-align:left}
.g-brecha{position:absolute;left:50%;border-left:4px dashed var(--rojo);transform-origin:bottom}
.g-brecha span{position:absolute;right:28px;top:50%;transform:translateY(-50%);color:var(--rojo);font-weight:500;font-size:${reel ? 36 : 32}px;line-height:1.1;white-space:nowrap;text-align:right}
.barra{width:100%;background:var(--gris);transform-origin:bottom}
.dest .barra{background:var(--rojo)}
.val{position:absolute;left:0;right:0;font-weight:600;font-size:46px;line-height:1}
.dest .val{color:var(--rojo)}
.etq{position:relative;top:0;font-size:30px;font-weight:500;line-height:1.15;margin-top:14px;height:72px;margin-bottom:-86px}
.g-fuente{margin-top:110px;font-size:28px;color:var(--tenue)}
/* Nunca una palabra sola en la última línea: titulares parejos, textos reacomodados. */
.tit,.frase,.cierre-txt,.logo-bajada,.firma-lema,.g-tit{text-wrap:balance}
.exp,.cita,.cifra-txt{text-wrap:pretty}
.esc-cierre,.esc-firma{text-align:center;align-items:center}
.firma-lema{font-family:var(--tit);font-style:italic;font-size:${reel ? 58 : 50}px;line-height:1.15;color:var(--tenue);margin-top:${reel ? 40 : 30}px;max-width:${reel ? 760 : 720}px;text-wrap:balance}
.firma-fondo{position:absolute;inset:-${reel ? 430 : 200}px -90px -${reel ? 410 : 140}px;background-size:cover;background-position:center;mix-blend-mode:multiply;opacity:.22;filter:sepia(.45) contrast(1.1) brightness(1.05);
  -webkit-mask-image:radial-gradient(ellipse 75% 65% at 50% 50%,transparent 20%,#000 75%);mask-image:radial-gradient(ellipse 75% 65% at 50% 50%,transparent 20%,#000 75%)}
.firma-marco{position:absolute;inset:-${reel ? 80 : 110}px -30px -${reel ? 80 : 80}px;border:2px solid var(--tinta);outline:1px solid var(--tinta);outline-offset:-14px}
.cierre-txt{text-wrap:balance}
.cierre-txt{font-family:var(--tit);font-weight:var(--tw);font-size:${reel ? 84 : 70}px;line-height:1.18}
.url{margin-top:${reel ? 40 : 28}px;font-family:var(--tit);font-style:italic;font-weight:400;font-size:${reel ? 132 : 112}px;line-height:1;color:var(--rojo)}
.ed{margin-top:${reel ? 30 : 20}px;font-family:var(--tit);font-style:italic;font-size:${reel ? 46 : 40}px;color:var(--tenue)}
.logo-g{margin-top:${reel ? 160 : 70}px;font-family:Unifraktur;font-size:${reel ? 120 : 96}px;text-align:center}
.logo-xl{white-space:nowrap;font-family:Unifraktur;font-size:${reel ? 150 : 128}px;text-align:center;line-height:1.1}
.logo-xl{margin-bottom:40px}
.logo-bajada{font-family:var(--tit);font-weight:var(--tw);font-size:${reel ? 72 : 62}px;line-height:1.12;text-align:center}
.comillas{color:var(--rojo);line-height:1}
.com-cursiva{font-family:var(--tit);font-style:italic;font-size:${reel ? 400 : 330}px;height:${reel ? 190 : 150}px;line-height:.9;margin-left:-.06em}
.com-latinas{font-family:var(--tit);font-size:${reel ? 84 : 70}px;position:relative;height:0;top:.06em;left:-.62em}
.com-gotica{font-family:Unifraktur;font-size:${reel ? 300 : 250}px;height:${reel ? 160 : 130}px;line-height:.85}
.cita-latinas{font-style:italic}
.cita{font-family:var(--tit);font-weight:var(--tw);font-size:${reel ? 84 : 70}px;line-height:1.2}
.autor{margin-top:36px;font-family:var(--tit);font-style:italic;font-size:${reel ? 46 : 40}px;color:var(--tenue)}
.esc-explica{justify-content:flex-start}
.vis{height:${reel ? 640 : 610}px;display:flex;align-items:center;justify-content:center;margin-bottom:${reel ? 50 : 24}px}
.exp{font-family:var(--tit);font-weight:var(--tw);font-size:${reel ? 80 : 64}px;line-height:1.2}
${V.CSS}
${A.CSS}
${M.CSS}
@keyframes entra{from{opacity:0;transform:translateY(90px)}35%{opacity:1}to{opacity:1;transform:none}}
@keyframes llega{from{opacity:0}to{opacity:1}}
@keyframes sale{from{opacity:1}to{opacity:0;transform:translateY(-70px)}}
@keyframes palabra{from{transform:translateY(115%)}to{transform:none}}
@keyframes deriva{from{transform:scale(1)}to{transform:scale(1.03)}}
@keyframes revela{from{clip-path:inset(0 0 100% 0)}to{clip-path:inset(0)}}
@keyframes escala{from{opacity:0;transform:scale(.7)}25%{opacity:1}to{opacity:1;transform:none}}
@keyframes logo{from{opacity:0;transform:scale(1.08);filter:blur(12px)}to{opacity:1;transform:none;filter:none}}
@keyframes marca{to{background-size:100% 100%}}
@keyframes sube{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:none}}
@keyframes crece{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes dibuja-x{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@keyframes kb{from{transform:scale(1.02)}to{transform:scale(1.14) translate(-2%,-1%)}}
@keyframes prog{from{transform:scaleX(0)}to{transform:scaleX(1)}}
</style></head><body>
<div class="cab"${ocultar}>Otra Lectura</div>
${"" /* Sin barra de progreso: Instagram ya muestra la suya y recorta la parte de arriba. */}
${secciones}
<div class="pie"${ocultar}><span>otralectura.co</span></div>
<div class="marcas"><i></i><i></i><i></i><i></i></div>
<script>
window.alTiempo = function(t){
  document.querySelectorAll('.cuenta').forEach(function(el){
    var ini=+el.dataset.ini, dur=+el.dataset.dur, hasta=+el.dataset.hasta, dec=+el.dataset.dec;
    var p=Math.min(1,Math.max(0,(t-ini)/dur)); p=p>=1?1:1-Math.pow(2,-10*p);
    el.textContent=(hasta*p).toLocaleString('es-CO',{minimumFractionDigits:dec,maximumFractionDigits:dec});
  });
};
</script></body></html>`;
  return { doc, total, tiempos };
}

async function fijar(page, t) {
  await page.evaluate((t) => {
    for (const a of document.getAnimations()) { a.pause(); a.currentTime = t; }
    window.alTiempo(t);
  }, t);
}

async function main() {
  const args = process.argv.slice(2);
  const ruta = args.find((a) => !a.startsWith("--"));
  if (!ruta) throw new Error("falta la ruta del guion");
  const guion = JSON.parse(fs.readFileSync(ruta, "utf8"));
  const tipo = (args.find((a) => a.startsWith("--tipo=")) || "--tipo=actual").slice(7);
  const salida = path.join(RAIZ, "redes", "salida", guion.slug);
  fs.mkdirSync(salida, { recursive: true });
  fs.writeFileSync(path.join(salida, "pie.txt"), guion.pie + "\n");

  const browser = await chromium.launch();
  try {
    // Carrusel: cada escena en su estado final, 1080 × 1350.
    {
      const { doc, tiempos } = html(guion, 1350, tipo);
      const archivo = path.join(salida, "_carrusel.html");
      fs.writeFileSync(archivo, doc);
      const page = await browser.newPage({ viewport: { width: 1080, height: 1350 } });
      await page.goto("file://" + archivo);
      await page.evaluate(() => document.fonts.ready);
      for (const [i, s] of tiempos.entries()) {
        await fijar(page, s.ini + s.dur - (i === tiempos.length - 1 ? 1 : 480));
        await page.screenshot({ path: path.join(salida, `carrusel-${i + 1}.png`) });
      }
      await page.close();
    }
    if (args.includes("--solo-carrusel")) return;

    // Reel: cuadro por cuadro, con el tiempo de las animaciones fijado a mano.
    const { doc, total } = html(guion, 1920, tipo);
    const archivo = path.join(salida, "_reel.html");
    fs.writeFileSync(archivo, doc);
    const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
    await page.goto("file://" + archivo);
    await page.evaluate(() => document.fonts.ready);
    // --cuadro=MS: solo una imagen del reel en ese instante, para revisar rápido.
    const cuadro = args.find((a) => a.startsWith("--cuadro="));
    if (cuadro) {
      const ms = +cuadro.slice(9);
      await fijar(page, ms);
      await page.screenshot({ path: path.join(salida, `cuadro-${ms}.png`) });
      console.log(`cuadro: ${path.join(salida, `cuadro-${ms}.png`)}`);
      return;
    }
    const mp4 = path.join(salida, "reel.mp4");
    const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(CAPTURA),
      "-i", "-", "-vf", `tmix=frames=${CAPTURA / FPS},fps=${FPS}`, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium",
      "-movflags", "+faststart", mp4], { stdio: ["pipe", "inherit", "inherit"] });
    const cuadros = Math.ceil((total / 1000) * CAPTURA) + CAPTURA; // un segundo final quieto
    for (let k = 0; k < cuadros; k++) {
      await fijar(page, Math.min(total - 1, (k * 1000) / CAPTURA));
      const buf = await page.screenshot({ type: "jpeg", quality: 92 });
      if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once("drain", r));
    }
    ff.stdin.end();
    await new Promise((r, j) => ff.on("close", (c) => (c === 0 ? r() : j(new Error("ffmpeg " + c)))));
    console.log(`reel: ${mp4} (${(total / 1000).toFixed(1)} s)`);
  } finally {
    await browser.close();
  }
}

main().catch((e) => { console.error(e.message); process.exit(1); });
