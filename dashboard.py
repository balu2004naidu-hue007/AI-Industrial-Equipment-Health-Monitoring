#!/usr/bin/env python3
"""Local, browser-based machine monitoring dashboard (no cloud service required)."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from industrial_monitoring.core import ModelBundle, analyze_reading, load_models, parse_timestamp, read_machine_rows

HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Industrial Guardian | Equipment Health</title>
<style>
:root{color-scheme:dark;--bg:#070b11;--panel:#0f1722;--panel2:#111d2a;--line:#243446;--muted:#92a2b2;--text:#e8f0f7;--blue:#60b8ff;--green:#43d99a;--yellow:#ffca63;--red:#ff6674}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 15% 0%,#132238 0,transparent 34%),var(--bg);color:var(--text);font-family:Inter,Segoe UI,Arial,sans-serif}.wrap{max-width:1500px;margin:auto;padding:28px 26px 44px}
header{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;flex-wrap:wrap}h1{font-size:clamp(24px,3vw,34px);margin:0 0 7px;letter-spacing:-.6px}.subtitle{color:var(--muted);font-size:13px}.pill{display:inline-flex;align-items:center;gap:8px;border:1px solid var(--line);background:#0c1723;border-radius:30px;padding:9px 13px;color:var(--muted);font-size:12px}.lamp{height:8px;width:8px;border-radius:50%;background:var(--yellow)}.pill.ok{color:var(--green);border-color:#22583f}.pill.ok .lamp{background:var(--green)}.pill.bad{color:var(--red);border-color:#64303a}.pill.bad .lamp{background:var(--red)}
.section{margin-top:26px}.section h2{font-size:15px;font-weight:700;margin:0 0 11px;color:#d5e0e9;letter-spacing:.2px}.grid{display:grid;gap:12px}.kpis{grid-template-columns:repeat(4,minmax(0,1fr))}.sensors{grid-template-columns:repeat(5,minmax(0,1fr))}.tri{grid-template-columns:repeat(3,minmax(0,1fr))}.two{grid-template-columns:repeat(2,minmax(0,1fr))}.card{min-width:0;background:linear-gradient(145deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:13px;padding:16px;box-shadow:0 8px 22px #0002}.label{font-size:10px;text-transform:uppercase;letter-spacing:1px;color:var(--muted)}.big{font-size:27px;font-weight:750;margin-top:9px;letter-spacing:-.6px}.value{font-size:22px;font-weight:700;margin-top:9px}.unit{font-size:11px;color:var(--muted);font-weight:500}.good{color:var(--green)}.warn{color:var(--yellow)}.danger{color:var(--red)}.blue{color:var(--blue)}
.ai-card{min-height:112px}.ai-value{font-size:15px;font-weight:650;line-height:1.5;margin-top:10px}.small{font-size:11px;color:var(--muted);line-height:1.5;margin-top:8px}.chart{height:270px}.chart svg{width:100%;height:205px;display:block;margin-top:10px}.chart-meta{color:var(--muted);font-size:10px;display:flex;justify-content:space-between}.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse;font-size:11px;white-space:nowrap}th,td{text-align:left;padding:10px 9px;border-bottom:1px solid #203040}th{color:var(--muted);font-weight:600;text-transform:uppercase;font-size:9px;letter-spacing:.7px}.footer{margin-top:18px;color:var(--muted);font-size:10px;display:flex;gap:16px;flex-wrap:wrap}.notice{display:none;margin-top:13px;border:1px solid #735a2b;border-radius:10px;padding:11px 13px;color:#ffd78a;background:#221b0e;font-size:12px}.notice.show{display:block}.muted{color:var(--muted)}
@media(max-width:1000px){.sensors{grid-template-columns:repeat(3,1fr)}}@media(max-width:720px){.wrap{padding:19px 12px 30px}.kpis,.tri,.two,.sensors{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:440px){.kpis,.tri,.two,.sensors{grid-template-columns:1fr}.big{font-size:24px}}
</style></head><body><div class="wrap">
<header><div><h1>🏭 Industrial Guardian</h1><div class="subtitle">AI-assisted equipment health monitoring · anomaly screening · predictive maintenance support</div></div><div id="connection" class="pill"><span class="lamp"></span><span>Connecting to local data service…</span></div></header>
<div id="notice" class="notice"></div>
<section class="section"><h2>Machine overview</h2><div class="grid kpis">
<div class="card"><div class="label">Condition status</div><div id="status" class="big">NO DATA</div><div id="mode" class="small">Waiting for sensor readings</div></div>
<div class="card"><div class="label">Overall risk score</div><div id="risk" class="big">—</div><div class="small">0 = lower screening risk · 100 = higher screening risk</div></div>
<div class="card"><div class="label">Health score</div><div id="health" class="big">—</div><div class="small">Derived as 100 minus the risk score</div></div>
<div class="card"><div class="label">Anomaly detector</div><div id="anomaly" class="big">—</div><div id="modelstate" class="small">Model status unavailable</div></div>
</div></section>
<section class="section"><h2>Live machine parameters</h2><div class="grid sensors" id="sensors"></div></section>
<section class="section"><h2>AI-assisted condition assessment</h2><div class="grid tri">
<div class="card ai-card"><div class="label">Pattern / diagnosis</div><div id="diagnosis" class="ai-value">Waiting for data</div></div>
<div class="card ai-card"><div class="label">Maintenance recommendation</div><div id="recommendation" class="ai-value">Start the simulator or connect the serial logger.</div></div>
<div class="card ai-card"><div class="label">Illustrative RUL proxy</div><div id="rul" class="ai-value">—</div><div class="small">Heuristic only; not a trained remaining-useful-life estimate.</div></div>
</div><div id="method" class="small"></div></section>
<section class="section"><h2>Sensor trends · latest 180 valid readings</h2><div class="grid two">
<div class="card chart"><div class="label">Temperature · °C</div><div id="chart_temperature"></div></div>
<div class="card chart"><div class="label">Vibration · mm/s (confirm sensor scaling)</div><div id="chart_vibration"></div></div>
<div class="card chart"><div class="label">RPM</div><div id="chart_rpm"></div></div>
<div class="card chart"><div class="label">Load · %</div><div id="chart_load"></div></div>
<div class="card chart"><div class="label">Voltage · V</div><div id="chart_voltage"></div></div>
<div class="card chart"><div class="label">Motor current · A</div><div id="chart_motor_current"></div></div>
</div></section>
<section class="section"><h2>Recent machine history</h2><div class="card table-wrap"><table><thead><tr><th>Timestamp</th><th>Mode</th><th>Temperature</th><th>Vibration</th><th>RPM</th><th>Current</th><th>Load</th><th>Risk</th><th>Status</th></tr></thead><tbody id="history"><tr><td colspan="9" class="muted">No readings yet</td></tr></tbody></table></div></section>
<div class="footer"><span>Local-only dashboard · refreshes every 2 seconds</span><span id="latest-time">Latest reading: —</span><span id="age">Data age: —</span><span id="count">Rows: —</span><span>Training data/model are synthetic educational baselines</span></div>
</div>
<script>
const PARAMS=[['temperature','Temperature','°C',2],['vibration','Vibration','mm/s',2],['rpm','RPM','',0],['motor_current','Motor current','A',2],['voltage','Voltage','V',2],['power','Power','W',1],['pressure','Pressure','bar',2],['ambient_temperature','Ambient temperature','°C',2],['load','Load','%',1],['running_hours','Running hours','h',1]];
const fmt=(x,d=1)=>Number.isFinite(Number(x))?Number(x).toFixed(d):'—';
const riskClass=x=>x>=70?'danger':x>=40?'warn':'good';
function setText(id,value){document.getElementById(id).textContent=value;}
function renderChart(id,rows,key){const el=document.getElementById(id);if(!rows.length){el.textContent='Waiting for readings…';return;}const vals=rows.map(r=>Number(r[key])).filter(Number.isFinite);if(!vals.length){el.textContent='No valid values';return;}let min=Math.min(...vals),max=Math.max(...vals);if(min===max){min-=1;max+=1;}const w=700,h=190,p=14;const pts=vals.map((v,i)=>{const x=p+(vals.length===1?0:i*(w-2*p)/(vals.length-1));const y=h-p-(v-min)/(max-min)*(h-2*p);return `${x.toFixed(1)},${y.toFixed(1)}`}).join(' ');const last=vals[vals.length-1],y=h-p-(last-min)/(max-min)*(h-2*p);el.innerHTML=`<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" role="img" aria-label="${key} time series"><line x1="${p}" y1="${h-p}" x2="${w-p}" y2="${h-p}" stroke="#26394b"/><polyline points="${pts}" fill="none" stroke="#60b8ff" stroke-width="3" vector-effect="non-scaling-stroke"/><circle cx="${w-p}" cy="${y}" r="4" fill="#43d99a"/></svg><div class="chart-meta"><span>Min ${fmt(min,2)}</span><span>Latest ${fmt(last,2)}</span><span>Max ${fmt(max,2)}</span></div>`;}
function render(s){const r=s.latest;if(!r){setText('status','NO DATA');setText('risk','—');setText('health','—');setText('diagnosis','Waiting for first valid reading');setText('recommendation','Run simulate_machine.py or connect the serial logger.');return;}
const a=s.analysis;setText('status',a.status);document.getElementById('status').className='big '+riskClass(a.risk_score);setText('mode',r.machine_mode.replaceAll('_',' '));setText('risk',fmt(a.risk_score,1)+'/100');document.getElementById('risk').className='big '+riskClass(a.risk_score);setText('health',fmt(a.health_score,1)+'%');document.getElementById('health').className='big '+riskClass(100-a.health_score);setText('anomaly',a.anomaly_status);document.getElementById('anomaly').className='big '+(a.anomaly_status==='ANOMALY'?'danger':a.anomaly_status==='NORMAL'?'good':'warn');setText('modelstate',s.model_status);setText('diagnosis',a.diagnosis);setText('recommendation',a.recommendation);setText('rul',fmt(a.rul_proxy_hours,0)+' h · proxy');setText('method','Assessment source: '+a.model_source+'. '+a.rul_note);
document.getElementById('sensors').innerHTML=PARAMS.map(([k,l,u,d])=>`<div class="card"><div class="label">${l}</div><div class="value">${fmt(r[k],d)} <span class="unit">${u}</span></div></div>`).join('');
['temperature','vibration','rpm','load','voltage','motor_current'].forEach(k=>renderChart('chart_'+k,s.rows,k));
document.getElementById('history').innerHTML=s.history.slice().reverse().map(x=>`<tr><td>${x.timestamp}</td><td>${x.machine_mode}</td><td>${fmt(x.temperature,1)}</td><td>${fmt(x.vibration,2)}</td><td>${fmt(x.rpm,0)}</td><td>${fmt(x.motor_current,2)}</td><td>${fmt(x.load,1)}</td><td>${fmt(x.analysis.risk_score,1)}</td><td>${x.analysis.status}</td></tr>`).join('');
setText('latest-time','Latest reading: '+r.timestamp);setText('age','Data age: '+(s.data_age_seconds===null?'unknown':fmt(s.data_age_seconds,0)+' s'));setText('count','Rows: '+s.total_valid_rows);}
async function update(){try{const response=await fetch('/api/live?ts='+Date.now(),{cache:'no-store'});if(!response.ok)throw new Error('HTTP '+response.status);const s=await response.json();render(s);const c=document.getElementById('connection');if(s.is_stale){c.className='pill bad';c.innerHTML='<span class="lamp"></span><span>DATA STALE</span>';}else if(s.latest){c.className='pill ok';c.innerHTML='<span class="lamp"></span><span>LOCAL DATA CONNECTED</span>';}else{c.className='pill';c.innerHTML='<span class="lamp"></span><span>WAITING FOR DATA</span>';}
const n=document.getElementById('notice');if(s.warnings&&s.warnings.length){n.textContent=s.warnings.join(' · ');n.className='notice show';}else{n.textContent='';n.className='notice';}}
catch(e){const c=document.getElementById('connection');c.className='pill bad';c.innerHTML='<span class="lamp"></span><span>DATA SERVICE ERROR</span>';setText('status','SERVER ERROR');document.getElementById('status').className='big danger';}}
update();setInterval(update,2000);
</script></body></html>'''


class DashboardApp:
    def __init__(self, data_file: Path, models_dir: Path, stale_after: float):
        self.data_file = data_file
        self.models = load_models(models_dir)
        self.stale_after = stale_after

    def snapshot(self) -> dict:
        warnings: list[str] = []
        try:
            rows, read_warnings = read_machine_rows(self.data_file, limit=180)
            warnings.extend(read_warnings)
        except Exception as exc:
            rows = []
            warnings.append(str(exc))
        latest = rows[-1] if rows else None
        history = []
        for row in rows[-30:]:
            history.append({**row, "analysis": analyze_reading(row, self.models)})
        now = datetime.now(timezone.utc)
        age = None
        stale = False
        analysis = None
        if latest:
            timestamp = parse_timestamp(latest["timestamp"])
            if timestamp:
                age = max(0.0, (now - timestamp).total_seconds())
                stale = age > self.stale_after
            analysis = analyze_reading(latest, self.models)
        warnings.extend(self.models.warnings)
        if stale:
            warnings.insert(0, f"Latest valid reading is {age:.0f} seconds old; check the logger or simulator.")
        if not latest:
            warnings.insert(0, "No valid machine readings yet. Start the simulator or serial logger.")
        return {
            "ok": bool(latest), "latest": latest, "analysis": analysis,
            "rows": rows[-180:], "history": history,
            "total_valid_rows": len(rows), "data_age_seconds": age,
            "is_stale": stale, "model_status": "Predictive model loaded" if self.models.predictive_model is not None else "Predictive model unavailable · rule-based mode",
            "warnings": warnings,
        }


def create_handler(app: DashboardApp):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            return

        def send_payload(self, payload: bytes, content_type: str, status: int = 200):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path == "/":
                self.send_payload(HTML.encode("utf-8"), "text/html; charset=utf-8")
            elif path == "/api/live":
                body = json.dumps(app.snapshot(), separators=(",", ":"), allow_nan=False).encode("utf-8")
                self.send_payload(body, "application/json; charset=utf-8")
            elif path == "/healthz":
                self.send_payload(b"ok", "text/plain; charset=utf-8")
            else:
                self.send_payload(b"Not found", "text/plain; charset=utf-8", 404)

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1", help="Defaults to loopback for local-only access")
    parser.add_argument("--port", type=int, default=8501)
    parser.add_argument("--data", type=Path, default=ROOT / "data" / "live_machine_data.csv")
    parser.add_argument("--models-dir", type=Path, default=ROOT / "models")
    parser.add_argument("--stale-after", type=float, default=10.0, help="Seconds before the newest reading is marked stale")
    args = parser.parse_args()
    if not (1 <= args.port <= 65535) or args.stale_after <= 0:
        parser.error("port must be 1-65535 and stale-after must be positive")
    app = DashboardApp(args.data, args.models_dir, args.stale_after)
    server = ThreadingHTTPServer((args.host, args.port), create_handler(app))
    print("=" * 68)
    print("INDUSTRIAL GUARDIAN · LOCAL MONITORING DASHBOARD")
    print(f"Dashboard: http://{args.host}:{args.port}")
    print(f"Data file: {args.data}")
    print(f"Predictive model loaded: {app.models.predictive_model is not None}")
    print(f"Anomaly model loaded: {app.models.anomaly_model is not None}")
    print("Press Ctrl+C to stop. Dashboard binds to localhost by default.")
    print("=" * 68)
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
