const panel = get('space-panel');
const pointMarkers = [...panel.querySelectorAll('.space-point')];
const linkedPoints = [...get('drawing').querySelectorAll('[data-point]'), ...pointMarkers];
const sceneSteps = [...panel.querySelectorAll('[data-space-step]')];
const planes = [...panel.querySelectorAll('[data-plane]')];
const reference = panel.querySelector('.space-status');
let selectedPoint = '';

function highlightPoint() {
  for (const node of linkedPoints) {
    const active = selectedPoint === node.dataset.point;
    node.classList.toggle('is-selected', active);
    if (node.matches('.space-point')) node.setAttribute('aria-pressed', String(active));
  }

  const projections = [...new Set(linkedPoints
    .filter(node => node.tagName.toLowerCase() === 'text' && node.dataset.point === selectedPoint &&
      !node.closest('.is-hidden'))
    .map(node => node.textContent))];
  reference.textContent = selectedPoint
    ? selectedPoint + ' 的投影 · ' + (projections.join('、') || '本步还未画出')
    : '点选字母，对照纸面图中已画出的投影。';
}

function renderSpace(position) {
  const activePlanes = new Set();
  for (const element of sceneSteps) {
    const start = Number(element.dataset.spaceStep);
    const end = Number(element.dataset.spaceUntil ?? Infinity);
    const visible = position >= start && position <= end;
    element.classList.toggle('is-hidden', !visible);
    element.classList.toggle('is-faded', visible && Boolean(element.dataset.spaceFocus) && position > start && end !== Infinity);
    if (visible && element.dataset.spaceFocus && (position === start || end === Infinity)) {
      activePlanes.add(element.dataset.spaceFocus);
    }
  }
  for (const plane of planes) {
    plane.classList.toggle('is-active', activePlanes.has(plane.dataset.plane));
  }
  if (!pointMarkers.some(node => node.dataset.point === selectedPoint && !node.closest('.is-hidden'))) {
    selectedPoint = '';
  }
  highlightPoint();
}

for (const marker of pointMarkers) {
  marker.onclick = () => {
    selectedPoint = selectedPoint === marker.dataset.point ? '' : marker.dataset.point;
    highlightPoint();
  };
  marker.onkeydown = event => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      marker.onclick();
    }
  };
}

// Orbit the existing SVG geometry, keeping paper projections and point IDs fixed.
const orbit = panel.querySelector('svg[data-orbit]');
const objects = [...orbit.querySelectorAll('[data-world]')].map(element => ({
  element,
  points: element.dataset.world.split(' ').map(point => point.split(',').map(Number)),
  offset: (element.dataset.offset || '0,0').split(',').map(Number),
}));
const fit = orbit.dataset.fit.split(' ').map(point => point.split(',').map(Number));
const defaults = orbit.dataset.orbit.split(',').map(Number);
let [azimuth, elevation] = defaults;
let drag = null;

function drawOrbit() {
  const a = azimuth * Math.PI / 180;
  const e = elevation * Math.PI / 180;
  const sa = Math.sin(a), ca = Math.cos(a), se = Math.sin(e), ce = Math.cos(e);
  const project = ([x, y, z]) => [-sa * x + ca * y, se * (ca * x + sa * y) - ce * z];
  const all = fit.map(project);
  const xs = all.map(([x]) => x), ys = all.map(([,y]) => y);
  const left = Math.min(...xs), right = Math.max(...xs);
  const top = Math.min(...ys), bottom = Math.max(...ys);
  const scale = Math.min(430 / Math.max(1, right - left), 214 / Math.max(1, bottom - top));
  for (const {element, points, offset} of objects) {
    const mapped = points.map(project).map(([x, y]) =>
      [270 + (x - (left + right) / 2) * scale, 142 + (y - (top + bottom) / 2) * scale]);
    const [[x,y]] = mapped;
    const tag = element.localName;
    const attrs = tag === 'polygon' ? {points: mapped.map(p => p.join(',')).join(' ')} :
      tag === 'line' ? {x1:x, y1:y, x2:mapped[1][0], y2:mapped[1][1]} :
      tag === 'circle' ? {cx:x, cy:y} : {
        x:Math.max(10, Math.min(435, x + offset[0])),
        y:Math.max(20, Math.min(272, y + offset[1])),
      };
    for (const [key, value] of Object.entries(attrs)) element.setAttribute(key, value);
  }
}

get('reset-space').addEventListener('click', () => {
  [azimuth, elevation] = defaults;
  drawOrbit();
});

orbit.addEventListener('pointerdown', event => {
  if (!event.isPrimary || event.button !== 0) return;
  drag = {id:event.pointerId, x:event.clientX, y:event.clientY, azimuth, elevation, moved:false};
});
orbit.addEventListener('pointermove', event => {
  if (!drag || drag.id !== event.pointerId) return;
  const dx = event.clientX - drag.x, dy = event.clientY - drag.y;
  if (!drag.moved) {
    if (Math.hypot(dx, dy) < 5) return;
    orbit.setPointerCapture(event.pointerId);
    drag.moved = true;
  }
  azimuth = drag.azimuth - dx * .42;
  elevation = Math.max(8, Math.min(83, drag.elevation + dy * .35));
  drawOrbit();
});
function endDrag(event) {
  if (drag?.id === event.pointerId) drag = null;
}
orbit.addEventListener('pointerup', endDrag);
orbit.addEventListener('pointercancel', endDrag);
orbit.addEventListener('pointerleave', event => {
  if (!drag?.moved) endDrag(event);
});
