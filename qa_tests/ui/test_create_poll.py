"""Create a new poll with two choices and verify it appears in the list."""

from playwright.sync_api import Page, expect

from .conftest import login_via_ui


def test_create_poll(page: Page, live_server, alice, screenshot_dir):
    base = live_server.url
    login_via_ui(page, base)

    page.goto(f"{base}/polls/add/")
    page.locator("textarea[name='text']").fill("Best language?")
    page.locator("input[name='choice1']").fill("Python")
    page.locator("input[name='choice2']").fill("JavaScript")
    page.locator("button:has-text('Add Poll')").click()

    expect(page).to_have_url(f"{base}/polls/list/")
    expect(page.get_by_text("Best language?")).to_be_visible()

    page.screenshot(path=str(screenshot_dir / "02_create_poll.png"))
