async function request(url, payload, output) {
  output.className = 'result'; output.textContent = 'Loading…';
  try {
    const response = await fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);
    output.textContent = JSON.stringify(data, null, 2);
  } catch (error) { output.className = 'result error'; output.textContent = error.message; }
}
document.querySelector('#load').addEventListener('click', () => request('/api/figma/file', {file:document.querySelector('#file').value}, document.querySelector('#fileResult')));
document.querySelector('#inspect').addEventListener('click', () => request('/api/figma/nodes', {file:document.querySelector('#file').value, node_ids:document.querySelector('#nodes').value.split(',').map(s=>s.trim()).filter(Boolean)}, document.querySelector('#nodeResult')));
