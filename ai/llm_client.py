from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from config import BACKUP_AI_CONFIGS, GEMINI_AI_CONFIG, PRIMARY_AI_CONFIG
from utils.logger import get_logger

logger = get_logger("ai.llm_client")

try:
    from google import genai
except Exception:  # pragma: no cover - 运行环境可选依赖
    genai = None


class LLMClient:
    """统一封装 Gemini/OpenAI 的调用入口。"""

    def __init__(
        self,
        *,
        gemini_config: dict[str, Any] | None = None,
        primary_openai_config: dict[str, Any] | None = None,
        backup_openai_configs: list[dict[str, Any]] | None = None,
    ) -> None:
        self.gemini_config = gemini_config or GEMINI_AI_CONFIG
        self.primary_openai_config = primary_openai_config or PRIMARY_AI_CONFIG
        self.backup_openai_configs = backup_openai_configs or BACKUP_AI_CONFIGS

        self._primary_client = self._build_openai_client(self.primary_openai_config)
        self._backup_clients: list[tuple[OpenAI, dict[str, Any]]] = []
        for cfg in self.backup_openai_configs:
            client = self._build_openai_client(cfg)
            if client is not None:
                self._backup_clients.append((client, cfg))

        self.last_used_info: dict[str, Any] = {
            "provider": None,
            "model": None,
            "api_base": None,
            "is_backup": False,
        }

    @staticmethod
    def _build_openai_client(config: dict[str, Any] | None) -> OpenAI | None:
        if not config:
            return None
        api_key = str(config.get("api_key", "")).strip()
        api_base = str(config.get("api_base", "")).strip()
        if not api_key or not api_base:
            return None
        return OpenAI(api_key=api_key, base_url=api_base)

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any] | list[Any] | None:
        if not text:
            return None
        stripped = text.strip()
        if not stripped:
            return None
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            return None

    def _set_last_used_info(
        self,
        *,
        provider: str | None,
        model: str | None,
        api_base: str | None,
        is_backup: bool,
    ) -> None:
        self.last_used_info = {
            "provider": provider,
            "model": model,
            "api_base": api_base,
            "is_backup": is_backup,
        }

    def _call_gemini(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[Any] | None = None,
    ) -> dict[str, Any] | list[Any] | None:
        api_key = str(self.gemini_config.get("api_key", "")).strip()
        model = str(self.gemini_config.get("model", "")).strip()
        base_url = str(self.gemini_config.get("base_url", "")).strip()
        if not api_key or not model or genai is None:
            return None

        try:
            http_options = {"base_url": base_url} if base_url else None
            client = genai.Client(api_key=api_key, http_options=http_options)
            content = f"系统提示:\n{system_prompt}\n\n用户提示:\n{user_prompt}"
            config: dict[str, Any] = {"response_mime_type": "application/json"}
            if response_schema is not None:
                config["response_schema"] = response_schema

            response = client.models.generate_content(
                model=model,
                contents=content,
                config=config,
            )

            parsed = getattr(response, "parsed", None)
            if parsed is not None:
                if hasattr(parsed, "model_dump"):
                    result = parsed.model_dump()
                elif isinstance(parsed, (dict, list)):
                    result = parsed
                else:
                    result = None
            else:
                result = self._extract_json(getattr(response, "text", ""))

            if result is not None:
                self._set_last_used_info(
                    provider="gemini",
                    model=model,
                    api_base=base_url or None,
                    is_backup=False,
                )
                return result
        except Exception as exc:
            logger.warning("Gemini 调用失败: %s", str(exc))
        return None

    def _call_openai_client(
        self,
        client: OpenAI,
        config: dict[str, Any],
        *,
        system_prompt: str,
        user_prompt: str,
        is_backup: bool,
    ) -> dict[str, Any] | list[Any] | None:
        model = str(config.get("model", "")).strip()
        if not model:
            return None

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        content = ""
        if response and response.choices:
            message = response.choices[0].message
            content = message.content if message else ""
        result = self._extract_json(content)
        if result is not None:
            self._set_last_used_info(
                provider="openai",
                model=model,
                api_base=str(config.get("api_base", "")).strip() or None,
                is_backup=is_backup,
            )
        return result

    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[Any] | None = None,
    ) -> dict[str, Any] | list[Any] | None:
        """按优先级调用 LLM：Gemini -> 主 OpenAI -> 备用 OpenAI。"""
        self._set_last_used_info(provider=None, model=None, api_base=None, is_backup=False)

        result = self._call_gemini(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=response_schema,
        )
        if result is not None:
            return result

        if self._primary_client is not None:
            try:
                result = self._call_openai_client(
                    self._primary_client,
                    self.primary_openai_config,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    is_backup=False,
                )
                if result is not None:
                    return result
            except Exception as exc:
                logger.warning("主 OpenAI 调用失败: %s", str(exc))

        for idx, (client, cfg) in enumerate(self._backup_clients, start=1):
            try:
                result = self._call_openai_client(
                    client,
                    cfg,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    is_backup=True,
                )
                if result is not None:
                    logger.info("已切换到备用 OpenAI 配置 #%s", idx)
                    return result
            except Exception as exc:
                logger.warning("备用 OpenAI #%s 调用失败: %s", idx, str(exc))

        return None
