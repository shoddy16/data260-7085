from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
REPORT = ROOT / "reports" / "hw07"
CSV = REPORT / "raw" / "pay_per_use_wins.csv"
MEMBERSHIP_CSV = REPORT / "raw" / "membership_wins.csv"
PRICING = REPORT / "raw" / "citi_bike_pricing_snapshot.txt"


def main() -> None:
    REPORT.mkdir(parents=True, exist_ok=True)
    browser_path = ROOT / "tmp" / "playwright-browsers"
    with sync_playwright() as playwright:
        executable = browser_path / "chromium-1248" / "chrome-win64" / "chrome.exe"
        browser = playwright.chromium.launch(headless=True, executable_path=str(executable))
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        page.on("pageerror", lambda error: print("pageerror", error))
        page.on("console", lambda message: print("console", message.type, message.text))
        page.goto("http://127.0.0.1:8785/hw7", wait_until="networkidle")
        print("handler", page.locator("#run").evaluate("element => String(element.onclick)"))
        page.screenshot(path=REPORT / "hw7_ui_initial.png", full_page=True)
        page.locator("#csv").set_input_files(str(CSV))
        page.locator("#url").fill(PRICING.as_uri())
        page.locator("#run").click(no_wait_after=True)
        page.wait_for_timeout(5000)
        page.wait_for_timeout(500)
        print("timeline", page.locator("#timeline").inner_text())
        print("result", page.locator("#result").inner_text())
        page.screenshot(path=REPORT / "hw7_ui_pay_per_use_result.png", full_page=True)
        page.locator("#csv").set_input_files(str(MEMBERSHIP_CSV))
        page.locator("#url").fill(PRICING.as_uri())
        page.locator("#run").click(no_wait_after=True)
        page.wait_for_timeout(5000)
        print("membership_timeline", page.locator("#timeline").inner_text())
        print("membership_result", page.locator("#result").inner_text())
        page.screenshot(path=REPORT / "hw7_ui_membership_result.png", full_page=True)
        browser.close()
    print(browser_path)


if __name__ == "__main__":
    main()
