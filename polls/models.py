from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from .services import build_poll_result_dicts


class Poll(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    pub_date = models.DateTimeField(default=timezone.now)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def user_can_vote(self, user):
        """
        Return False if user already voted.
        """
        user_votes = user.vote_set.all()
        qs = user_votes.filter(poll=self)
        return not qs.exists()

    @property
    def get_vote_count(self):
        return self.vote_set.count()

    def get_result_dict(self, rng=None):
        """
        Thin wrapper over ``polls.services.build_poll_result_dicts`` so
        existing templates that call ``poll.get_result_dict`` keep working.
        New callers (notably tests) should pass ``rng`` to make the random
        ``alert_class`` deterministic.
        """
        return build_poll_result_dicts(self, rng=rng)

    def __str__(self):
        return self.text


class Choice(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def get_vote_count(self):
        return self.vote_set.count()

    def __str__(self):
        return f"{self.poll.text[:25]} - {self.choice_text[:25]}"


class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Enforce "one vote per user per poll" at the database level so the
        # check in views.poll_vote / Poll.user_can_vote cannot be raced. An
        # integration test can now assert that a duplicate INSERT raises
        # IntegrityError instead of silently writing two rows.
        constraints = [
            models.UniqueConstraint(
                fields=("user", "poll"),
                name="one_vote_per_user_per_poll",
            ),
        ]

    def __str__(self):
        poll_text = self.poll.text[:15]
        choice_text = self.choice.choice_text[:15]
        return f"{poll_text} - {choice_text} - {self.user.username}"
