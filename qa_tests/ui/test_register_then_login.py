"""Register a new user and immediately log in as them."""
from playwright.sync_api import Page, expect


def test_register_then_login(page: Page, live_server, db, screenshot_dir):
    base = live_server.url

    page.goto(f"{base}/accounts/register/")
    page.locator("input[name='username']").fill("alicia")
    page.locator("input[name='email']").fill("alicia@example.com")
    page.locator("input[name='password1']").fill("secret")
    page.locator("input[name='password2']").fill("secret")
    page.locator("button:has-text('Sign Up')").click()

    expect(page).to_have_url(f"{base}/accounts/login/")

    page.locator("input[name='username']").fill("alicia")
    page.locator("input[name='password']").fill("secret")
    page.locator("button:has-text('Login')").click()

    expect(page).to_have_url(f"{base}/")
    expect(page.get_by_role("link", name="Logout")).to_be_visible()

    page.screenshot(path=str(screenshot_dir / "01_register_then_login.png"))
