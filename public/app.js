const form = document.getElementById('controls');
const score = document.getElementById('score');
const grade = document.getElementById('grade');
const statusText = document.getElementById('status');
form.addEventListener('input', () => {
  score.textContent = '—';
  grade.textContent = '—';
  delete grade.dataset.grade;
  document.getElementById('pointer').hidden = true;
  statusText.textContent = 'Run prediction for these readings.';
});
form.addEventListener('submit', event => {
  event.preventDefault();
  if (!form.reportValidity()) return;
  const channels = Array.from(form.querySelectorAll('[data-channel]'), field => field.valueAsNumber);
  const averageCount = channels.reduce((sum, count) => sum + count, 0) / channels.length;
  const intensity = averageCount * 100 / 65535;
  const value = Number((10.4 + 2.2*(intensity-50)/20).toFixed(2));
  const cutoffs = [[15,'A'],[12,'B'],[9,'C'],[6,'D']];
  const label = cutoffs.find(([min]) => value >= min)?.[1] ?? 'Below D';
  score.textContent = value.toFixed(2);
  grade.textContent = label;
  grade.dataset.grade = label;
  const pointer = document.getElementById('pointer');
  pointer.style.left = Math.min(100, Math.max(0, value * 5)) + '%';
  pointer.hidden = false;
  statusText.textContent = 'Prediction complete · Grade ' + label;
});
