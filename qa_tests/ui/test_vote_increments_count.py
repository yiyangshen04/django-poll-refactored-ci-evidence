"""Cast a vote and confirm the result page shows the count went up by one."""
from playwright.sync_api import Page, expect

from .conftest import login_via_ui


def test_vote_increments_count(page: Page, live_server, sample_poll, screenshot_dir):
    base = live_server.url
    login_via_ui(page, base)

    page.goto(f"{base}/polls/{sample_poll.id}/")
    first_choice = sample_poll.choice_set.first()
    page.locator(f"input[name='choice'][value='{first_choice.id}']").check()
    page.locator("input[type='submit'][value='Vote']").click()

    expect(page.get_by_text(f"Result for: {sample_poll.text}")).to_be_visible()
    expect(page.get_by_text("Total: 1 votes")).to_be_visible()

    page.screenshot(path=str(screenshot_dir / "03_vote_result.png"))
