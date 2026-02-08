# Helpers for install phases. Phases use these to report into shared state.
from helpers.errors import record_error
from helpers.logging import append_log

__all__ = ["record_error", "append_log"]
