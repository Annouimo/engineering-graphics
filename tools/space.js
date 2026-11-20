const panel = get('space-panel');
const pointMarkers = [...panel.querySelectorAll('.space-point')];
const linkedPoints = [...get('drawing').querySelectorAll('[data-point]'), ...pointMarkers];
const sceneSteps = [...panel.querySelectorAll('[data-space-step]')];
const cameras = [...panel.querySelectorAll('[data-camera]')];
const sceneViews = [...panel.querySelectorAll('[data-space-view]')];
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
  for (const element of sceneSteps) {
    element.classList.toggle('is-hidden', Number(element.dataset.spaceStep) > position);
  }
  if (!pointMarkers.some(node => node.dataset.point === selectedPoint && !node.closest('.is-hidden'))) {
    selectedPoint = '';
  }
  highlightPoint();
}

for (const button of cameras) {
  button.onclick = () => {
    const camera = button.dataset.camera;
    for (const view of sceneViews) view.hidden = view.dataset.spaceView !== camera;
    for (const control of cameras) control.setAttribute('aria-pressed', String(control === button));
  };
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
