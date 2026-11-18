// Shared by the Board and the Live view: read the data, flip a factory's switch, draw a result line.
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));

async function api(path, body) {
  const res = await fetch(path, body ? {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)} : {});
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || res.statusText);
  return data;
}
const loadData = () => api("api/data");

function showError(err) {
  document.querySelectorAll(".load-error").forEach(el => el.remove());
  document.body.insertAdjacentHTML("afterbegin", `<div class="load-error" role="alert">${esc(err.message)}</div>`);
}

// Which STOP files hold a factory off, and what each one says.
const stopNote = f => f.stopped_by.map(s => `${s.file}${s.why ? ` ("${s.why}")` : ""}`).join(" and ");

const powerSwitch = f => `<button class="sw" type="button" role="switch" aria-checked="${f.on}" data-power="${esc(f.id)}" title="${f.on ? "On. Click to stop this factory." : "Off: " + esc(stopNote(f))}"><i></i><span>${f.on ? "On" : "Off"}</span></button>`;

// Every switch on the page. Off writes the factory's STOP file. On removes it, so that one asks first.
// The server refuses to remove a STOP file this UI did not write, and the refusal is shown as it is.
function onPower(factories, changed) {
  document.addEventListener("click", async ev => {
    const sw = ev.target.closest("[data-power]"); if (!sw) return;
    const f = factories().find(x => x.id === sw.dataset.power);
    if (f.on || confirm(`Turn ${f.name} on?\nIts runs will be allowed to start again.`)) {
      try { changed(await api(`api/factories/${encodeURIComponent(f.id)}/power`, {on: !f.on})); } catch (err) { showError(err); }
    }
  });
}

// The factory files change under the page: look again every 30 seconds while the page is visible.
function watch(current, changed) {
  const same = d => JSON.stringify({...d, asOf: ""});
  setInterval(async () => {
    if (document.hidden) return;
    const next = await loadData().catch(() => null);
    if (next && same(next) !== same(current())) changed(next);
  }, 30000);
}

// A running result as a small line over its zero line. Colour comes from the page: .sp.up and .sp.down.
function sparkline(v, w, h, cls = "") {
  if (!v || v.length < 2) return "";
  const mn = Math.min(0, ...v), mx = Math.max(0, ...v), pad = w < 100 ? 2 : 5;
  const sx = i => pad + i * (w - 2 * pad) / (v.length - 1), sy = y => h - pad - (y - mn) / ((mx - mn) || 1) * (h - 2 * pad);
  const d = v.map((y, i) => (i ? "L" : "M") + sx(i).toFixed(1) + " " + sy(y).toFixed(1)).join(" "), zero = sy(0).toFixed(1);
  return `<svg class="sp ${v[v.length - 1] >= 0 ? "up" : "down"} ${cls}" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true"><line class="zero" x1="0" x2="${w}" y1="${zero}" y2="${zero}"/><path class="area" d="${d} L${sx(v.length - 1)} ${zero} L${sx(0)} ${zero}Z"/><path class="line" d="${d}"/></svg>`;
}
