// 원본 모듈은 build_prototype.py가 위에 합쳐 둔다(M_g, M_kit, M_data, M_art, M_hw, M_screens, M_flow).
(function () {
  const q = new URLSearchParams(location.search);
  if (q.get('fast')) G.flags.fast = +q.get('fast');
  const $ = (id) => document.getElementById(id);
  const log = (who, text) => {
    const d = document.createElement('div'); d.textContent = (who ? who + ': ' : '') + text;
    $('log').appendChild(d); $('log').scrollTop = 1e9;
  };
  const NAMES = { kiosk: '키오스크', gp: '할아버지', staff: '알바생' };
  const noop = () => {};
  const audio = { play: noop, stop: noop };
  const ui = { say: (who, t) => { log(NAMES[who] || who || '', t); return Promise.resolve(); }, nunchi: noop, views: noop, prompt: noop };
  const nun = { v: 0, say(who, t) { log(NAMES[who] || who, t); return Promise.resolve(); }, mutter: noop, add: noop, sorry: noop, update: noop };
  const hands = { held: null, equip(v) { this.held = v; } };

  let scr = null, flow = null, finished = false;
  const sc = $('screen'), sx = sc.getContext('2d');
  const readables = { create(o) {
    return { mesh: new THREE.Mesh(), blur: o.blur, lensRadius: 0.15, mat: { uniforms: { glow: { value: 1 } } },
      redraw() { o.draw(sx, o.px, o.px * 16 / 9, false); if ($('c_mean').checked) o.draw(sx, o.px, o.px * 16 / 9, true); } };
  } };
  const ctx = { audio, ui, hands, readables };

  const K = M_flow.newK();
  const api = { redraw: () => scr && scr.redraw(), finish() { finished = true; $('done').style.display = 'block'; $('done').textContent = '주문 완료 ' + G.state.order.number; log('', '주문 완료'); sync(); }, onCall: noop };
  const hw = {
    coverOpened: false, plate: {},
    openCover() { this.coverOpened = true; sync(); },
    closeCover() { this.coverOpened = false; },
    cardHide: noop, nudge: noop, showPaperSpot: noop, update: noop,
    cardAt(slot, mode) { log('', '카드 ' + slot + ' ' + mode); },
    resetReceipt() { $('rc').style.display = 'none'; },
    printReceipt(draw) { draw($('rc').getContext('2d'), 296, 1000); $('rc').style.display = 'block'; },
    tearReceipt() { $('rc').style.display = 'none'; },
  };
  flow = M_flow.createFlow(ctx, K, hw, nun, api);
  scr = M_screens.createScreen(ctx, K, flow.A);
  api.scr = scr;
  // 안 먹는 터치 연출(눈치용)은 빼고 봇 입력으로 처리
  const touch = (px, py) => flow.touch(px, py, { bot: true });
  const spot = (id) => flow.spot(id, { bot: true });

  function sync() {
    $('state').innerHTML = '화면: ' + K.screen + '<br>덮개: ' + (hw.coverOpened ? '열림' : '닫힘') + '<br>합계: ' + M_data.won(K.total()) + (K.cardMsg ? '<br>' + K.cardMsg : '');
  }
  function reset() { finished = false; $('done').style.display = 'none'; $('log').innerHTML = ''; hands.equip(null); flow.resetAll(); K.timer = 90; sync(); }

  sc.addEventListener('click', (e) => {
    const r = sc.getBoundingClientRect(), px = (e.clientX - r.left) / r.width * 1080, py = (e.clientY - r.top) / r.height * 1920;
    const d = document.createElement('div'); d.className = 'rip'; d.style.left = (e.clientX - r.left) + 'px'; d.style.top = (e.clientY - r.top) + 'px';
    $('scr').appendChild(d); setTimeout(() => d.remove(), 500);
    touch(px, py); sync();
  });
  $('b_cover').onclick = () => { spot('cover'); sync(); };
  $('b_ic').onclick = () => { spot('ic'); sync(); };
  $('b_bar').onclick = () => { spot('barcode'); sync(); };
  $('b_rec').onclick = () => { spot('receipt'); sync(); };
  $('b_out').onclick = () => { spot('ic'); sync(); };
  $('b_tear').onclick = () => { spot('paper'); sync(); };
  $('b_call').onclick = () => { spot('call'); sync(); };
  $('b_reset').onclick = reset;
  $('c_mean').onchange = () => scr.redraw();

  let last = performance.now(), slideT = 0, lastKey = '';
  function frame(now) {
    const dt = Math.min(0.1, (now - last) / 1000); last = now;
    G.dt = dt; G.time += dt;
    M_g.tickWaits();
    flow.update(dt);
    if (K.screen === 'idle') { slideT += dt; if (slideT > 3.6) { slideT = 0; K.slide++; scr.redraw(); } }
    if ($('c_time').checked && flow.timed()) { K.timer -= dt; if (K.timer <= 0) { flow.timedOut(); sync(); } }
    const key = K.screen + K.cart.length + hw.coverOpened + K.cardMsg;
    if (key !== lastKey) { lastKey = key; sync(); }
    requestAnimationFrame(frame);
  }
  window.KIOSK = { K, flow, hw, scr, art: M_art, data: M_data, spot, touch, isDone: () => finished,
    buttons: () => scr.buttons.map((b) => b.id),
    press: (id) => { const b = scr.find(id); if (!b) return false; return touch(b.x + b.w / 2, b.y + b.h / 2); } };
  reset(); scr.redraw();
  requestAnimationFrame(frame);
})();
