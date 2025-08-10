async function post(url, data){
  const r = await fetch(url, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(data)});
  if(!r.ok) throw new Error(await r.text());
  return r.json();
}

function ChartWheel(planets, houses){
  const size = 320, r = 150, cx = size/2, cy = size/2;
  const toXY = deg => {
    const rad = (deg-90) * Math.PI/180;
    return { x: cx + r*Math.cos(rad), y: cy + r*Math.sin(rad) };
  };
  const svgNS = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(svgNS, "svg");
  svg.setAttribute("width", size); svg.setAttribute("height", size);
  const circle = document.createElementNS(svgNS, "circle");
  circle.setAttribute("cx", cx); circle.setAttribute("cy", cy); circle.setAttribute("r", r); circle.setAttribute("fill", "white"); circle.setAttribute("stroke", "#ddd");
  svg.appendChild(circle);
  const h1 = houses["H1"] || 0;
  for(let i=0;i<12;i++){
    const angle = h1 + i*30;
    const rad = (angle-90)*Math.PI/180;
    const x2 = cx + r*Math.cos(rad);
    const y2 = cy + r*Math.sin(rad);
    const line = document.createElementNS(svgNS, "line");
    line.setAttribute("x1", cx); line.setAttribute("y1", cy); line.setAttribute("x2", x2); line.setAttribute("y2", y2); line.setAttribute("stroke", "#eee");
    svg.appendChild(line);
  }
  Object.keys(planets).forEach(k=>{
    const deg = planets[k].lon;
    const p = toXY(deg);
    const dot = document.createElementNS(svgNS, "circle");
    dot.setAttribute("cx", p.x); dot.setAttribute("cy", p.y); dot.setAttribute("r", 6);
    svg.appendChild(dot);
    const label = document.createElementNS(svgNS, "text");
    label.setAttribute("x", p.x+8); label.setAttribute("y", p.y+4); label.setAttribute("font-size", "10");
    label.textContent = k[0];
    svg.appendChild(label);
  });
  return svg;
}

async function computeTransits(chart, tz){
  const natal = {};
  Object.keys(chart.planets).forEach(k => { natal[k] = chart.planets[k].lon; });
  const today = new Date();
  const yyyy = today.getFullYear(), mm = String(today.getMonth()+1).padStart(2,"0"), dd = String(today.getDate()).padStart(2,"0");
  const params = new URLSearchParams({
    date: `${yyyy}-${mm}-${dd}`,
    days: "7",
    tz: tz || "UTC",
    natal_json: JSON.stringify(natal)
  });
  const r = await fetch(`/api/transits?${params.toString()}`);
  if(!r.ok) throw new Error(await r.text());
  return r.json();
}

function renderTransits(data){
  const wrap = document.getElementById("transits");
  wrap.innerHTML = "";
  if(!data.events || !data.events.length){ wrap.textContent = "No major hits in the next 7 days (tight orbs)."; return; }
  const byDate = {};
  data.events.forEach(e => { (byDate[e.date] = byDate[e.date] || []).push(e); });
  Object.keys(byDate).sort().forEach(date => {
    const c = document.createElement("div"); c.className = "card";
    const h = document.createElement("h4"); h.textContent = date; c.appendChild(h);
    const ul = document.createElement("ul");
    byDate[date].forEach(ev => {
      const li = document.createElement("li");
      li.textContent = `${ev.transit} ${ev.aspect} natal ${ev.natal} (orb ${ev.orb}°)`;
      ul.appendChild(li);
    });
    c.appendChild(ul);
    wrap.appendChild(c);
  });
}

document.getElementById("notify").addEventListener("click", async ()=>{
  if (!("Notification" in window)){ alert("Notifications not supported in this browser."); return; }
  const perm = await Notification.requestPermission();
  if (perm !== "granted"){ alert("Notifications disabled."); return; }
  setInterval(()=>{
    const items = document.querySelectorAll("#transits li");
    const today = new Date().toISOString().slice(0,10);
    items.forEach(li => {
      if(li.parentElement.previousSibling.textContent === today && li.textContent.includes("(orb 0.") ){
        new Notification("Transit exact-ish today", { body: li.textContent });
      }
    });
  }, 60*60*1000);
});

document.getElementById("go").addEventListener("click", async ()=>{
  const payload = {
    name: document.getElementById("name").value || "You",
    date: document.getElementById("date").value,
    time: document.getElementById("time").value || null,
    time_precision: document.getElementById("prec").value,
    place: document.getElementById("place").value || "Unknown",
    lat: parseFloat(document.getElementById("lat").value),
    lng: parseFloat(document.getElementById("lng").value),
    tz: document.getElementById("tz").value || "UTC"
  };
  const out = document.getElementById("out");
  out.innerHTML = "<div class='card'>Calculating…</div>";
  try{
    // Prefer Swiss engine; fallback to mock with friendly note
    let chart;
    try {
      chart = await post("/api/charts/swiss", payload);
      document.getElementById("swissNote").style.display="none";
    } catch(e){
      chart = await post("/api/charts", payload);
      const note = document.getElementById("swissNote");
      note.style.display="block"; note.className="card note";
      note.innerHTML = "<strong>Heads up:</strong> Using fast demo engine for now. When Swiss Ephemeris files are added on the server, you'll see astrologer‑grade precision automatically.";
    }
    const reading = await post("/api/readings", { chart });
    const card = document.createElement("div");
    card.className = "card";
    const h2 = document.createElement("h2"); h2.textContent = "Overview"; card.appendChild(h2);
    const p = document.createElement("p"); p.innerHTML = `<strong>Chart ID:</strong> ${chart.id} • <strong>Reading ID:</strong> ${reading.id}`; card.appendChild(p);
    const linkHtml = document.createElement("a"); linkHtml.href = `/static/readings/${reading.id}.json`; linkHtml.textContent = "View Reading JSON"; linkHtml.target = "_blank"; card.appendChild(linkHtml);
    card.appendChild(document.createElement("br"));
    const linkPdf = document.createElement("a"); linkPdf.href = `/api/export/pdf?reading_id=${reading.id}`; linkPdf.textContent = "Download PDF"; linkPdf.target = "_blank"; card.appendChild(linkPdf);
    const h3 = document.createElement("h3"); h3.textContent = "Chart Wheel"; card.appendChild(h3);
    card.appendChild(ChartWheel(chart.planets, chart.houses));
    const h3s = document.createElement("h3"); h3s.textContent = "Sections"; card.appendChild(h3s);
    reading.sections.forEach(sec=>{
      const sdiv = document.createElement("div"); sdiv.className="card";
      const tt = document.createElement("h4"); tt.textContent = sec.title; sdiv.appendChild(tt);
      const ss = document.createElement("p"); ss.textContent = sec.short; sdiv.appendChild(ss);
      const lg = document.createElement("div"); lg.textContent = sec.long; sdiv.appendChild(lg);
      if (sec.actions && sec.actions.length){
        const ul = document.createElement("ul");
        sec.actions.forEach(a=>{ const li = document.createElement("li"); li.textContent = a; ul.appendChild(li); });
        sdiv.appendChild(ul);
      }
      card.appendChild(sdiv);
    });
    out.innerHTML = ""; out.appendChild(card);
    // Transits
    try {
      const trans = await computeTransits(chart, payload.tz);
      renderTransits(trans);
    } catch(e){
      document.getElementById("transits").textContent = "Transits need Swiss Ephemeris files on the server.";
    }
  } catch(e){
    console.error(e);
    out.innerHTML = "<div class='card'>Something went wrong. Try again.</div>";
  }
});
