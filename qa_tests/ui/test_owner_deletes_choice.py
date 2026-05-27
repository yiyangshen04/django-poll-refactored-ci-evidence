"""Poll owner deletes a choice and the edit page should show one fewer."""

from playwright.sync_api import Page, expect

from .conftest import login_via_ui


def test_owner_deletes_choice(
    page: Page, live_server, alice, sample_poll, screenshot_dir
):
    base = live_server.url
    login_via_ui(page, base)

    page.goto(f"{base}/polls/edit/{sample_poll.id}/")
    expect(page.locator(".choices li.list-group-item")).to_have_count(2)

    target = sample_poll.choice_set.first()
    page.goto(f"{base}/polls/delete/choice/{target.id}/")

    expect(page).to_have_url(f"{base}/polls/edit/{sample_poll.id}/")
    expect(page.locator(".choices li.list-group-item")).to_have_count(1)
    expect(page.get_by_text("Choice Deleted successfully.")).to_be_visible()

    page.screenshot(path=str(screenshot_dir / "05_owner_deletes_choice.png"))
