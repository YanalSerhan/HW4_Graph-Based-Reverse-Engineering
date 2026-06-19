"""
OpenAI LLM wrapper to be used with ApiGatekeeper.
"""

import json
import logging
import urllib.error
import urllib.request
from typing import Any

from langchain_core.language_models.llms import LLM
from pydantic import Field

from ..shared.config import ConfigManager
from ..shared.gatekeeper import ApiGatekeeper

logger = logging.getLogger(__name__)


class LLMResponse:
    """Response object compatible with ApiGatekeeper's expected structure."""

    def __init__(self, text: str, model: str, input_tokens: int, output_tokens: int):
        self.text = text
        self.model = model
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cost = self._estimate_cost(model, input_tokens, output_tokens)

    def _estimate_cost(self, model: str, in_toks: int, out_toks: int) -> float:
        """
        Estimate the financial cost of the LLM call.

        Why: We need to proactively track and estimate API costs before billing to stay
        within our configured token budgets and ensure the pipeline remains cost-effective.
        """
        if model.startswith("gpt-4o-mini"):
            return (in_toks / 1_000_000) * 0.150 + (out_toks / 1_000_000) * 0.600
        elif model.startswith("gpt-4o"):
            return (in_toks / 1_000_000) * 5.0 + (out_toks / 1_000_000) * 15.0
        return 0.0

    def __str__(self) -> str:
        return self.text


class OpenAILLM:
    """OpenAI API wrapper designed to be routed through ApiGatekeeper."""

    def __init__(self, gatekeeper: ApiGatekeeper, api_key: str, model: str = "gpt-4o-mini"):
        self.gatekeeper = gatekeeper
        self.api_key = api_key
        self.model = model

    def __call__(self, prompt: str) -> str:
        """Executes the LLM request via the gatekeeper and returns the text."""
        if not self.api_key:
            logger.warning("No LLM_API_KEY provided. Returning stub.")
            return f"[STUB] Missing API Key. Prompt length: {len(prompt)}"

        def _api_call() -> LLMResponse:
            url = ConfigManager.get_instance().get_api_url()
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
            }
            req = urllib.request.Request(
                url, data=json.dumps(data).encode("utf-8"), headers=headers
            )
            try:
                with urllib.request.urlopen(req) as response:
                    res_body = response.read().decode("utf-8")
                    res_json = json.loads(res_body)

                    text = res_json["choices"][0]["message"]["content"]
                    usage = res_json.get("usage", {})
                    in_toks = usage.get("prompt_tokens", 0)
                    out_toks = usage.get("completion_tokens", 0)
                    return LLMResponse(text, self.model, in_toks, out_toks)
            except urllib.error.HTTPError as e:
                err_msg = e.read().decode("utf-8")
                logger.error("OpenAI API HTTPError: %s", err_msg)
                raise

        # Execute through gatekeeper to enforce rate limits
        response = self.gatekeeper.execute(_api_call)
        return response.text


class GatekeeperLangchainLLM(LLM):
    """
    Langchain LLM wrapper that routes calls through ApiGatekeeper.

    Why: Adapts standard Langchain components to our custom rate-limited environment,
    ensuring third-party library compatibility while respecting our gatekeeper rules.
    """
    gatekeeper: Any = Field(exclude=True)
    openai_api_key: str
    model_name: str = "gpt-4o-mini"

    @property
    def _llm_type(self) -> str:
        return "custom_gatekeeper_llm"

    def _call(
        self,
        prompt: str,
        stop: list[str] | None = None,
        run_manager: Any | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Internal Langchain call implementation.

        Why: We intercept standard Langchain execution to force all LLM interactions
        through the central Gatekeeper for rate limit enforcement.
        """
        wrapper = OpenAILLM(self.gatekeeper, self.openai_api_key, self.model_name)
        return wrapper(prompt)

    def __call__(self, prompt: str, **kwargs: Any) -> str:
        """
        Direct callable implementation.

        Why: Provides a simplified direct invocation method identical to the Langchain interface.
        """
        return self._call(prompt, **kwargs)
