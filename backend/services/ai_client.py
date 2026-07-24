"""External AI API client with mock fallback."""

from __future__ import annotations

import hashlib
import logging
import math
import re
from typing import Any

import httpx
import numpy as np

from backend.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class AIClient:
    """Talks to external LLM / vision / embedding / image APIs. Never loads local models."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        if self.settings.use_mock_ai or not self.settings.llm_api_key:
            return self._mock_chat(messages)

        headers = {
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.settings.llm_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.settings.llm_api_base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def describe_image(self, image_b64: str, prompt: str) -> str:
        if self.settings.use_mock_ai or not (
            self.settings.vision_api_key or self.settings.llm_api_key
        ):
            return (
                "Mock vision analysis: image appears professional with clear subject focus, "
                "suitable for social content. Dominant colors are cool blues and neutrals."
            )

        api_key = self.settings.vision_api_key or self.settings.llm_api_key
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.settings.vision_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                        },
                    ],
                }
            ],
            "max_tokens": 512,
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.settings.vision_api_base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if self.settings.use_mock_ai or not (
            self.settings.embedding_api_key or self.settings.llm_api_key
        ):
            return [self._mock_embedding(text) for text in texts]

        api_key = self.settings.embedding_api_key or self.settings.llm_api_key
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": self.settings.embedding_model, "input": texts}
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.settings.embedding_api_base_url.rstrip('/')}/embeddings",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return [item["embedding"] for item in data["data"]]

    async def generate_image(self, prompt: str, size: str = "1792x1024") -> dict[str, Any]:
        if self.settings.use_mock_ai or not (
            self.settings.image_gen_api_key or self.settings.llm_api_key
        ):
            return {
                "mock": True,
                "prompt": prompt,
                "size": size,
                "url": None,
                "b64_json": None,
            }

        api_key = self.settings.image_gen_api_key or self.settings.llm_api_key
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.settings.image_gen_model,
            "prompt": prompt,
            "size": size,
            "n": 1,
            "response_format": "b64_json",
        }
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{self.settings.image_gen_api_base_url.rstrip('/')}/images/generations",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            item = data["data"][0]
            return {
                "mock": False,
                "prompt": prompt,
                "size": size,
                "url": item.get("url"),
                "b64_json": item.get("b64_json"),
            }

    @staticmethod
    def cosine_similarity(a: list[float], b: list[float]) -> float:
        va = np.asarray(a, dtype=np.float64)
        vb = np.asarray(b, dtype=np.float64)
        denom = float(np.linalg.norm(va) * np.linalg.norm(vb))
        if denom == 0:
            return 0.0
        return float(np.dot(va, vb) / denom)

    def _mock_chat(self, messages: list[dict[str, str]]) -> str:
        user_msgs = [m["content"] for m in messages if m.get("role") == "user"]
        joined = "\n".join(user_msgs).lower()
        if "plan" in joined or "outline" in joined:
            return (
                '{"angle":"Practical expert insight","structure":'
                '["Hook","Context","Key takeaways","CTA"],'
                '"tone":"authoritative yet approachable","audience":"intermediate practitioners"}'
            )
        if "evaluate" in joined or "score" in joined:
            return (
                '{"originality":0.94,"relevance":0.93,"expertise":0.88,'
                '"feedback":["Strong technical depth","Clear platform fit"]}'
            )
        if "improve" in joined or "optimize" in joined:
            base = user_msgs[-1] if user_msgs else "Content"
            return (
                f"Improved draft:\n\n{base[:500]}\n\n"
                "Key refinements: sharper opening hook, denser examples, "
                "clearer CTA aligned to platform norms."
            )
        if "banner" in joined:
            return (
                "Create a clean professional banner with bold title "
                "and subtle geometric accents."
            )
        prompt_snip = user_msgs[-1][:180] if user_msgs else "your topic"
        return (
            f"# Platform-ready draft\n\n{prompt_snip}\n\n"
            "Practitioners often underestimate the compounding effect of deliberate iteration. "
            "Start with a crisp thesis, ground claims in concrete evidence from your attachments, "
            "then translate insights into actionable steps your audience can apply this week.\n\n"
            "Three takeaways:\n"
            "1. Prioritize clarity over novelty theater.\n"
            "2. Cite grounding material from uploaded sources.\n"
            "3. End with a specific next action.\n\n"
            "What will you ship first?"
        )

    @staticmethod
    def _mock_embedding(text: str) -> list[float]:
        digest = hashlib.sha256(text.encode()).digest()
        rng = np.random.default_rng(int.from_bytes(digest[:8], "little"))
        vec = rng.normal(size=64)
        norm = float(np.linalg.norm(vec)) or 1.0
        return (vec / norm).tolist()


def extract_json_object(text: str) -> dict[str, Any] | None:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    import json

    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def clamp01(value: float) -> float:
    if math.isnan(value):
        return 0.0
    return max(0.0, min(1.0, value))
