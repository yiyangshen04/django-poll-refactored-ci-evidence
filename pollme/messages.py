"""
Shared Bootstrap-flavoured tag strings for ``django.contrib.messages``.

Extracted from ``polls/views.py`` and ``accounts/views.py`` where the same
literal strings were copy-pasted into every ``messages.success``/
``messages.error`` call. Centralising them removes duplication and makes
the tag values trivially assertable from tests.
"""

WARNING_TAGS = "alert alert-warning alert-dismissible fade show"
SUCCESS_TAGS = "alert alert-success alert-dismissible fade show"
