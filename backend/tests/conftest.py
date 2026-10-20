import pytest

import main


@pytest.fixture(autouse=True)
def _fresh_abuse_counters():
    """Each test starts with empty rate-limit and duplicate-submission memory."""
    main._recent_requests.clear()
    main._last_submission.clear()
    yield
