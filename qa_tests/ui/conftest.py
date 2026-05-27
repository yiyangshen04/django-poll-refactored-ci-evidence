import os

os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

from pathlib import Path

import pytest
from django.contrib.auth.models import Permission, User

from polls.models import Choice, Poll


SCREENSHOTS = (
    Path(__file__).resolve().parents[2] / "screenshots" / "q5_ui"
)
SCREENSHOTS.mkdir(parents=True, exist_ok=True)


@pytest.fixture
def screenshot_dir():
    return SCREENSHOTS


@pytest.fixture
def browser_context_args(browser_context_args):
    return {**browser_context_args, "viewport": {"width": 1280, "height": 800}}


@pytest.fixture
def alice(db):
    user = User.objects.create_user(
        username="alice", password="secret", email="alice@example.com"
    )
    perm = Permission.objects.get(codename="add_poll")
    user.user_permissions.add(perm)
    return user


@pytest.fixture
def sample_poll(alice):
    poll = Poll.objects.create(owner=alice, text="Best language to learn first?")
    Choice.objects.create(poll=poll, choice_text="Python")
    Choice.objects.create(poll=poll, choice_text="JavaScript")
    return poll


def login_via_ui(page, base_url, username="alice", password="secret"):
    page.goto(f"{base_url}/accounts/login/")
    page.locator("input[name='username']").fill(username)
    page.locator("input[name='password']").fill(password)
    page.locator("button:has-text('Login')").click()
    page.wait_for_url(f"{base_url}/")
