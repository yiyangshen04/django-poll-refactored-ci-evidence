"""Try to vote twice on the same poll: second attempt should be blocked."""

from playwright.sync_api import Page, expect

from polls.models import Vote

from .conftest import login_via_ui


def test_double_vote_blocked(
    page: Page, live_server, alice, sample_poll, screenshot_dir
):
    base = live_server.url
    first_choice = sample_poll.choice_set.first()
    Vote.objects.create(user=alice, poll=sample_poll, choice=first_choice)

    login_via_ui(page, base)

    page.goto(f"{base}/polls/{sample_poll.id}/")
    second_choice = sample_poll.choice_set.last()
    page.locator(f"input[name='choice'][value='{second_choice.id}']").check()
    page.locator("input[type='submit'][value='Vote']").click()

    expect(page).to_have_url(f"{base}/polls/list/")
    expect(page.get_by_text("You already voted this poll!")).to_be_visible()

    page.screenshot(path=str(screenshot_dir / "04_double_vote_blocked.png"))
