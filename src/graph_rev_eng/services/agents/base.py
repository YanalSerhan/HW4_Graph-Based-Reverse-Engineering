"""
Base classes and mixins for the agent architecture.
Follows the Template Method and Mixin design patterns.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from ..token_counter import TokenCounter

logger = logging.getLogger(__name__)

T_In = TypeVar("T_In")
T_Out = TypeVar("T_Out")


class BaseAgent(ABC, Generic[T_In, T_Out]):
    """
    Abstract base class for all agents.

    Implements the Modular "Building Blocks" paradigm:
    Strictly separates Data Setup, Data Processing, and Data Output.
    Follows the Template Method pattern via the `run()` method.
    """

    def __init__(self, token_counter: TokenCounter, token_budget: int = 2000) -> None:
        self._counter = token_counter
        self._budget = token_budget

    def run(self, *args: Any, **kwargs: Any) -> T_Out:
        """
        Template method that dictates the execution flow of the agent.
        """
        setup_data = self.setup(*args, **kwargs)
        processed_data = self.process(setup_data)
        return self.format_output(processed_data)

    @abstractmethod
    def setup(self, *args: Any, **kwargs: Any) -> T_In:
        """
        Prepares the data for processing.
        """
        pass

    @abstractmethod
    def process(self, data: T_In) -> Any:
        """
        Processes the data. Core business logic goes here.
        """
        pass

    @abstractmethod
    def format_output(self, data: Any) -> T_Out:
        """
        Formats the output into the final expected shape.
        """
        pass


class LLMStubMixin:
    """
    Mixin that provides a deterministic default LLM stub for testing.
    Ensures single responsibility and prevents duplicated try/except
    or stub logic across agents.
    """

    def _default_llm_stub(self, prompt: str) -> str:
        """Deterministic stub for environments without LLM access."""
        return f"[STUB] Operation pending LLM. ({len(prompt)} chars)"
