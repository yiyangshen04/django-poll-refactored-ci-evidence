from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase

from accounts.forms import UserRegistrationForm
from polls.models import Choice, Poll, Vote
from polls.services import attach_alert_classes, compute_poll_results


# --- test doubles --------------------------------------------------------

class FakeChoice:
    def __init__(self, text, votes):
        self.choice_text = text
        self.get_vote_count = votes


class FakeChoiceSet:
    def __init__(self, choices):
        self._choices = choices

    def all(self):
        return self._choices


class FakePoll:
    def __init__(self, choices):
        self.choice_set = FakeChoiceSet(choices)
        self.get_vote_count = sum(c.get_vote_count for c in choices)


class StubRNG:
    def __init__(self, return_value):
        self._value = return_value

    def choice(self, seq):
        return self._value


class SpyVoteSet:
    def __init__(self, exists_return):
        self.filter_calls = []
        self.all_called = False
        self._exists_return = exists_return

    def all(self):
        self.all_called = True
        return self

    def filter(self, **kwargs):
        self.filter_calls.append(kwargs)
        return self

    def exists(self):
        return self._exists_return


class SpyUser:
    def __init__(self, spy_vote_set):
        self.vote_set = spy_vote_set


# --- tests using doubles -------------------------------------------------

class ComputePollResultsTests(SimpleTestCase):
    def test_percentages_match_vote_distribution(self):
        poll = FakePoll([
            FakeChoice("Python", 3),
            FakeChoice("JS", 1),
            FakeChoice("Rust", 0),
        ])
        results = compute_poll_results(poll)
        self.assertEqual(results, [
            {"text": "Python", "num_votes": 3, "percentage": 75.0},
            {"text": "JS", "num_votes": 1, "percentage": 25.0},
            {"text": "Rust", "num_votes": 0, "percentage": 0.0},
        ])

    def test_zero_total_votes_returns_zero_percentage(self):
        poll = FakePoll([FakeChoice("A", 0), FakeChoice("B", 0)])
        results = compute_poll_results(poll)
        for r in results:
            self.assertEqual(r["percentage"], 0)


class AttachAlertClassesTests(SimpleTestCase):
    def test_uses_injected_rng_for_each_result(self):
        results = [
            {"text": "A", "num_votes": 1, "percentage": 100.0},
            {"text": "B", "num_votes": 0, "percentage": 0.0},
        ]
        rng = StubRNG("success")
        out = attach_alert_classes(results, rng=rng)
        self.assertEqual(out[0]["alert_class"], "success")
        self.assertEqual(out[1]["alert_class"], "success")


class CleanUsernameTests(SimpleTestCase):
    @patch("accounts.forms.User.objects")
    def test_clean_username_rejects_duplicate(self, mock_objects):
        mock_objects.filter.return_value.exists.return_value = True
        form = UserRegistrationForm()
        form.cleaned_data = {"username": "alice"}

        with self.assertRaises(ValidationError) as ctx:
            form.clean_username()

        mock_objects.filter.assert_called_once_with(username="alice")
        self.assertIn("Username already exists!", str(ctx.exception))


class UserCanVoteTests(SimpleTestCase):
    def test_filters_vote_set_by_poll(self):
        poll = Poll(id=1, text="t")
        spy_vote_set = SpyVoteSet(exists_return=False)
        user = SpyUser(spy_vote_set)

        result = poll.user_can_vote(user)

        self.assertTrue(result)
        self.assertTrue(spy_vote_set.all_called)
        self.assertEqual(spy_vote_set.filter_calls, [{"poll": poll}])


# --- tests without doubles -----------------------------------------------

class PasswordMatchTests(TestCase):
    def test_password_mismatch_attaches_error_to_password2(self):
        form = UserRegistrationForm(data={
            "username": "alicia",
            "email": "alicia@example.com",
            "password1": "secret",
            "password2": "different",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("Password did not match!", form.errors["password2"])


class ModelStrTests(SimpleTestCase):
    def test_poll_str_returns_text(self):
        poll = Poll(text="Best language?")
        self.assertEqual(str(poll), "Best language?")

    def test_choice_str_truncates_poll_and_choice_text_to_25(self):
        poll = Poll(text="x" * 30)
        choice = Choice(poll=poll, choice_text="y" * 30)
        self.assertEqual(str(choice), "x" * 25 + " - " + "y" * 25)

    def test_vote_str_format(self):
        poll = Poll(text="Best language to learn first?")
        choice = Choice(poll=poll, choice_text="JavaScript or Python")
        user = User(username="alice")
        vote = Vote(user=user, poll=poll, choice=choice)
        self.assertEqual(str(vote), "Best language t - JavaScript or P - alice")
