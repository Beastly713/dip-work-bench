import threading

import pytest

from dip_workbench.core import CancelledOperation
from dip_workbench.execution import CancellationToken


def test_cancellation_is_idempotent_and_visible_cross_thread() -> None:
    token = CancellationToken()
    assert not token.is_cancelled
    thread = threading.Thread(target=token.cancel)
    thread.start()
    thread.join()
    token.cancel()
    assert token.is_cancelled
    with pytest.raises(CancelledOperation):
        token.raise_if_cancelled()
