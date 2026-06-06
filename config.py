from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Annotated, Any, ClassVar

from pydantic import BaseModel, Field, field_validator, model_validator

try:
    from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
except ModuleNotFoundError:
    from dotenv import dotenv_values

    class NoDecode:
        """Marker used by pydantic-settings when available."""

    class SettingsConfigDict(dict):
        """兼容缺少 pydantic-settings 的运行环境。"""

    class BaseSettings(BaseModel):
        """简化版 BaseSettings：优先读取环境变量，其次读取 .env。"""

        model_config = {"extra": "ignore", "populate_by_name": True}

        def __init__(self, **values: Any) -> None:
            env_values: dict[str, Any] = {}

            # 构建 alias -> field_name 映射
            alias_to_name: dict[str, str] = {}
            for field_name, field in self.__class__.model_fields.items():
                if field.alias:
                    alias_to_name[field.alias] = field_name

            # 从 .env 文件加载，将 alias key 转为 field_name key
            env_file = getattr(self.__class__, "model_config", {}).get("env_file")
            if env_file and Path(env_file).exists():
                loaded = dotenv_values(str(env_file))
                for key, val in loaded.items():
                    if val is None:
                        continue
                    field_name = alias_to_name.get(key, key)
                    env_values[field_name] = val

            # 从环境变量加载（优先级高于 .env）
            for alias, field_name in alias_to_name.items():
                if alias in os.environ:
                    env_values[field_name] = os.environ[alias]

            # 显式传入的值优先级最高
            env_values.update(values)
            super().__init__(**env_values)


class Paths:
    """Centralized path management for the project."""

    ROOT_DIR: ClassVar[Path] = Path(__file__).resolve().parent
    DATA_DIR: ClassVar[Path] = ROOT_DIR / "data"
    LOGS_DIR: ClassVar[Path] = ROOT_DIR / "logs"
    RESULTS_DIR: ClassVar[Path] = ROOT_DIR / "results"
    REPORTS_DIR: ClassVar[Path] = ROOT_DIR / "reports"
    BLACKLIST_DIR: ClassVar[Path] = DATA_DIR / "blacklist"
    ANALYSIS_HISTORY_DIR: ClassVar[Path] = DATA_DIR / "analysis_history"
    DATABASE_PATH: ClassVar[Path] = ROOT_DIR / "cve_database.db"

    @classmethod
    def abs_path(cls, value: str | Path) -> str:
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = cls.ROOT_DIR / path
        return str(path.resolve())


