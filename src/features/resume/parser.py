"""LLM-based structured resume parsing.

Reuses the public ``ModelManager`` and ``PromptBuilder`` interfaces
from ``features.job_extraction`` to avoid importing internal modules.
"""

import json
import logging
from typing import cast

from llama_cpp import Llama

from features.job_extraction import ModelManager, PromptBuilder
from shared.models import Resume

logger = logging.getLogger(__name__)


class ResumeParser:
    """Parse a resume into structured fields using the local LLM."""

    SYSTEM_PROMPT: str = (
        "You are a resume parser. Extract the following fields from the resume text:\n"
        "- skills: A list of technical and professional skills\n"
        "- experience: A list of previous job titles or roles\n\n"
        "Respond ONLY with a valid JSON object containing two keys: "
        "'skills' (list of strings) and 'experience' (list of strings). "
        "Do not include markdown formatting or extra text."
    )

    def __init__(
        self,
        model_manager: ModelManager | None = None,
        prompt_builder: PromptBuilder | None = None,
        n_ctx: int = 4096,
        max_tokens: int = 512,
    ) -> None:
        self.model_manager = model_manager or ModelManager()
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.n_ctx = n_ctx
        self.max_tokens = max_tokens
        self._llm: Llama | None = None

    def _load_model(self) -> Llama:
        """Lazy-load the Llama model (shared cache via ModelManager)."""
        if self._llm is None:
            model_path = self.model_manager.get_gguf_model_path()
            logger.info("Loading GGUF model for resume parsing from %s", model_path)
            self._llm = Llama(
                model_path=str(model_path),
                n_ctx=self.n_ctx,
                verbose=False,
            )
        return self._llm

    def parse(self, raw_text: str) -> Resume:
        """Run inference and parse structured fields from resume text."""
        llm = self._load_model()
        user_prompt = (
            f"Parse the following resume text and return JSON:\n\n"
            f"{raw_text[:6000]}\n\n"
            f"Remember: respond with ONLY a JSON object."
        )

        output = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=self.max_tokens,
            temperature=0.2,
        )

        response_text = cast(str, output["choices"][0]["message"]["content"])
        parsed = self._parse_json_response(response_text)

        return Resume(
            filename="",
            raw_text=raw_text,
            parsed_skills=parsed.get("skills", []),
            parsed_experience=parsed.get("experience", []),
        )

    @staticmethod
    def _parse_json_response(response_text: str) -> dict:
        """Sanitize and parse the LLM response."""
        cleaned = response_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        return json.loads(cleaned)
