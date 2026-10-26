"""Capture genuine browser screenshots of live API and deterministic HW7 evidence outputs."""

import json
import shutil
from pathlib import Path

from playwright.sync_api import sync_playwright

from hw7_agent import ScriptedActionModel, run_agent
from hw7_filetools import confirm_bash, glob_files, read_file, search_in_files, write_file

ROOT = Path(__file__).parent
REPORT = ROOT / "reports" / "hw07"
BROWSER = ROOT / "tmp" / "playwright-browsers" / "chromium-1248" / "chrome-win64" / "chrome.exe"


def api_capture(page):
    page.goto("http://127.0.0.1:8785/hw7", wait_until="networkidle")
    page.evaluate(
        r"""async () => {
        const form = (u, p) => new URLSearchParams({username: u, password: p});
        const req = async (label, url, options = {}) => {
          const r = await fetch(url, options);
          const raw = await r.text();
          let body = raw;
          try { body = JSON.stringify(JSON.parse(raw)); } catch (_) {}
          return {label, status: r.status, body};
        };
        const login = async (u, p) => {
          const r = await fetch('/auth/login', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:form(u,p)});
          return {status:r.status, data: await r.json()};
        };
        const bad = await login('reader', 'bad');
        const reader = await login('reader', 'reader');
        const writer = await login('writer', 'writer');
        const moderator = await login('moderator', 'moderator');
        const rh = {'Authorization': `Bearer ${reader.data.access_token}`, 'Content-Type':'application/json'};
        const wh = {'Authorization': `Bearer ${writer.data.access_token}`, 'Content-Type':'application/json'};
        const mh = {'Authorization': `Bearer ${moderator.data.access_token}`, 'Content-Type':'application/json'};
        const payload = JSON.stringify({restaurantName:'Live HW7 Evidence Cafe', location:'San Jose', email:'evidence@example.com', description:'evidence', category:'routine'});
        const created = await req('writer create (201)', '/inspections/', {method:'POST', headers:wh, body:payload});
        const id = JSON.parse(created.body).id;
        const results = [
          {label:'successful login (200)', status:reader.status, body:'JWT returned'},
          {label:'failed login (401)', status:bad.status, body:JSON.stringify(bad.data)},
          await req('missing token /auth/me (401)', '/auth/me'),
          await req('invalid token /auth/me (401)', '/auth/me', {headers:{Authorization:'Bearer invalid.token.value'}}),
          await req('reader create (403)', '/inspections/', {method:'POST', headers:rh, body:payload}),
          created,
          await req('authenticated list (200)', '/inspections/', {headers:rh}),
          await req('writer delete (403)', `/inspections/${id}`, {method:'DELETE', headers:wh}),
          await req('moderator delete (204)', `/inspections/${id}`, {method:'DELETE', headers:mh})
        ];
        document.body.innerHTML = '<style>body{font-family:Arial;max-width:1250px;margin:32px;font-size:18px}pre{font:16px Consolas,monospace;white-space:pre-wrap}</style><h1>Bhushan Waingankar — HW7 live API evidence</h1><p>Responses from the running FastAPI application at 127.0.0.1:8785</p><pre id="evidence"></pre>';
        document.getElementById('evidence').textContent = results.map(x => `${x.label}: HTTP ${x.status}\n${x.body}`).join('\n\n');
      }"""
    )
    page.screenshot(path=REPORT / "hw7_api_auth_roles_live.png", full_page=True)


def agent_capture(page):
    cases = {
        "A search then detail": [
            {"tool": "search", "inputs": {"query": "restaurant"}},
            {"tool": "detail_lookup", "inputs": {"inspection_id": 1}},
            {"final": "Task A complete"},
        ],
        "B aggregate then supporting detail": [
            {"tool": "aggregate", "inputs": {"group_by": "category"}},
            {"tool": "detail_lookup", "inputs": {"inspection_id": 1}},
            {"final": "Task B complete"},
        ],
        "C search then two details": [
            {"tool": "search", "inputs": {"query": "restaurant"}},
            {"tool": "detail_lookup", "inputs": {"inspection_id": 1}},
            {"tool": "detail_lookup", "inputs": {"inspection_id": 2}},
            {"final": "Task C complete"},
        ],
        "nonexistent ID recovery": [
            {"tool": "detail_lookup", "inputs": {"inspection_id": 999999}},
            {"final": "No inspection found; handled without crashing"},
        ],
    }
    results = {}
    for name, actions in cases.items():
        results[name] = run_agent(
            name,
            model=ScriptedActionModel(actions),
            tool_executor=lambda tool, inputs: json.dumps(
                {"ok": False, "error": "inspection not found"}
                if tool == "detail_lookup" and inputs.get("inspection_id") == 999999
                else {"ok": True, "data": [{"id": 1}, {"id": 2}]}
            ),
        )
        page.set_content(
        "<style>body{font-family:Arial;margin:32px}pre{font:18px Consolas,monospace;white-space:pre-wrap}</style>"
        "<h1>Bhushan Waingankar — HW7 Part 2 evidence</h1>"
        "<p>Actual run_agent outputs using the fixed deterministic verification cases.</p>"
        f"<pre>{json.dumps({k: {'stop_reason': v['stop_reason'], 'tool_call_count': v['tool_call_count'], 'answer': v['answer']} for k, v in results.items()}, indent=2)}</pre>"
    )
    page.screenshot(path=REPORT / "hw7_part2_tasks_and_recovery.png", full_page=True)


def file_capture(page):
    root = ROOT / "tmp" / "hw7_screenshot_sandbox"
    root.mkdir(parents=True, exist_ok=True)
    try:
        write_file(root / "one.py", "DEBUG = True\n", root)
        write_file(root / "two.py", "OK = True\n", root)
        integration = {
            "glob": [str(p) for p in glob_files("*.py", root)],
            "search": search_in_files("DEBUG", root, "*.py"),
            "read": read_file(root / "one.py", root, 10),
        }
        commands = [
            ("python -c \"print(1)\"", True), ("dir", True), ("type file.txt", True),
            ("rg DEBUG .", True), ("python --version", True),
            ("rm -rf sandbox", False), ("sudo chmod 777 file", False),
            ("format C:", False), ("dd if=x of=/dev/sda", False), ("echo x > /etc/x", False),
        ]
        safety = [{"command": c, "allowed": confirm_bash(c, False)["allowed"]} for c, _ in commands]
        page.set_content(
            "<style>body{font-family:Arial;margin:32px}pre{font:16px Consolas,monospace;white-space:pre-wrap}</style>"
            "<h1>Bhushan Waingankar — HW7 Part 6 evidence</h1>"
            "<p>Actual file-tool integration and deterministic safety-gate outputs.</p>"
            f"<pre>{json.dumps({'integration': integration, 'safety_gate': safety}, indent=2)}</pre>"
        )
        page.screenshot(path=REPORT / "hw7_part6_filetools_safety.png", full_page=True)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main():
    REPORT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=str(BROWSER))
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        api_capture(page)
        agent_capture(page)
        file_capture(page)
        browser.close()


if __name__ == "__main__":
    main()