class StaticConfig:
    """Non-sensitive configuration kept in code."""

    BLACKLIST_USERS: ClassVar[list[str]] = [
        "Kvi74",
        "huihuo123",
        "Live-Hack-CVE",
        "yrtsec",
        "l00neyhacker",
        "Shmily-ing",
        "romainmarcoux",
        "criminalip",
        "20142995",
        "Siwakorn2545",
        "moraveczd",
        "Vitrius",
    ]

    BLACKLIST_REPOSITORIES: ClassVar[list[str]] = [
        "1992513/www",
        "Ifem2BXvz4N4gh1gGn0bkR3Lp/cihna-dictatorshrip-8",
        "cirosantilli/china-dictatorhsip-7",
        "cirosantilli/china-dictatorship",
        "huangxy7/jd_scripts",
        "jerryy2577/jd_scripts",
        "snalfword/t_v_b_o_x_u_r_l_2",
        "SingLoveMyself/C2Panel",
        "lxw15337674/weibo-trending-hot-history",
        "btou666/I0QdsjFIVY",
        "JoeZang520/PHA_dm",
        "psk107520/p",
        "mhieu102/C2_NNPTUDM_24Mar",
        "dick318/awesome-stars",
        "romainmarcoux/malicious-outgoing-ip",
        "criminalip/C2-Daily-Feed",
        "huqi-pr/trending-in-one",
        "drb-ra/C2IntelFeeds",
        "szzdmj/szzdmj",
        "cxyfreedom/website-hot-hub",
        "XiangDongCJC/Conditional_competition-bypass-defender",
        "drrgtg/weibo_hot",
        "AZeC4/TelegramGroup",
        "Ro1eee/AcademyManager",
        "FlashNightModReborn/CrazyFlashNight",
        "adminlove520/Poc-Monitor_v1.0.1",
        "projectdiscovery/nuclei-templates",
        "romainmarcoux/malicious-outgoing-ip",
        "criminalip/C2-Daily-Feed",
        "lintx0/link-tools",
        "rodanmaharjan/ThreatIntelligence",
        "TencentBlueKing/blueking-dbm",
        "dimpal001/c2w_com",
        "duggytuxy/malicious_ip_addresses",
        "trickest/cve",
        "XiaomingX/data-cve-poc",
        "adysec/nuclei_poc",
    ]

    WATCHED_REPOSITORIES: ClassVar[list[str]] = [
        "wy876/POC",
        "knownsec/404StarLink",
        "shadow1ng/fscan",
        "SafeGroceryStore/MDUT",
        "gentilkiwi/mimikatz",
        "ehang-io/nps",
        "chaitin/xray",
        "BeichenDream/Godzilla",
        "FunnyWolf/pystinger",
        "Adaptix-Framework/AdaptixC2",
    ]

    GITHUB_KEYWORDS: ClassVar[list[str]] = [
        "免杀",
        "Sql注入",
        "RCE",
        "反序列化",
        "任意文件上传",
        "漏洞复现",
        "漏洞",
        "edr evasion",
        "安全工具",
        "security tool",
        "c2",
        "反向shell",
        "cnvd",
        "post-exploitation command",
        "AI Security",
        "外网打点",
        "资产+AND+指纹识别",
        "shellcode Loader",
        "后渗透",
    ]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # Database
    database_path: str = Field(default=str(Paths.DATABASE_PATH), alias="DATABASE_PATH")

    # Runtime
    monitor_interval: int = Field(default=7200, alias="MONITOR_INTERVAL", gt=0)

    # Primary AI config
    primary_ai_key: str = Field(default="", alias="PRIMARY_AI_KEY")
    primary_ai_base: str = Field(default="https://ai.897010.xyz/v1", alias="PRIMARY_AI_BASE")
    primary_ai_model: str = Field(default="qwen3-next", alias="PRIMARY_AI_MODEL")

    # Backup AI configs (JSON list)
    backup_ai_configs: Annotated[list[dict[str, str]], NoDecode] = Field(
        default_factory=list,
        alias="BACKUP_AI_CONFIGS",
    )

    # Gemini config
    gemini_ai_key: str = Field(default="", alias="GEMINI_AI_KEY")
    gemini_ai_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_AI_MODEL")
    gemini_ai_base_url: str = Field(
        default="https://generativelanguage.googleapis.com",
        alias="GEMINI_AI_BASE_URL",
    )

    # GitHub tokens
    github_tokens: Annotated[list[str], NoDecode] = Field(default_factory=list, alias="GITHUB_TOKENS")
    github_token: str = Field(default="", alias="GITHUB_TOKEN")

    # Blog
    blog_base_url: str = Field(default="http://127.0.0.1", alias="BLOG_BASE_URL")
    blog_token: str = Field(default="", alias="BLOG_TOKEN")

    @field_validator("database_path", mode="before")
    @classmethod
    def _normalize_database_path(cls, value: Any) -> str:
        if value in (None, ""):
            return str(Paths.DATABASE_PATH)
        return Paths.abs_path(value)

    @field_validator(
        "primary_ai_key",
        "primary_ai_base",
        "primary_ai_model",
        "gemini_ai_key",
        "gemini_ai_model",
        "gemini_ai_base_url",
        "github_token",
        "blog_base_url",
        "blog_token",
        mode="before",
    )
    @classmethod
    def _strip_string_fields(cls, value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @field_validator("github_tokens", mode="before")
    @classmethod
    def _parse_github_tokens(cls, value: Any) -> list[str]:
        if value in (None, ""):
            return []

        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]

        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []

            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                return [item.strip() for item in raw.split(",") if item.strip()]

            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
            if isinstance(parsed, str):
                return [item.strip() for item in parsed.split(",") if item.strip()]

        raise ValueError("GITHUB_TOKENS must be a JSON array or comma-separated string")

    @field_validator("backup_ai_configs", mode="before")
    @classmethod
    def _parse_backup_ai_configs(cls, value: Any) -> list[dict[str, str]]:
        if value in (None, ""):
            return []

        parsed: Any = value
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []

            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError("BACKUP_AI_CONFIGS must be a JSON array") from exc

        if not isinstance(parsed, list):
            raise ValueError("BACKUP_AI_CONFIGS must be a list of objects")

        normalized: list[dict[str, str]] = []
        for item in parsed:
            if not isinstance(item, dict):
                raise ValueError("Each BACKUP_AI_CONFIGS item must be an object")

            api_key = str(item.get("api_key", "")).strip()
            if not api_key:
                continue

            api_base = str(item.get("api_base", "https://api.openai.com/v1")).strip()
            model = str(item.get("model", "gpt-4.1-nano-2025-04-14")).strip()
            normalized.append(
                {
                    "api_key": api_key,
                    "api_base": api_base,
                    "model": model,
                }
            )

        return normalized

    @model_validator(mode="after")
    def _sync_github_token_fields(self) -> "Settings":
        if self.github_tokens:
            self.github_tokens = [token for token in self.github_tokens if token]
            self.github_token = self.github_tokens[0] if self.github_tokens else ""
        elif self.github_token:
            self.github_token = self.github_token.strip()
            self.github_tokens = [self.github_token] if self.github_token else []
        else:
            self.github_tokens = []
            self.github_token = ""

        return self

    @property
    def primary_ai_config(self) -> dict[str, str]:
        return {
            "api_key": self.primary_ai_key,
            "api_base": self.primary_ai_base,
            "model": self.primary_ai_model,
        }

    @property
    def gemini_ai_config(self) -> dict[str, str]:
        return {
            "api_key": self.gemini_ai_key,
            "model": self.gemini_ai_model,
            "base_url": self.gemini_ai_base_url,
        }


