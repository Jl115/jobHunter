"""Concrete LLM-based job extractor using llama-cpp-python."""

import logging
from typing import cast

from llama_cpp import Llama

from shared.models import Job
from .contracts import IJobExtractor
from .model_manager import ModelManager
from .prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class LlamaJobExtractor(IJobExtractor):
    """Extract structured job fields using a local GGUF model."""

    def __init__(
        self,
        model_manager: ModelManager,
        prompt_builder: PromptBuilder,
        n_ctx: int = 4096,
        max_tokens: int = 1024,
    ) -> None:
        self.model_manager = model_manager
        self.prompt_builder = prompt_builder
        self.n_ctx = n_ctx
        self.max_tokens = max_tokens
        self._llm: Llama | None = None

    def _load_model(self) -> Llama:
        """Lazy-load the Llama model from cache."""
        if self._llm is None:
            model_path = self.model_manager.get_gguf_model_path()
            logger.info("Loading GGUF model from %s", model_path)
            self._llm = Llama(
                model_path=str(model_path),
                n_ctx=self.n_ctx,
                verbose=False,
            )
        return self._llm

    def infer(self, system_prompt: str, user_prompt: str) -> dict:
        """Run a single inference call and return the parsed JSON dict."""
        llm = self._load_model()

        output = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=self.max_tokens,
            temperature=0.2,
        )

        response_text = cast(str, output["choices"][0]["message"]["content"])
        logger.info("(first 300 chars): %s", response_text[:300].replace('\n', ' '))
        return self.prompt_builder.parse_response(response_text)

    def extract(self, raw_html: str) -> Job:
        """Run inference and parse structured fields from raw HTML."""
        system_prompt = self.prompt_builder.SYSTEM_PROMPT
        user_prompt = self.prompt_builder.build_user_prompt(raw_html)
        parsed = self.infer(system_prompt, user_prompt)

        return Job(
            url="",  # populated by caller
            source="",  # populated by caller
            title=parsed.get("title"),
            company=parsed.get("company"),
            location=parsed.get("location"),
            description=parsed.get("description"),
            raw_html=raw_html,
            scraped_at=None,  # type: ignore[arg-type]  # populated by caller
        )
