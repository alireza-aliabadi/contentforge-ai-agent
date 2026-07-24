"""Multi-agent content pipeline orchestration."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from backend.core.config import Settings, get_settings
from backend.models.entities import Platform
from backend.services.ai_client import AIClient, clamp01, extract_json_object
from backend.services.platforms import get_platform

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    prompt: str
    platform: Platform
    document_context: str = ""
    image_context: str = ""
    plan: dict[str, Any] = field(default_factory=dict)
    draft_title: str = ""
    draft_body: str = ""
    evaluation: dict[str, Any] = field(default_factory=dict)
    banner_prompt: str = ""
    banner_result: dict[str, Any] = field(default_factory=dict)
    history: list[str] = field(default_factory=list)


class PlannerAgent:
    def __init__(self, client: AIClient) -> None:
        self.client = client

    async def run(self, ctx: AgentContext) -> AgentContext:
        profile = get_platform(ctx.platform)
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a Content Planning Agent. Return JSON with keys: "
                    "angle, structure (list), tone, audience."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Platform: {profile.label}\nStyle: {profile.style_notes}\n"
                    f"Prompt: {ctx.prompt}\n"
                    f"Documents:\n{ctx.document_context[:4000]}\n"
                    f"Images:\n{ctx.image_context[:2000]}\n"
                    "Create a content plan outline."
                ),
            },
        ]
        raw = await self.client.chat(messages, temperature=0.4)
        plan = extract_json_object(raw) or {
            "angle": "Expert practical insight",
            "structure": ["Hook", "Context", "Insights", "CTA"],
            "tone": "professional",
            "audience": "intermediate practitioners",
            "raw": raw,
        }
        ctx.plan = plan
        ctx.history.append("planner")
        return ctx


class WriterAgent:
    def __init__(self, client: AIClient) -> None:
        self.client = client

    async def run(self, ctx: AgentContext) -> AgentContext:
        profile = get_platform(ctx.platform)
        length_hint = (
            f"Stay under {profile.max_length} characters."
            if profile.max_length
            else "Use long-form structure with headings."
        )
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a Writer Agent. Produce platform-optimized content. "
                    "Start with a short title line prefixed with 'TITLE:', then the body."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Platform: {profile.label}\n{length_hint}\nStyle: {profile.style_notes}\n"
                    f"Plan: {json.dumps(ctx.plan)}\nPrompt: {ctx.prompt}\n"
                    f"Document grounding:\n{ctx.document_context[:5000]}\n"
                    f"Image grounding:\n{ctx.image_context[:2000]}"
                ),
            },
        ]
        raw = await self.client.chat(messages, temperature=0.7, max_tokens=3000)
        title, body = _split_title_body(raw, fallback_title=ctx.prompt[:80])
        if profile.max_length and len(body) > profile.max_length:
            body = body[: profile.max_length - 1].rstrip() + "…"
        ctx.draft_title = title
        ctx.draft_body = body
        ctx.history.append("writer")
        return ctx


class OriginalityEvaluator:
    def __init__(self, client: AIClient) -> None:
        self.client = client

    async def score(self, text: str, prior_texts: list[str] | None = None) -> float:
        corpus = prior_texts or [
            "Generic motivational social media post about hustle culture.",
            "Clickbait listicle without evidence or actionable depth.",
        ]
        embeddings = await self.client.embed([text, *corpus])
        target = embeddings[0]
        max_sim = max(
            (self.client.cosine_similarity(target, other) for other in embeddings[1:]),
            default=0.0,
        )
        # High similarity to generic corpus => lower originality
        return clamp01(1.0 - max(0.0, max_sim))


class ExpertiseEvaluator:
    def __init__(self, client: AIClient) -> None:
        self.client = client

    async def score(self, text: str, prompt: str) -> tuple[float, list[str]]:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an Expertise Evaluator. Score intermediate-to-advanced skill level. "
                    "Return JSON: expertise (0-1), feedback (list of strings)."
                ),
            },
            {
                "role": "user",
                "content": f"Prompt: {prompt}\nContent:\n{text}\nEvaluate technical depth.",
            },
        ]
        raw = await self.client.chat(messages, temperature=0.2)
        data = extract_json_object(raw) or {}
        score = clamp01(float(data.get("expertise", 0.85)))
        feedback = data.get("feedback") or []
        if not isinstance(feedback, list):
            feedback = [str(feedback)]
        return score, [str(item) for item in feedback]


class RelevanceEvaluator:
    def __init__(self, client: AIClient) -> None:
        self.client = client

    async def score(self, text: str, prompt: str, grounding: str) -> float:
        embeddings = await self.client.embed([text, f"{prompt}\n{grounding}"])
        return clamp01(self.client.cosine_similarity(embeddings[0], embeddings[1]))


class EvaluationAgent:
    def __init__(self, client: AIClient, settings: Settings) -> None:
        self.originality = OriginalityEvaluator(client)
        self.expertise = ExpertiseEvaluator(client)
        self.relevance = RelevanceEvaluator(client)
        self.settings = settings

    async def run(self, ctx: AgentContext) -> AgentContext:
        grounding = f"{ctx.document_context}\n{ctx.image_context}"
        originality = await self.originality.score(ctx.draft_body)
        relevance = await self.relevance.score(ctx.draft_body, ctx.prompt, grounding)
        expertise, expertise_feedback = await self.expertise.score(ctx.draft_body, ctx.prompt)
        passed = (
            originality >= self.settings.originality_threshold
            and relevance >= self.settings.relevance_threshold
            and expertise >= 0.7
        )
        feedback = list(expertise_feedback)
        if originality < self.settings.originality_threshold:
            feedback.append("Increase originality; avoid generic phrasing.")
        if relevance < self.settings.relevance_threshold:
            feedback.append("Improve alignment with prompt and attachments.")
        ctx.evaluation = {
            "originality": originality,
            "relevance": relevance,
            "expertise": expertise,
            "passed": passed,
            "feedback": feedback,
            "thresholds": {
                "originality": self.settings.originality_threshold,
                "relevance": self.settings.relevance_threshold,
            },
        }
        ctx.history.append("evaluation")
        return ctx


class OptimizationAgent:
    def __init__(self, client: AIClient) -> None:
        self.client = client

    async def run(self, ctx: AgentContext, instructions: str | None = None) -> AgentContext:
        profile = get_platform(ctx.platform)
        feedback = ctx.evaluation.get("feedback", [])
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an Optimization Agent. Improve the draft using evaluation feedback. "
                    "Return TITLE: then body."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Platform: {profile.label}\nFeedback: {feedback}\n"
                    f"Extra instructions: {instructions or 'n/a'}\n"
                    f"Current title: {ctx.draft_title}\nCurrent body:\n{ctx.draft_body}"
                ),
            },
        ]
        raw = await self.client.chat(messages, temperature=0.5)
        title, body = _split_title_body(raw, fallback_title=ctx.draft_title)
        ctx.draft_title = title
        ctx.draft_body = body
        ctx.history.append("optimizer")
        return ctx


class BannerAgent:
    def __init__(self, client: AIClient) -> None:
        self.client = client

    async def run(self, ctx: AgentContext) -> AgentContext:
        profile = get_platform(ctx.platform)
        size = _banner_size(ctx.platform)
        prompt_messages = [
            {
                "role": "system",
                "content": "You write concise image-generation prompts for content banners.",
            },
            {
                "role": "user",
                "content": (
                    f"Platform: {profile.label}\nTitle: {ctx.draft_title}\n"
                    f"Body excerpt: {ctx.draft_body[:400]}\n"
                    "Write one banner prompt."
                ),
            },
        ]
        banner_prompt = await self.client.chat(prompt_messages, temperature=0.6, max_tokens=200)
        result = await self.client.generate_image(banner_prompt.strip(), size=size)
        ctx.banner_prompt = banner_prompt.strip()
        ctx.banner_result = result
        ctx.history.append("banner")
        return ctx


class ContentPipeline:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.client = AIClient(self.settings)
        self.planner = PlannerAgent(self.client)
        self.writer = WriterAgent(self.client)
        self.evaluator = EvaluationAgent(self.client, self.settings)
        self.optimizer = OptimizationAgent(self.client)
        self.banner = BannerAgent(self.client)

    async def run(
        self,
        prompt: str,
        platform: Platform,
        document_context: str = "",
        image_context: str = "",
    ) -> AgentContext:
        ctx = AgentContext(
            prompt=prompt,
            platform=platform,
            document_context=document_context,
            image_context=image_context,
        )
        ctx = await self.planner.run(ctx)
        ctx = await self.writer.run(ctx)

        for _ in range(self.settings.max_regeneration_loops):
            ctx = await self.evaluator.run(ctx)
            if ctx.evaluation.get("passed"):
                break
            ctx = await self.optimizer.run(ctx)

        # Final evaluation after last improvement attempt
        if not ctx.evaluation.get("passed"):
            ctx = await self.evaluator.run(ctx)

        ctx = await self.banner.run(ctx)
        return ctx


def _split_title_body(raw: str, fallback_title: str) -> tuple[str, str]:
    lines = [line.rstrip() for line in raw.strip().splitlines()]
    title = fallback_title
    body_lines = lines
    if lines:
        first = lines[0].strip()
        if first.lower().startswith("title:"):
            title = first.split(":", 1)[1].strip() or fallback_title
            body_lines = lines[1:]
        elif first.startswith("# "):
            title = first[2:].strip() or fallback_title
            body_lines = lines[1:]
    body = "\n".join(body_lines).strip() or raw.strip()
    return title[:512], body


def _banner_size(platform: Platform) -> str:
    sizes = {
        Platform.LINKEDIN: "1792x1024",
        Platform.TWITTER: "1792x1024",
        Platform.BLOG: "1792x1024",
        Platform.MEDIUM: "1792x1024",
        Platform.YOUTUBE_COMMUNITY: "1792x1024",
        Platform.CUSTOM: "1024x1024",
    }
    return sizes[platform]
