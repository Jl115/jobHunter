"""Prompt builder for LLM-based job field extraction."""

import html
import json
import re


class PromptBuilder:
    """Constructs system and user prompts for the local LLM."""

    SYSTEM_PROMPT: str = (
        "You are a job posting parser. "
        "Extract exactly 4 fields from the job posting and return ONLY a JSON object.\n"
        "Fields: title, company, location, description.\n"
        "If a field is missing, use null.\n"
        "No markdown, no explanation, only JSON."
    )

    JSON_EXAMPLE: str = (
        '{"title": "Software Engineer", "company": "Acme Corp", "location": "Berlin", "description": "Build web apps"}'
    )

    def build_user_prompt(self, raw_html: str) -> str:
        """Strip HTML tags, truncate to fit model context, and wrap in a prompt."""
        text = self._strip_html_tags(raw_html)
        # A 3B model can handle ~2000 chars of input text at Q4_K_M in a 4096-token context.
        MAX_CHARS = 1800
        text = text[:MAX_CHARS]
        return (
            f"Extract the 4 fields as JSON.\n"
            f"{text}\n\n"
            f"JSON:"
        )

    def parse_response(self, response_text: str) -> dict:
        """Sanitize, parse, and validate the LLM response into a dict.

        Returns an empty dict if parsing fails so the caller can fall back.
        """
        cleaned = response_text.strip()

        # Strip markdown code fences
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # Try direct JSON first
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return self._normalize(parsed)
        except json.JSONDecodeError:
            pass

        # Extract first balanced JSON object via regex
        json_match = self._extract_json(cleaned)
        if json_match:
            try:
                parsed = json.loads(json_match)
                if isinstance(parsed, dict):
                    return self._normalize(parsed)
            except json.JSONDecodeError:
                pass

        return {}

    @staticmethod
    def _extract_json(text: str) -> str | None:
        """Extract the first balanced JSON object string from text."""
        # Find first opening brace
        start = text.find("{")
        if start == -1:
            return None

        depth = 0
        in_string = False
        escape = False
        for i, ch in enumerate(text[start:], start=start):
            if escape:
                escape = False
                continue
            if ch == "\\" and in_string:
                escape = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
        return None

    @staticmethod
    def _normalize(parsed: dict) -> dict:
        """Accept multiple possible keys (incl. German variants) from a small model."""
        lc = {str(k).lower().strip().replace(" ", "_"): v for k, v in parsed.items()}

        def _first(keys: list[str], default=None):
            for k in keys:
                if k in lc and lc[k] is not None:
                    return lc[k]
            return default

        title = _first(["title", "job_title", "position", "stelle", "job title", "titel"])
        company = _first(["company", "employer", "company_name", "firma", "arbeitgeber", "unternehmen", "company name"])
        location = _first(["location", "ort", "stadt", "standort", "place", "city"])
        description = _first(["description", "job_description", "beschreibung", "aufgaben", "text", "job description", "details"])

        return {
            "title": title,
            "company": company,
            "location": location,
            "description": description,
        }

    @staticmethod
    def _strip_html_tags(raw_html: str) -> str:
        """Remove HTML tags and unescape entities from raw HTML."""
        # Remove tags
        text = re.sub(r"<[^>]+>", " ", raw_html)
        # Collapse excess whitespace
        text = re.sub(r"\s+", " ", text)
        # Unescape entities (&amp; → &, etc.)
        text = html.unescape(text)
        return text.strip()
