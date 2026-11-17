// Apertura en montaje para scripts/redes.cjs, a la manera de los cortes
// rápidos de archivo: una sola frase se arma palabra por palabra en un rótulo
// pequeño mientras detrás cambia el dibujo con cada palabra. Luego un
// silencio (papel en blanco y el punto rojo latiendo) y el giro, con la
// pantalla llenándose de rojo. Los dibujos son objetos de la casa a tinta.

function esc(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
const ms = (x) => Math.round(x);

// Objetos en una caja de 400 × 400: trazos (se dibujan) y aguada (se posa).
const OBJETOS = {
  llaves: {
    trazo: "M150 80 A50 50 0 1 0 150.1 80 M196 168 A40 40 0 1 0 196.1 168 M226 236 L330 340 M300 310 L322 288 M318 328 L340 306 M180 150 L198 168",
    aguada: "M196 168 A40 40 0 1 0 196.1 168 Z",
  },
  gafas: {
    trazo: "M130 160 A60 60 0 1 0 130.1 160 M270 160 A60 60 0 1 0 270.1 160 M190 215 Q200 198 210 215 M70 215 L36 186 M330 215 L364 186",
    aguada: "M130 160 A60 60 0 1 0 130.1 160 Z M270 160 A60 60 0 1 0 270.1 160 Z",
  },
  taza: {
    trazo: "M110 170 H290 V250 Q290 320 225 320 H175 Q110 320 110 250 Z M290 195 Q352 195 352 238 Q352 280 290 280 M90 336 H310 M165 145 Q150 120 168 100 Q186 80 170 58 M215 145 Q200 120 218 100 Q236 80 220 58",
    aguada: "M110 170 H290 V250 Q290 320 225 320 H175 Q110 320 110 250 Z",
  },
  calendario: {
    trazo: "M96 110 H304 V326 H96 Z M96 160 H304 M150 86 V132 M250 86 V132 M128 196 H156 M186 196 H214 M244 196 H272 M128 240 H156 M186 240 H214 M244 240 H272 M128 284 H156 M186 284 H214",
    aguada: "M96 110 H304 V160 H96 Z",
  },
  reloj: {
    trazo: "M200 80 A125 125 0 1 0 200.1 80 M200 205 V128 M200 205 L262 238 M200 96 V112 M309 205 H293 M200 314 V298 M91 205 H107",
    aguada: "M200 80 A125 125 0 1 0 200.1 80 Z",
  },
  retrato: {
    trazo: "M112 80 H288 V336 H112 Z M136 104 H264 V312 H136 Z M200 150 A34 34 0 1 0 200.1 150 M150 300 Q154 236 200 232 Q246 236 250 300",
    aguada: "M136 104 H264 V312 H136 Z",
  },
  libro: {
    trazo: "M200 140 Q140 108 70 128 V300 Q140 282 200 312 Q260 282 330 300 V128 Q260 108 200 140 Z M200 140 V312 M96 160 Q140 150 178 166 M96 196 Q140 186 178 202 M222 166 Q260 150 304 160 M222 202 Q260 186 304 196",
    aguada: "M200 140 Q140 108 70 128 V300 Q140 282 200 312 Z",
  },
};

// Escena «montaje»: { texto, objetos: [nombres], paso }.
function montaje(e, t0) {
  const palabras = e.texto.trim().split(/\s+/);
  const paso = e.paso || 560;
  const objs = e.objetos && e.objetos.length ? e.objetos : Object.keys(OBJETOS);
  let cuadros = "", rotulo = "";
  palabras.forEach((w, i) => {
    const ini = t0 + 250 + i * paso, fin = ini + paso;
    const o = OBJETOS[objs[i % objs.length]];
    if (!o) throw new Error(`objeto desconocido: ${objs[i % objs.length]}`);
    const ultimo = i === palabras.length - 1;
    const vis = `animation: corte-on 1ms linear ${ms(ini)}ms both${ultimo ? "" : `, corte-off 1ms linear ${ms(fin)}ms forwards`}`;
    cuadros += `<g style="${vis}"><g style="animation: golpe ${ms(paso + 400)}ms var(--suave) ${ms(ini)}ms both">
      <path class="mt-aguada" d="${o.aguada}"/>
      <path class="mt-trazo" pathLength="1" d="${o.trazo}" style="animation: dibuja ${ms(Math.min(420, paso * 0.8))}ms var(--trazo) ${ms(ini)}ms both"/>
    </g></g>`;
    rotulo += `<span class="mt-w" style="animation: mt-abre 260ms var(--suave) ${ms(ini)}ms both">${esc(w)}&nbsp;</span>`;
  });
  return `<div class="mt-fig"><svg viewBox="0 0 400 400" class="mt-svg">${cuadros}</svg></div>
    <div class="mt-rotulo"><span class="mt-pildora">${rotulo}</span></div>`;
}

function duracionMontaje(e) {
  const n = e.texto.trim().split(/\s+/).length;
  return 250 + n * (e.paso || 560) + 1300;
}

const CSS = `
.esc-montaje{justify-content:space-between;align-items:center}
.mt-fig{flex:1;width:100%;display:flex;align-items:center;justify-content:center}
.mt-svg{width:760px;height:760px;overflow:visible}
.mt-svg *{transform-box:fill-box;transform-origin:center}
.mt-trazo{fill:none;stroke:var(--tinta);stroke-width:5.5;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1}
.mt-aguada{fill:rgba(22,19,15,.1)}
.mt-rotulo{width:100%;display:flex;justify-content:center;margin-bottom:10px}
.mt-pildora{display:inline-flex;flex-wrap:nowrap;font-family:var(--sans);font-weight:500;font-size:42px;line-height:1;padding:22px 30px 22px 34px;border:2px solid rgba(22,19,15,.22);border-radius:60px;background:rgba(239,231,214,.92);white-space:nowrap}
.mt-w{display:inline-block;overflow:hidden;white-space:nowrap;max-width:0}
.esc-pausa{align-items:center;justify-content:center}
.pausa-punto{width:40px;height:40px;border-radius:50%;background:var(--rojo)}
.esc-giro{justify-content:center}
.giro-fondo{position:absolute;inset:-430px -90px -410px;background:var(--rojo);z-index:-1}
.esc-giro .frase{color:var(--papel);position:relative}
.esc-giro .punto{background:var(--papel)}
.esc-giro .m{background:none}
@keyframes corte-on{from{opacity:0}to{opacity:1}}
@keyframes corte-off{from{opacity:1}to{opacity:0}}
@keyframes golpe{from{transform:scale(1.07)}to{transform:none}}
@keyframes mt-abre{from{max-width:0;opacity:0}to{max-width:420px;opacity:1}}
@keyframes late{0%,49%{opacity:1}50%,100%{opacity:0}}
@keyframes llena{from{clip-path:circle(0% at 50% 50%)}to{clip-path:circle(75% at 50% 50%)}}
`;

module.exports = { montaje, duracionMontaje, CSS, OBJETOS };
