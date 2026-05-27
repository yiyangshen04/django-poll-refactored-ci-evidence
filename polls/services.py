"""
Pure helpers extracted from ``polls.models.Poll.get_result_dict``.

The original implementation mixed three concerns in one method:

* statistics (per-choice vote count and percentage)
* presentation (random Bootstrap colour class for the bar)
* a non-injectable random source (``secrets.choice``)

That made the method untestable in isolation: every call returned a
different ``alert_class`` and there was no seam to swap the random source.
The helpers below split those concerns and let callers inject a ``rng`` so
unit tests can assert exact output with a stub.
"""

import random

ALERT_CLASSES = (
    'primary', 'secondary', 'success', 'danger', 'dark', 'warning', 'info',
)


def compute_poll_results(poll):
    """
    Return one dict per choice in ``poll`` with ``text``, ``num_votes`` and
    ``percentage`` keys. No presentation concerns are mixed in here, which
    means unit tests can feed a hand-built fake ``poll`` and assert the
    numbers exactly.
    """
    total = poll.get_vote_count
    results = []
    for choice in poll.choice_set.all():
        choice_votes = choice.get_vote_count
        percentage = (choice_votes / total) * 100 if total else 0
        results.append({
            'text': choice.choice_text,
            'num_votes': choice_votes,
            'percentage': percentage,
        })
    return results


def attach_alert_classes(results, rng=None, classes=ALERT_CLASSES):
    """
    Decorate each result dict with an ``alert_class`` (Bootstrap colour
    name). ``rng`` defaults to a fresh ``random.Random``; tests may pass a
    stub object exposing ``.choice(seq)`` to make output deterministic.
    Mutates and returns ``results`` for caller convenience.
    """
    rng = rng or random.Random()
    for entry in results:
        entry['alert_class'] = rng.choice(classes)
    return results


def build_poll_result_dicts(poll, rng=None):
    """
    Convenience wrapper: stats + colour assignment in the shape the
    ``poll_result.html`` template expects.
    """
    return attach_alert_classes(compute_poll_results(poll), rng=rng)
