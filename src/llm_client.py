# Provider-agnostic minimal client for OpenAI or Anthropic.
# Env:
#   PROVIDER=openai|anthropic
#   OPENAI_API_KEY=...   or   ANTHROPIC_API_KEY=...
from __future__ import annotations
import os
import json
from dataclasses import dataclass

@dataclass
class LLMConfig:
    provider: str = os.getenv("PROVIDER", "openai").lower()
    model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "16000"))

class LLMClient:
    def __init__(self, cfg: LLMConfig = LLMConfig()):
        self.cfg = cfg
        self._init_clients()

    def _init_clients(self):
        self.openai_client = self.anthropic = None
        if self.cfg.provider == "openai":
            # OpenAI python SDK >= 1.0 uses the client pattern
            from openai import OpenAI
            # Uses OPENAI_API_KEY from environment
            self.openai_client = OpenAI()
        elif self.cfg.provider == "anthropic":
            import anthropic
            self.anthropic = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        else:
            raise ValueError("Unsupported PROVIDER (use 'openai' or 'anthropic').")

    def chat_json(self, system: str, user: str) -> dict:
        """Return parsed JSON dict; raises on parse failure."""
        if self.cfg.provider == "openai":
            resp = self.openai_client.chat.completions.create(
                model=self.cfg.model,
                temperature=self.cfg.temperature,
                messages=[{"role":"system","content":system},{"role":"user","content":user}],
                response_format={"type": "json_object"},
                max_tokens=self.cfg.max_tokens,
            )
            text = resp.choices[0].message.content
            return json.loads(text)
        else:  # anthropic
            msg = self.anthropic.messages.create(
                model=self.cfg.model,
                max_tokens=self.cfg.max_tokens,
                temperature=self.cfg.temperature,
                system=system,
                messages=[{"role":"user","content":user}],
            )
            # Claude returns content as a list of parts; expect a single text part
            text = "".join([p.text for p in msg.content if hasattr(p, "text")])
            return json.loads(text)