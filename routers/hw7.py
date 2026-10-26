"""Small browser-facing HW7 MRKL demonstration UI."""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from hw7_bikeshare import run_scenario

router = APIRouter(tags=["HW7"])


@router.get("/hw7", response_class=HTMLResponse)
def hw7_page():
    return HTMLResponse("""<!doctype html><html><head><meta charset='utf-8'><title>HW7 Citi Bike MRKL</title>
<style>body{font-family:Arial;max-width:1100px;margin:2rem auto;color:#17202a}input,button{padding:.6rem;margin:.25rem}button{background:#0b5;color:white;border:0;border-radius:4px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem}.panel{border:1px solid #ccd6dd;border-radius:8px;padding:1rem}.timeline{background:#f5f7f9;padding:.75rem;min-height:5rem}.decision{font-size:1.35rem;font-weight:bold;color:#075e54}</style></head>
<body><h1>Citi Bike Membership Advisor</h1><p>Upload a trip CSV and provide the official pricing URL. Retrieved policy text is treated as untrusted evidence.</p>
<div class='panel'><input id='csv' type='file' accept='.csv'><input id='url' size='60' value='https://citibikenyc.com/pricing/annual'><button id='run'>Run MRKL Agent</button></div>
<div class='grid'><section class='panel'><h2>Tool-call timeline</h2><pre id='timeline' class='timeline'></pre></section><section class='panel'><h2>Results</h2><div id='result'>Waiting for a CSV.</div></section></div>
<script>const $=id=>document.getElementById(id);$('run').onclick=async()=>{const file=$('csv').files[0];if(!file){$('result').textContent='Select a CSV first.';return}const text=await file.text();$('timeline').textContent='1. csv_sql: aggregate uploaded trips\\n2. policy_retriever: retrieve pricing snippets\\n3. calculator: compare costs\\n4. verifier: check decision and evidence';const r=await fetch('/api/hw7/bikeshare',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({csv_text:text,pricing_url:$('url').value})});const data=await r.json();$('result').innerHTML=data.error?'<b>Error:</b> '+data.error:'<div class="decision">'+data.decision+'</div><p>Pay per use: $'+data.costs.pay_per_use+'<br>Membership + residual: $'+data.costs.membership_plus_residual+'<br>Rides: '+data.ride_count+'; steps: '+data.steps+'; stop: '+data.stop_reason+'</p><p><a href="'+data.source_url+'" target="_blank">Pricing citation</a></p>'}</script></body></html>""")


@router.post("/api/hw7/bikeshare")
def bikeshare(payload: dict[str, str]):
    import tempfile
    from pathlib import Path

    csv_text = payload.get("csv_text", "")
    pricing_url = payload.get("pricing_url", "https://citibikenyc.com/pricing/annual")
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as stream:
        stream.write(csv_text)
        path = Path(stream.name)
    try:
        return run_scenario(path, pricing_url)
    finally:
        path.unlink(missing_ok=True)