settings = Settings()

# Paths
PATHS = Paths
ROOT_DIR = str(Paths.ROOT_DIR)
DATA_DIR = str(Paths.DATA_DIR)
LOGS_DIR = str(Paths.LOGS_DIR)
RESULTS_DIR = str(Paths.RESULTS_DIR)
REPORTS_DIR = str(Paths.REPORTS_DIR)
BLACKLIST_DIR = str(Paths.BLACKLIST_DIR)
ANALYSIS_HISTORY_DIR = str(Paths.ANALYSIS_HISTORY_DIR)

# Backward-compatible exports
DATABASE_PATH = settings.database_path
MONITOR_INTERVAL = settings.monitor_interval

PRIMARY_AI_CONFIG = settings.primary_ai_config
BACKUP_AI_CONFIGS = settings.backup_ai_configs
GEMINI_AI_CONFIG = settings.gemini_ai_config

GITHUB_TOKENS = settings.github_tokens
GITHUB_TOKEN = settings.github_token

BLACKLIST_USERS = list(StaticConfig.BLACKLIST_USERS)
BLACKLIST_REPOSITORIES = list(StaticConfig.BLACKLIST_REPOSITORIES)
WATCHED_REPOSITORIES = list(StaticConfig.WATCHED_REPOSITORIES)
GITHUB_KEYWORDS = list(StaticConfig.GITHUB_KEYWORDS)

BLOG_TOKEN = settings.blog_token
BLOG_BASE_URL = settings.blog_base_url

__all__ = [
    "settings",
    "PATHS",
    "ROOT_DIR",
    "DATA_DIR",
    "LOGS_DIR",
    "RESULTS_DIR",
    "REPORTS_DIR",
    "BLACKLIST_DIR",
    "ANALYSIS_HISTORY_DIR",
    "DATABASE_PATH",
    "MONITOR_INTERVAL",
    "PRIMARY_AI_CONFIG",
    "BACKUP_AI_CONFIGS",
    "GEMINI_AI_CONFIG",
    "GITHUB_TOKENS",
    "GITHUB_TOKEN",
    "BLACKLIST_USERS",
    "BLACKLIST_REPOSITORIES",
    "WATCHED_REPOSITORIES",
    "GITHUB_KEYWORDS",
    "BLOG_TOKEN",
    "BLOG_BASE_URL",
]
