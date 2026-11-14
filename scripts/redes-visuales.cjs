// Ilustraciones animadas para las escenas «explica» de scripts/redes.cjs.
// Misma línea gráfica del sitio: trazo de tinta sobre papel, acentos en rojo.
// Cada función recibe la escena (e.visual) y el instante de inicio t (ms) y
// devuelve un <svg>. Los trazos se «dibujan» con la clase .tr (pathLength=1);
// lo que aparece entero usa .pop; lo que viaja, .viaja con --dx/--dy.

function esc(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

const dib = (t, dur = 900) => `style="animation: dibuja ${dur}ms ease-out ${Math.round(t)}ms both"`;
const pop = (t, dur = 450) => `style="animation: pop ${dur}ms cubic-bezier(.2,1.4,.4,1) ${Math.round(t)}ms both"`;
const sube = (t, dur = 500) => `style="animation: sube ${dur}ms ease-out ${Math.round(t)}ms both"`;

function svg(vb, cuerpo) {
  return `<svg class="ilus" viewBox="${vb}" preserveAspectRatio="xMidYMid meet">${cuerpo}</svg>`;
}

// 100 puntos; los primeros n en rojo.
function cuadricula(v, t) {
  const n = v.n, total = v.de || 100;
  let s = "";
  for (let i = 0; i < total; i++) {
    const x = 60 + (i % 10) * 64, y = 60 + Math.floor(i / 10) * 64;
    s += `<circle cx="${x}" cy="${y}" r="24" class="pt-gris" ${pop(t + i * 6, 300)}/>`;
  }
  for (let i = 0; i < n; i++) {
    const x = 60 + (i % 10) * 64, y = 60 + Math.floor(i / 10) * 64;
    s += `<circle cx="${x}" cy="${y}" r="24" class="pt-rojo" ${pop(t + 900 + i * 14, 300)}/>`;
  }
  return svg("0 0 700 700", s);
}

// Línea de tiempo horizontal con hitos.
function tiempo(v, t) {
  const hs = v.hitos, ancho = 900, x0 = 60, x1 = 840;
  let s = `<path pathLength="1" class="tr" d="M${x0} 300 H${x1}" ${dib(t, 1400)}/>`;
  s += `<path pathLength="1" class="tr" d="M${x1 - 30} 280 L${x1 + 4} 300 L${x1 - 30} 320" ${dib(t + 1300, 300)}/>`;
  hs.forEach((h, i) => {
    const x = x0 + ((x1 - x0 - 60) * i) / (hs.length - 1);
    const ti = t + 300 + i * 420;
    const rojo = i > 0;
    s += `<circle cx="${x}" cy="300" r="${rojo ? 22 : 16}" class="${rojo ? "pt-rojo" : "pt-tinta"}" ${pop(ti)}/>`;
    s += `<text x="${x}" y="${i % 2 ? 390 : 240}" class="tx-num" text-anchor="middle" ${sube(ti + 150)}>${esc(h.etq)}</text>`;
    if (h.sub) s += `<text x="${x}" y="${i % 2 ? 432 : 198}" class="tx-peq" text-anchor="middle" ${sube(ti + 250)}>${esc(h.sub)}</text>`;
  });
  return svg(`0 0 ${ancho} 600`, s);
}

const ICONOS = {
  sol: `<circle cx="50" cy="50" r="18"/><path d="M50 12v12M50 76v12M12 50h12M76 50h12M23 23l8 8M69 69l8 8M77 23l-8 8M31 69l-8 8"/>`,
  rayo: `<path d="M56 8 L26 56 H48 L42 92 L74 40 H52 Z"/>`,
  corazon: `<path d="M50 84 C18 62 10 44 18 30 C26 16 44 18 50 32 C56 18 74 16 82 30 C90 44 82 62 50 84 Z"/><path d="M30 50 H42 L47 40 L54 60 L59 50 H70"/>`,
  chip: `<rect x="28" y="28" width="44" height="44" rx="4"/><rect x="40" y="40" width="20" height="20"/><path d="M38 28V16M50 28V16M62 28V16M38 84V72M50 84V72M62 84V72M28 38H16M28 50H16M28 62H16M84 38H72M84 50H72M84 62H72"/>`,
  planta: `<path d="M50 90 V40"/><path d="M50 60 C34 60 24 50 22 34 C38 34 48 44 50 60 Z"/><path d="M50 48 C66 48 76 38 78 22 C62 22 52 32 50 48 Z"/><path d="M30 90 H70"/>`,
  ciudad: `<path d="M14 88 H86"/><rect x="18" y="44" width="20" height="44"/><rect x="42" y="20" width="22" height="68"/><rect x="68" y="54" width="16" height="34"/><path d="M48 32h10M48 44h10M48 56h10M24 56h8M24 68h8"/>`,
  gota: `<path d="M50 12 C66 36 76 50 76 64 A26 26 0 0 1 24 64 C24 50 34 36 50 12 Z"/>`,
  personas: `<circle cx="36" cy="34" r="12"/><circle cx="66" cy="38" r="10"/><path d="M14 86 C14 64 24 54 36 54 C48 54 58 64 58 86"/><path d="M52 62 C56 58 60 56 66 56 C78 56 86 66 86 86"/>`,
};

function iconos(v, t) {
  const n = v.lista.length, cols = Math.min(3, n), filas = Math.ceil(n / cols);
  let s = "";
  v.lista.forEach((nom, i) => {
    const c = i % cols, f = Math.floor(i / cols);
    const x = 40 + c * 300, y = 30 + f * 300;
    const ti = t + i * 380;
    const trazos = ICONOS[nom].replace(/<(path|circle|rect)\b/g, `<$1 pathLength="1" class="tr ic" ${dib(ti, 1000)}`);
    s += `<g transform="translate(${x + 40} ${y}) scale(1.8)">${trazos}</g>`;
    if (v.etiquetas && v.etiquetas[i]) s += `<text x="${x + 130}" y="${y + 228}" class="tx-etq" text-anchor="middle" ${sube(ti + 500)}>${esc(v.etiquetas[i])}</text>`;
  });
  return svg(`0 0 ${cols * 300 + 40} ${filas * 300}`, s);
}

// Muchas noticias; una se queda.
function titulares(v, t) {
  let s = "";
  const anchos = [560, 640, 480, 600, 520, 660, 440];
  anchos.forEach((w, i) => {
    const y = 60 + i * 80;
    const elegida = i === 3;
    s += `<rect x="${(800 - w) / 2}" y="${y}" width="${w}" height="40" rx="6" class="${elegida ? "bl-tinta" : "bl-gris"}" ${pop(t + i * 120, 350)}/>`;
  });
  s += `<rect pathLength="1" x="60" y="282" width="680" height="76" rx="10" class="tr tr-rojo" ${dib(t + 1500, 800)}/>`;
  s += `<text x="400" y="640" class="tx-rojo" text-anchor="middle" ${sube(t + 2100)}>${esc(v.etiqueta || "")}</text>`;
  return svg("0 0 800 680", s);
}

// Una página con cifras numeradas y sus fuentes.
function documento(v, t) {
  let s = `<path pathLength="1" class="tr" d="M180 40 H560 L640 120 V680 H180 Z" ${dib(t, 1000)}/>`;
  s += `<path pathLength="1" class="tr" d="M560 40 V120 H640" ${dib(t + 700, 400)}/>`;
  [0, 1, 2, 3, 4].forEach((i) => {
    const y = 170 + i * 62;
    s += `<rect x="230" y="${y}" width="${[330, 300, 340, 260, 310][i]}" height="18" rx="5" class="bl-gris" ${pop(t + 900 + i * 120, 300)}/>`;
  });
  [[565, 168, "1"], [535, 230, "2"], [575, 292, "3"]].forEach(([x, y, n], i) => {
    s += `<text x="${x}" y="${y + 14}" class="tx-sup" ${pop(t + 1700 + i * 250)}>${n}</text>`;
  });
  s += `<text x="230" y="520" class="tx-rojo-peq" ${sube(t + 2500)}>FUENTES</text>`;
  [0, 1, 2].forEach((i) => {
    s += `<rect x="230" y="${545 + i * 36}" width="${[300, 260, 280][i]}" height="12" rx="4" class="bl-gris" ${pop(t + 2700 + i * 120, 300)}/>`;
  });
  if (v.sello) s += `<g ${pop(t + 3300, 500)}><rect x="420" y="390" width="300" height="64" rx="32" class="sello"/><text x="570" y="432" class="tx-sello" text-anchor="middle">${esc(v.sello)}</text></g>`;
  return svg("0 0 800 720", s);
}

function conversar(v, t) {
  let s = `<path pathLength="1" class="tr" d="M90 120 H460 Q490 120 490 150 V330 Q490 360 460 360 H220 L150 430 L165 360 H90 Q60 360 60 330 V150 Q60 120 90 120 Z" ${dib(t, 1200)}/>`;
  s += `<path pathLength="1" class="tr tr-rojo" d="M360 400 H710 Q740 400 740 430 V590 Q740 620 710 620 H650 L670 690 L590 620 H360 Q330 620 330 590 V430 Q330 400 360 400 Z" ${dib(t + 900, 1200)}/>`;
  s += `<text x="275" y="275" class="tx-grande" text-anchor="middle" ${pop(t + 1300)}>?</text>`;
  s += `<text x="535" y="540" class="tx-grande tx-rojo-g" text-anchor="middle" ${pop(t + 2200)}>…</text>`;
  return svg("0 0 800 720", s);
}

// La planta con raíces; nodulos rojos opcionales y bacterias que llegan.
function planta(x, alto, conNodulos, t, rotulo, tam = 1) {
  const suelo = 420;
  let s = `<path pathLength="1" class="tr" d="M${x} ${suelo} V${suelo - alto}" ${dib(t, 700)}/>`;
  const hojas = tam > 1
    ? [[-1, 0.35], [1, 0.5], [-1, 0.65], [1, 0.8]]
    : [[-1, 0.45], [1, 0.7]];
  hojas.forEach(([lado, p], i) => {
    const y = suelo - alto * p, lx = x + lado * 90 * tam;
    s += `<path pathLength="1" class="tr" d="M${x} ${y + 20} Q${x + lado * 40 * tam} ${y - 40} ${lx} ${y - 30}" ${dib(t + 400 + i * 150, 600)}/>`;
  });
  const raices = [[-60, 90], [-25, 120], [10, 130], [45, 110], [75, 80]];
  raices.forEach(([dx, dy], i) => {
    s += `<path pathLength="1" class="tr tr-fino" d="M${x} ${suelo} Q${x + dx * 0.4} ${suelo + dy * 0.6} ${x + dx * tam} ${suelo + dy * tam}" ${dib(t + 800 + i * 90, 600)}/>`;
    if (conNodulos) s += `<circle cx="${x + dx * 0.7 * tam}" cy="${suelo + dy * 0.75 * tam}" r="11" class="pt-rojo" ${pop(t + 1700 + i * 140)}/>`;
  });
  if (rotulo) s += `<text x="${x}" y="${suelo + 200}" class="tx-etq" text-anchor="middle" ${sube(t + 600)}>${esc(rotulo)}</text>`;
  return s;
}

function suelo(t) {
  return `<path pathLength="1" class="tr" d="M30 420 H770" ${dib(t, 900)}/>`;
}

function soyaMaiz(v, t) {
  let s = suelo(t);
  s += planta(230, 180, true, t + 300, "Soya");
  s += planta(560, 300, false, t + 900, "Maíz", 1.3);
  s += `<text x="640" y="560" class="tx-grande tx-gris" ${pop(t + 3000)}>?</text>`;
  return svg("0 0 800 650", s);
}

function maizBacterias(v, t) {
  let s = suelo(t);
  s += planta(400, 300, false, t + 200, "", 1.3);
  const destinos = [[-55, 88], [-23, 117], [9, 127], [41, 107], [68, 78], [-40, 60], [30, 70], [0, 100]];
  destinos.forEach(([dx, dy], i) => {
    const ox = (i % 2 ? 1 : -1) * (250 + i * 20), oy = -220 + (i % 3) * 60;
    s += `<g style="--dx:${ox}px;--dy:${oy}px;animation: viaja 1400ms cubic-bezier(.3,.6,.3,1) ${t + 1600 + i * 160}ms both">
      <ellipse cx="${400 + dx * 1.3}" cy="${420 + dy * 1.3}" rx="16" ry="9" class="pt-rojo" style="transform:rotate(${i * 37}deg)"/></g>`;
  });
  s += `<text x="400" y="110" class="tx-etq" text-anchor="middle" ${sube(t + 3200)}>${esc(v.etiqueta || "")}</text>`;
  return svg("0 0 800 650", s);
}

function bolsa(v, t) {
  let s = `<path pathLength="1" class="tr" d="M250 120 Q400 80 550 120 L590 620 Q400 660 210 620 Z" ${dib(t, 1200)}/>`;
  s += `<path pathLength="1" class="tr" d="M260 150 Q400 115 540 150" ${dib(t + 800, 500)}/>`;
  (v.etiqueta || "Fertilizante").split(" ").forEach((w, i) => {
    s += `<text x="400" y="${240 + i * 50}" class="tx-etq" text-anchor="middle" ${sube(t + 900 + i * 120)}>${esc(w)}</text>`;
  });
  s += `<clipPath id="cb"><path d="M250 120 Q400 80 550 120 L590 620 Q400 660 210 620 Z"/></clipPath>`;
  s += `<g clip-path="url(#cb)"><rect x="180" y="375" width="440" height="300" class="relleno-rojo" style="transform-origin:bottom;animation: crece 1200ms cubic-bezier(.2,.8,.2,1) ${t + 1600}ms both"/></g>`;
  s += `<path pathLength="1" class="tr tr-punteado" d="M200 375 H600" ${dib(t + 1500, 700)}/>`;
  s += `<text x="620" y="385" class="tx-rojo-peq" ${sube(t + 2600)}>${esc(v.marca || "")}</text>`;
  return svg("0 0 800 700", s);
}

// Un precio que salta.
function salto(v, t) {
  let s = `<path pathLength="1" class="tr tr-fino" d="M80 560 H740 M80 560 V80" ${dib(t, 800)}/>`;
  s += `<path pathLength="1" class="tr tr-rojo tr-grueso" d="M90 430 L250 420 L360 435 L430 425 L470 230 L560 215 L700 220" ${dib(t + 700, 1800)}/>`;
  s += `<circle cx="470" cy="230" r="14" class="pt-rojo" ${pop(t + 1900)}/>`;
  s += `<text x="490" y="170" class="tx-num tx-rojo-g" ${pop(t + 2100)}>${esc(v.etiqueta || "")}</text>`;
  if (v.cuando) s += `<text x="470" y="610" class="tx-peq" text-anchor="middle" ${sube(t + 2300)}>${esc(v.cuando)}</text>`;
  return svg("0 0 800 660", s);
}

// Un barco que cruza de un punto a otro.
function ruta(v, t) {
  let s = `<path pathLength="1" class="tr tr-punteado" d="M700 320 Q400 120 100 320" ${dib(t, 1400)}/>`;
  s += `<circle cx="700" cy="320" r="16" class="pt-tinta" ${pop(t)}/><circle cx="100" cy="320" r="16" class="pt-rojo" ${pop(t + 1300)}/>`;
  s += `<text x="700" y="390" class="tx-etq" text-anchor="middle" ${sube(t + 200)}>${esc(v.desde)}</text>`;
  s += `<text x="100" y="390" class="tx-etq" text-anchor="middle" ${sube(t + 1400)}>${esc(v.hasta)}</text>`;
  s += `<g style="offset-path: path('M700 300 Q400 100 100 300');offset-rotate:0deg;animation: navega 2400ms ease-in-out ${t + 400}ms both">
    <path class="barco" d="M-40 0 H40 L28 22 H-28 Z M0 0 V-46 L28 -12 H0"/></g>`;
  return svg("0 0 800 460", s);
}

const VISUALES = { cuadricula, tiempo, iconos, titulares, documento, conversar, "soya-maiz": soyaMaiz, "maiz-bacterias": maizBacterias, bolsa, salto, ruta };

function visual(v, t) {
  const f = VISUALES[v.tipo];
  if (!f) throw new Error(`visual desconocido: ${v.tipo}`);
  return f(v, t);
}

const CSS = `
.ilus{width:100%;height:100%;overflow:visible}
.ilus *{transform-box:fill-box;transform-origin:center}
.tr{fill:none;stroke:var(--tinta);stroke-width:5;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1}
.tr-fino{stroke-width:3.5}.tr-grueso{stroke-width:8}
.tr-rojo{stroke:var(--rojo)}
.tr-punteado{stroke-dasharray:.012 .012;stroke-dashoffset:0;animation-name:aparece!important}
.ic{stroke-width:3}
.pt-gris{fill:none;stroke:rgba(22,19,15,.28);stroke-width:3}
.pt-rojo{fill:var(--rojo)}.pt-tinta{fill:var(--tinta)}
.bl-gris{fill:rgba(22,19,15,.16)}.bl-tinta{fill:var(--tinta)}
.relleno-rojo{fill:rgba(161,35,27,.85)}
.sello{fill:none;stroke:var(--rojo);stroke-width:4}
.barco{fill:var(--papel);stroke:var(--tinta);stroke-width:4;stroke-linejoin:round}
.ilus text{font-family:var(--sans);fill:var(--tinta)}
.tx-num{font-size:52px;font-weight:800}.tx-peq{font-size:30px;fill:var(--tenue)!important;font-weight:600}
.tx-etq{font-size:40px;font-weight:700}
.tx-rojo{font-size:44px;font-weight:800;fill:var(--rojo)!important;letter-spacing:.06em;text-transform:uppercase}
.tx-rojo-peq{font-size:30px;font-weight:800;fill:var(--rojo)!important;letter-spacing:.12em}
.tx-sup{font-size:34px;font-weight:800;fill:var(--rojo)!important}
.tx-sello{font-size:30px;font-weight:800;fill:var(--rojo)!important;letter-spacing:.08em;text-transform:uppercase}
.tx-grande{font-family:var(--tit)!important;font-size:150px}.tx-rojo-g{fill:var(--rojo)!important}.tx-gris{fill:rgba(22,19,15,.35)!important}
@keyframes dibuja{to{stroke-dashoffset:0}}
@keyframes pop{from{opacity:0;transform:scale(.3)}to{opacity:1;transform:none}}
@keyframes aparece{from{opacity:0}to{opacity:1}}
@keyframes viaja{from{transform:translate(var(--dx),var(--dy));opacity:0}25%{opacity:1}to{transform:none;opacity:1}}
@keyframes navega{from{offset-distance:0%}to{offset-distance:100%}}
`;

module.exports = { visual, CSS, ICONOS };
