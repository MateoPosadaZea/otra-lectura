// Piezas para redes a partir de un guion (redes/guiones/<slug>.json):
//   - reel.mp4: video vertical 1080 × 1920, animado, sin audio (la música se
//     pone en Instagram al subirlo).
//   - carrusel-N.png: una lámina 1080 × 1350 por escena, en su estado final.
//   - pie.txt: el texto del post.
//
// Uso: NODE_PATH=$(npm root -g) node scripts/redes.cjs redes/guiones/<slug>.json [--solo-carrusel]
// Sale en redes/salida/<slug>/. No forma parte del build del sitio: necesita
// Chromium (Playwright) y ffmpeg, que no existen en el build de Cloudflare.

const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");
const { chromium } = require("playwright");

const RAIZ = path.resolve(__dirname, "..");
const FPS = 30;

const TIPOS = {
  // titular, texto. Las fuentes viven en plantilla/fuentes (sin red).
  actual: { titular: "'Instrument Serif'", peso: 400, texto: "Manrope" },
};

function esc(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function numero(v, dec) {
  return v.toLocaleString("es-CO", { minimumFractionDigits: dec, maximumFractionDigits: dec });
}

// Palabras con su retraso; ==así== marca lo que se subraya.
function palabras(texto, inicio, paso) {
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
      trozo += `<span class="w" style="animation-delay:${Math.round(inicio + i * paso)}ms">${esc(w)}</span>`;
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

function contar(texto) {
  return texto.replace(/==/g, "").split(/\s+/).filter(Boolean).length;
}

function duracion(e) {
  switch (e.tipo) {
    case "portada": return 5200;
    case "frase": return Math.max(3400, 1300 + contar(e.texto) * 330);
    case "cifra": return 5000;
    case "grafico": return 6800;
    case "cierre": return 5000;
    default: return 4000;
  }
}

function escena(e, t0, d, g, ultima) {
  const sale = ultima ? "" : `, sale 450ms ease-in ${t0 + d - 450}ms forwards`;
  const base = `class="esc esc-${e.tipo}" style="animation: entra 450ms ease-out ${t0}ms both${sale}"`;
  if (e.tipo === "portada") {
    const p = palabras(e.titulo, t0 + 700, 110);
    return `<section ${base}>
      <div class="foto"><img src="${g.imagenUrl}" style="animation: kb ${d + 600}ms linear ${t0}ms both"></div>
      <div class="rot" style="animation: sube 600ms ease-out ${t0 + 300}ms both">${esc(e.rotulo)} · ${esc(g.fecha)}</div>
      <h1 class="tit">${p.html}</h1>
    </section>`;
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
      <div class="cifra"><span class="cuenta" data-hasta="${e.valor}" data-dec="${dec}" data-ini="${t0 + 300}" data-dur="1400">0</span><span class="suf" style="animation: sube 500ms ease-out ${t0 + 1500}ms both">${esc(e.sufijo || "")}</span></div>
      <p class="cifra-txt">${p.html}</p>
    </section>`;
  }
  if (e.tipo === "grafico") {
    const max = Math.max(...e.datos.map((x) => x.valor));
    const cols = e.datos.map((x, i) => {
      const t = t0 + 900 + i * 450;
      const alto = (x.valor / max) * 100;
      const dest = x.etiqueta === e.destacar ? " dest" : "";
      const dec = String(x.valor).includes(".") ? 1 : 0;
      return `<div class="col${dest}">
        <div class="val" style="animation: sube 400ms ease-out ${t + 500}ms both">${numero(x.valor, dec)}${esc(e.unidad || "")}</div>
        <div class="barra-c"><div class="barra" style="height:${alto}%;animation: crece 800ms cubic-bezier(.2,.8,.2,1) ${t}ms both"></div></div>
        <div class="etq">${esc(x.etiqueta)}</div></div>`;
    }).join("");
    return `<section ${base}>
      <h2 class="g-tit" style="animation: sube 500ms ease-out ${t0 + 200}ms both">${esc(e.titulo)}</h2>
      <div class="cols">${cols}</div>
      <div class="g-fuente" style="animation: sube 500ms ease-out ${t0 + 900}ms both">Fuente: ${esc(e.fuente || "")}</div>
    </section>`;
  }
  if (e.tipo === "cierre") {
    return `<section ${base}>
      <p class="cierre-txt" style="animation: sube 500ms ease-out ${t0 + 200}ms both">${esc(e.texto)}</p>
      <div class="url" style="animation: sube 600ms ease-out ${t0 + 800}ms both">otralectura.co</div>
      <div class="ed" style="animation: sube 500ms ease-out ${t0 + 1300}ms both">Edición ${esc(g.edicion)} · ${esc(g.fecha)}</div>
      <div class="logo-g" style="animation: sube 600ms ease-out ${t0 + 1700}ms both">Otra Lectura</div>
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
    imagenUrl: "file://" + path.join(RAIZ, guion.imagen),
  };
  const secciones = guion.escenas.map((e, i) => {
    const d = duracion(e);
    tiempos.push({ ini: t, dur: d, tipo: e.tipo });
    const s = escena(e, t, d, g, i === guion.escenas.length - 1);
    t += d;
    return s;
  }).join("\n");
  const total = t;
  const ty = TIPOS[tipo] || TIPOS.actual;
  const reel = alto === 1920;
  const doc = `<!doctype html><html lang="es"><head><meta charset="utf-8"><style>
@font-face{font-family:"Instrument Serif";src:url(${f("instrument-serif.woff2")})}
@font-face{font-family:"Manrope";src:url(${f("manrope.woff2")});font-weight:200 800}
@font-face{font-family:"Unifraktur";src:url(${f("unifraktur.woff2")})}
:root{--papel:#efe7d6;--tinta:#16130f;--tenue:#5a5145;--rojo:#a1231b;--gris:#a39c92;
  --tit:${ty.titular};--tw:${ty.peso};--sans:${ty.texto}}
*{box-sizing:border-box;margin:0}
html,body{width:1080px;height:${alto}px;overflow:hidden;background:var(--papel);color:var(--tinta);font-family:var(--sans)}
body::after{content:"";position:absolute;inset:0;pointer-events:none;opacity:.5;
  background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 .09 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}
.cab{position:absolute;top:${reel ? 90 : 56}px;left:90px;right:90px;text-align:center;font-family:Unifraktur;font-size:${reel ? 64 : 52}px;padding-bottom:18px;border-bottom:2px solid var(--tinta);z-index:2}
.prog{position:absolute;top:${reel ? 190 : 140}px;left:90px;right:90px;height:6px;background:rgba(22,19,15,.12);z-index:2}
.prog i{display:block;height:100%;background:var(--rojo);transform-origin:left;animation:prog ${total}ms linear 0ms both}
.pie{position:absolute;bottom:${reel ? 110 : 60}px;left:90px;right:90px;display:flex;justify-content:space-between;font-weight:700;font-size:30px;letter-spacing:.12em;text-transform:uppercase;color:var(--tenue);z-index:2}
.esc{position:absolute;inset:${reel ? 260 : 200}px 90px ${reel ? 220 : 140}px;display:flex;flex-direction:column;justify-content:center}
.foto{height:${reel ? 760 : 470}px;overflow:hidden;margin-bottom:56px;border:2px solid var(--tinta)}
.foto img{width:100%;height:100%;object-fit:cover;filter:sepia(.2) contrast(1.05);mix-blend-mode:multiply}
.rot{color:var(--rojo);font-weight:800;font-size:34px;letter-spacing:.16em;text-transform:uppercase;margin-bottom:20px}
.tit{font-family:var(--tit);font-weight:var(--tw);font-size:${reel ? 104 : 84}px;line-height:1.02;letter-spacing:-.01em}
.frase{font-family:var(--tit);font-weight:var(--tw);line-height:1.08}
.frase.corta{font-size:${reel ? 150 : 124}px;line-height:1}
.frase.media{font-size:${reel ? 112 : 94}px}
.frase.larga{font-size:${reel ? 96 : 80}px}
.w{display:inline-block;animation:palabra 520ms cubic-bezier(.2,.8,.2,1) both}
.m{background:linear-gradient(transparent 58%,rgba(161,35,27,.28) 58%) no-repeat 0 0/0% 100%;animation:marca 700ms ease-out both;color:inherit}
.cifra{font-family:var(--tit);font-weight:var(--tw);color:var(--rojo);font-size:${reel ? 300 : 250}px;line-height:1}
.suf{font-size:${reel ? 96 : 80}px;display:inline-block}
.cifra-txt{font-size:${reel ? 64 : 54}px;line-height:1.25;margin-top:36px;font-weight:500}
.g-tit{font-family:var(--tit);font-weight:var(--tw);font-size:${reel ? 76 : 64}px;line-height:1.05;margin-bottom:40px}
.cols{display:flex;gap:34px;align-items:flex-end;height:${reel ? 900 : 640}px;border-bottom:3px solid var(--tinta)}
.col{flex:1;display:flex;flex-direction:column;height:100%;justify-content:flex-end;align-items:stretch;text-align:center}
.barra-c{flex:1;display:flex;align-items:flex-end;max-height:${reel ? 760 : 520}px}
.barra{width:100%;background:var(--gris);transform-origin:bottom}
.dest .barra{background:var(--rojo)}
.val{font-weight:800;font-size:46px;margin-bottom:12px}
.dest .val{color:var(--rojo)}
.etq{position:relative;top:0;font-size:30px;font-weight:600;line-height:1.15;margin-top:14px;height:72px;margin-bottom:-86px}
.g-fuente{margin-top:110px;font-size:28px;color:var(--tenue)}
.cierre-txt{font-family:var(--tit);font-weight:var(--tw);font-size:${reel ? 90 : 76}px;line-height:1.08}
.url{margin-top:50px;font-weight:800;font-size:${reel ? 104 : 92}px;color:var(--rojo);letter-spacing:-.01em}
.ed{margin-top:24px;font-size:36px;color:var(--tenue);font-weight:600}
.logo-g{margin-top:${reel ? 160 : 70}px;font-family:Unifraktur;font-size:${reel ? 120 : 96}px;text-align:center}
@keyframes entra{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:none}}
@keyframes sale{from{opacity:1}to{opacity:0;transform:translateY(-24px)}}
@keyframes palabra{from{opacity:0;transform:translateY(.35em)}to{opacity:1;transform:none}}
@keyframes marca{to{background-size:100% 100%}}
@keyframes sube{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:none}}
@keyframes crece{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes kb{from{transform:scale(1.02)}to{transform:scale(1.14) translate(-2%,-1%)}}
@keyframes prog{from{transform:scaleX(0)}to{transform:scaleX(1)}}
</style></head><body>
<div class="cab">Otra Lectura</div>
${reel ? '<div class="prog"><i></i></div>' : ""}
${secciones}
<div class="pie"><span>otralectura.co</span><span>Edición ${esc(guion.edicion)}</span></div>
<script>
window.alTiempo = function(t){
  document.querySelectorAll('.cuenta').forEach(function(el){
    var ini=+el.dataset.ini, dur=+el.dataset.dur, hasta=+el.dataset.hasta, dec=+el.dataset.dec;
    var p=Math.min(1,Math.max(0,(t-ini)/dur)); p=1-Math.pow(1-p,3);
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
    const mp4 = path.join(salida, "reel.mp4");
    const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(FPS),
      "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium",
      "-movflags", "+faststart", mp4], { stdio: ["pipe", "inherit", "inherit"] });
    const cuadros = Math.ceil((total / 1000) * FPS) + FPS; // un segundo final quieto
    for (let k = 0; k < cuadros; k++) {
      await fijar(page, Math.min(total - 1, (k * 1000) / FPS));
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
