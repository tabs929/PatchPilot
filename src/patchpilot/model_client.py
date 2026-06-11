"""Thin Anthropic client wrapper with retries and token/cost accounting."""

from __future__ import annotations

from dataclasses import dataclass, field

import anthropic
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from . import config


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    calls: int = 0

    def add(self, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.calls += 1


_RETRYABLE = (
    anthropic.RateLimitError,
    anthropic.APIConnectionError,
    anthropic.InternalServerError,
)


class ModelClient:
    def __init__(self, model: str | None = None, api_key: str | None = None) -> None:
        self.model = model or config.DEFAULT_MODEL
        key = api_key or config.ANTHROPIC_API_KEY
        if not key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Add it to your .env (see .env.example)."
            )
        self.client = anthropic.Anthropic(api_key=key)
        self.usage = Usage()

    @retry(
        retry=retry_if_exception_type(_RETRYABLE),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=2, max=60),
        reraise=True,
    )
    def complete(self, system: str, user: str, max_tokens: int | None = None) -> str:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens or config.MAX_OUTPUT_TOKENS,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        self.usage.add(resp.usage.input_tokens, resp.usage.output_tokens)
        return "".join(block.text for block in resp.content if getattr(block, "type", None) == "text")

    @property
    def cost_usd(self) -> float:
        in_price, out_price = config.price_for(self.model)
        return (
            self.usage.input_tokens / 1_000_000 * in_price
            + self.usage.output_tokens / 1_000_000 * out_price
        )

    def usage_summary(self) -> str:
        return (
            f"model={self.model} calls={self.usage.calls} "
            f"in={self.usage.input_tokens} out={self.usage.output_tokens} "
            f"cost=${self.cost_usd:.4f}"
        )
