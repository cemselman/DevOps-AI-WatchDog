"""Provide a small shared wrapper around the OpenAI client."""

from __future__ import annotations

import logging

from openai import APIConnectionError, APITimeoutError, OpenAI, RateLimitError

log = logging.getLogger("watchdog.llm")


class LLMClient:
    def __init__(self, api_key: str, model: str) -> None:
        """Create one reusable OpenAI client for both agents."""
        if not api_key or api_key == "your_openai_api_key_here":
            raise ValueError(
                "OPENAI_API_KEY is missing. Put your real key into the .env file."
            )

        self.model = model
        self.client = OpenAI(api_key=api_key)

    def ask(self, system_prompt: str, user_prompt: str) -> str:
        """Send one prompt pair and return plain text output.

        Catches transient API errors and returns a short fallback message
        so one failed call does not crash the entire pipeline.
        """
        try:
            response = self.client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response.output_text.strip()
        except APIConnectionError:
            log.warning("Could not connect to the OpenAI API.")
            return "[LLM error] Could not connect to the OpenAI API."
        except APITimeoutError:
            log.warning("OpenAI API request timed out.")
            return "[LLM error] OpenAI API request timed out."
        except RateLimitError:
            log.warning("Rate limit exceeded.")
            return "[LLM error] Rate limit exceeded. Try again later."
        except Exception as exc:  # noqa: BLE001
            log.exception("Unexpected API failure: %s", exc)
            return f"[LLM error] Unexpected API failure: {exc}"
