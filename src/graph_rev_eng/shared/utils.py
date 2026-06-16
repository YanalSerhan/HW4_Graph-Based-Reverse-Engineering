"""
Utility functions shared across the SDK and services.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def safe_execute(
    func: Callable[..., T],
    *args: Any,
    error_list: list[str] | None = None,
    default_return: T | None = None,
    error_message_prefix: str = "Execution failed",
    **kwargs: Any,
) -> T | None:
    """
    Safely executes a function, catching exceptions and appending them to an error list.

    Args:
        func: The function to execute.
        *args: Positional arguments to pass to the function.
        error_list: A list to append error messages to.
        default_return: The value to return if an exception occurs.
        error_message_prefix: Prefix for the error message in logs and the error_list.
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        The result of the function call, or `default_return` if an exception occurred.
    """
    try:
        return func(*args, **kwargs)
    except Exception as exc:
        msg = f"{error_message_prefix}: {exc}"
        if error_list is not None:
            error_list.append(msg)
        logger.error(msg)
        return default_return
