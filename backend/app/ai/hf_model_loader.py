"""
Hugging Face model loader and inference service.
Supports both local model loading and API-based inference.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Module-level model cache ─────────────────────────────────
_pipeline_cache = None


class HFModelLoader:
    """
    Manages Hugging Face model loading and text generation.
    Supports two modes:
      1. API mode (HF Inference API) — lightweight, no GPU needed
      2. Local mode — loads model into memory with transformers
    """

    def __init__(self):
        self.model_name = settings.hf_model_name
        self.use_api = settings.hf_use_api
        self.api_token = settings.hf_api_token
        base = settings.hf_api_url.rstrip("/")
        # OpenAI-compatible router uses /chat/completions endpoint
        if "router.huggingface.co/v1" in base:
            self.api_url = f"{base}/chat/completions"
            self.use_openai_format = True
        else:
            self.api_url = f"{base}/{self.model_name}"
            self.use_openai_format = False

    # ── API-based Inference ──────────────────────────────────
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def generate_via_api(
        self,
        prompt: str,
        max_new_tokens: int = 2048,
        temperature: float = 0.3,
        top_p: float = 0.9,
    ) -> str:
        """Call Hugging Face router API for text generation."""
        headers = {"Content-Type": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        if self.use_openai_format:
            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_new_tokens,
                "temperature": temperature,
                "top_p": top_p,
            }
        else:
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": max_new_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                    "do_sample": True,
                    "return_full_text": False,
                },
            }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                self.api_url,
                json=payload,
                headers=headers,
            )
            if not response.is_success:
                logger.error(
                    f"HF API error {response.status_code} for {self.api_url}: {response.text[:300]}"
                )
            response.raise_for_status()

        result = response.json()

        # OpenAI-compatible response format
        if self.use_openai_format:
            return result["choices"][0]["message"]["content"]

        # Legacy response formats
        if isinstance(result, list) and len(result) > 0:
            return result[0].get("generated_text", "")
        elif isinstance(result, dict):
            return result.get("generated_text", "")

        logger.warning(f"Unexpected API response format: {type(result)}")
        return str(result)

    # ── Local Model Inference ────────────────────────────────
    def _load_local_pipeline(self):
        """Lazily load the model pipeline into memory."""
        global _pipeline_cache
        if _pipeline_cache is not None:
            return _pipeline_cache

        logger.info(f"Loading model locally: {self.model_name}")

        from transformers import pipeline

        if "t5" in self.model_name.lower():
            _pipeline_cache = pipeline(
                "text2text-generation",
                model=self.model_name,
                device_map="auto",
            )
        else:
            _pipeline_cache = pipeline(
                "text-generation",
                model=self.model_name,
                device_map="auto",
            )

        logger.info("Model loaded successfully")
        return _pipeline_cache

    def generate_local(
        self,
        prompt: str,
        max_new_tokens: int = 2048,
        temperature: float = 0.3,
    ) -> str:
        """Generate text using locally loaded model."""
        pipe = self._load_local_pipeline()

        result = pipe(
            prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=True,
            top_p=0.9,
        )

        if isinstance(result, list) and len(result) > 0:
            text = result[0].get("generated_text", "")
            # For causal LM, strip the prompt from output
            if text.startswith(prompt):
                text = text[len(prompt):]
            return text.strip()

        return str(result)

    # ── Unified Generate ─────────────────────────────────────
    async def generate(
        self,
        prompt: str,
        max_new_tokens: int = 2048,
        temperature: float = 0.3,
    ) -> str:
        """
        Generate text using either API or local model.
        Falls back to local if API fails.
        """
        if self.use_api:
            try:
                return await self.generate_via_api(
                    prompt, max_new_tokens, temperature
                )
            except Exception as e:
                logger.warning(f"API inference failed: {e}. Falling back to local.")
                return self.generate_local(prompt, max_new_tokens, temperature)
        else:
            return self.generate_local(prompt, max_new_tokens, temperature)


def parse_json_response(text: str) -> Any:
    """
    Robustly extract JSON from LLM output.
    Handles common issues like markdown fences, trailing text, etc.
    """
    # Strip markdown code fences
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON array or object
    for pattern in [
        r"\[[\s\S]*\]",   # JSON array
        r"\{[\s\S]*\}",   # JSON object
    ]:
        match = re.search(pattern, text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                continue

    logger.error(f"Failed to parse JSON from LLM output: {text[:200]}")
    return None


# ── Singleton accessor ───────────────────────────────────────
_model_loader: Optional[HFModelLoader] = None


def get_model_loader() -> HFModelLoader:
    """Return a singleton HFModelLoader instance."""
    global _model_loader
    if _model_loader is None:
        _model_loader = HFModelLoader()
    return _model_loader
