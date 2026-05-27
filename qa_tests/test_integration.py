from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from polls.models import Choice, Poll, Vote


class DuplicateVoteIntegrationTest(TestCase):
    """View ↔ ORM ↔ DB. Voting twice never produces two Vote rows."""

    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="secret")
        self.poll = Poll.objects.create(owner=self.alice, text="Q?")
        self.c1 = Choice.objects.create(poll=self.poll, choice_text="A")
        self.c2 = Choice.objects.create(poll=self.poll, choice_text="B")
        self.client.login(username="alice", password="secret")

    def test_second_vote_attempt_blocked_and_db_rejects_raw_duplicate(self):
        url = reverse("polls:vote", kwargs={"poll_id": self.poll.id})

        r1 = self.client.post(url, {"choice": self.c1.id})
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(
            Vote.objects.filter(user=self.alice, poll=self.poll).count(), 1
        )

        r2 = self.client.post(url, {"choice": self.c2.id})
        self.assertEqual(r2.status_code, 302)
        self.assertEqual(r2.url, reverse("polls:list"))

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Vote.objects.create(
                    user=self.alice, poll=self.poll, choice=self.c2
                )

        self.assertEqual(
            Vote.objects.filter(user=self.alice, poll=self.poll).count(), 1
        )


class RegistrationFormIntegrationTest(TestCase):
    """Form ↔ User table. The form really creates a row and rejects dups."""

    URL = "/accounts/register/"

    def test_form_creates_user_row_and_rejects_duplicate_username(self):
        r1 = self.client.post(self.URL, {
            "username": "alicia",
            "email": "alicia@example.com",
            "password1": "secret",
            "password2": "secret",
        })
        self.assertEqual(r1.status_code, 302)
        self.assertTrue(User.objects.filter(username="alicia").exists())

        before = User.objects.count()
        r2 = self.client.post(self.URL, {
            "username": "alicia",
            "email": "someone-else@example.com",
            "password1": "secret",
            "password2": "secret",
        })
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(User.objects.count(), before)
        self.assertIn(
            "Username already exists!",
            r2.context["form"].errors["username"],
        )
