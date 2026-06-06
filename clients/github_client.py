from __future__ import annotations

import base64
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from config import GITHUB_TOKEN, GITHUB_TOKENS
from utils.logger import get_logger

logger = get_logger("clients.github_client")


@dataclass
class _TokenState:
    remaining: int = 5000
    available_at: float = 0.0
    reset_at: float = 0.0


class GithubClient:
    """GitHub API 统一客户端。"""

    def __init__(
        self,
        tokens: list[str] | None = None,
        *,
        min_interval: float = 0.2,
        timeout: int = 30,
        max_retries: int = 3,
    ) -> None:
        raw_tokens = tokens if tokens is not None else (GITHUB_TOKENS or [GITHUB_TOKEN])
        self.tokens = [token.strip() for token in raw_tokens if isinstance(token, str) and token.strip()]
        self.min_interval = max(0.0, min_interval)
        self.timeout = timeout
        self.max_retries = max(1, max_retries)

        self._lock = threading.Lock()
        self._current_index = 0
        self._next_request_time = 0.0
        self._token_state = {token: _TokenState() for token in self.tokens}

        self.session = requests.Session()
        retry = Retry(
            total=5,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=frozenset(["GET"]),
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.verify = True

    def _wait_interval(self) -> None:
        if self.min_interval <= 0:
            return
        with self._lock:
            now = time.time()
            wait = max(0.0, self._next_request_time - now)
            if wait > 0:
                time.sleep(wait)
            self._next_request_time = time.time() + self.min_interval

    def _get_token(self) -> str | None:
        if not self.tokens:
            return None

        while True:
            with self._lock:
                now = time.time()
                wait_seconds = None
                chosen_token: str | None = None

                for offset in range(len(self.tokens)):
                    idx = (self._current_index + offset) % len(self.tokens)
                    token = self.tokens[idx]
                    state = self._token_state[token]
                    if state.available_at <= now:
                        self._current_index = (idx + 1) % len(self.tokens)
                        chosen_token = token
                        break
                    token_wait = max(0.0, state.available_at - now)
                    wait_seconds = token_wait if wait_seconds is None else min(wait_seconds, token_wait)

            if chosen_token:
                return chosen_token
            if wait_seconds is None:
                return None
            time.sleep(max(wait_seconds, 0.1))

    def _update_token_state_from_headers(self, token: str | None, response: requests.Response) -> None:
        if not token:
            return
        remaining_header = response.headers.get("X-RateLimit-Remaining")
        reset_header = response.headers.get("X-RateLimit-Reset")
        with self._lock:
            state = self._token_state[token]
            if remaining_header is not None:
                try:
                    state.remaining = int(remaining_header)
                except ValueError:
                    pass
            if reset_header is not None:
                try:
                    state.reset_at = float(reset_header)
                except ValueError:
                    pass
            if state.remaining <= 0 and state.reset_at > time.time():
                state.available_at = state.reset_at
            elif state.available_at < time.time():
                state.available_at = 0.0

    def _mark_token_cooldown(self, token: str | None, cooldown_seconds: float, remaining: int = 0) -> None:
        if not token:
            return
        with self._lock:
            state = self._token_state[token]
            state.remaining = remaining
            state.available_at = max(state.available_at, time.time() + cooldown_seconds)

    def _request(
        self,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
        absolute: bool = False,
    ) -> requests.Response | None:
        url = endpoint if absolute else f"https://api.github.com{endpoint}"
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            token = self._get_token()
            headers = {"Accept": "application/vnd.github.v3+json"}
            if token:
                headers["Authorization"] = f"token {token}"

            self._wait_interval()

            try:
                response = self.session.get(url, headers=headers, params=params, timeout=self.timeout)
            except requests.RequestException as exc:
                last_error = exc
                logger.warning("GitHub 请求异常，第 %s 次重试: %s", attempt, str(exc))
                self._mark_token_cooldown(token, cooldown_seconds=30.0)
                if attempt < self.max_retries:
                    time.sleep(min(2 ** attempt, 8))
                continue

            self._update_token_state_from_headers(token, response)

            if response.status_code == 401:
                logger.warning("GitHub Token 认证失败，切换 Token")
                self._mark_token_cooldown(token, cooldown_seconds=3600.0)
                if attempt < self.max_retries:
                    continue
                return None

            if response.status_code == 403:
                reset_header = response.headers.get("X-RateLimit-Reset")
                wait = 60.0
                if reset_header:
                    try:
                        wait = max(1.0, float(reset_header) - time.time())
                    except ValueError:
                        wait = 60.0
                logger.warning("GitHub 速率限制触发，切换 Token")
                self._mark_token_cooldown(token, cooldown_seconds=wait)
                if attempt < self.max_retries:
                    continue
                return None

            if 500 <= response.status_code < 600:
                logger.warning("GitHub 服务端错误 %s，第 %s 次重试", response.status_code, attempt)
                if attempt < self.max_retries:
                    time.sleep(min(2 ** attempt, 8))
                    continue
                return None

            return response

        if last_error:
            logger.error("GitHub 请求失败: %s", str(last_error))
        return None

    def _request_json(
        self,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
        absolute: bool = False,
    ) -> dict[str, Any] | list[Any] | None:
        response = self._request(endpoint, params=params, absolute=absolute)
        if not response:
            return None
        if response.status_code >= 400:
            logger.warning("GitHub 返回错误状态码: %s", response.status_code)
            return None
        try:
            return response.json()
        except ValueError:
            logger.warning("GitHub 返回非 JSON 响应")
            return None

    def get_rate_limit(self) -> dict[str, Any] | None:
        data = self._request_json("/rate_limit")
        return data if isinstance(data, dict) else None

    def search_repos(
        self,
        query: str,
        *,
        sort: str = "updated",
        order: str = "desc",
        page: int = 1,
        per_page: int = 30,
    ) -> dict[str, Any] | None:
        params = {
            "q": query,
            "sort": sort,
            "order": order,
            "page": page,
            "per_page": per_page,
        }
        data = self._request_json("/search/repositories", params=params)
        return data if isinstance(data, dict) else None

    def get_commits(
        self,
        repo_full_name: str,
        *,
        since: datetime | str | None = None,
        per_page: int = 10,
    ) -> list[dict[str, Any]] | None:
        params: dict[str, Any] = {"per_page": per_page}
        if since:
            if isinstance(since, datetime):
                params["since"] = since.strftime("%Y-%m-%dT%H:%M:%SZ")
            else:
                params["since"] = since
        data = self._request_json(f"/repos/{repo_full_name}/commits", params=params)
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        return None

    def get_commit_detail(self, repo_full_name: str, sha_or_url: str) -> dict[str, Any] | None:
        if sha_or_url.startswith("http://") or sha_or_url.startswith("https://"):
            data = self._request_json(sha_or_url, absolute=True)
        else:
            data = self._request_json(f"/repos/{repo_full_name}/commits/{sha_or_url}")
        return data if isinstance(data, dict) else None

    def get_readme(self, repo_full_name: str) -> str | None:
        data = self._request_json(f"/repos/{repo_full_name}/readme")
        if not isinstance(data, dict):
            return None
        encoded = data.get("content")
        if not encoded:
            return None
        try:
            normalized = str(encoded).replace("\n", "")
            return base64.b64decode(normalized).decode("utf-8", errors="ignore")
        except Exception:
            logger.warning("README 解码失败: %s", repo_full_name)
            return None

    def get_repository(self, repo_full_name: str) -> dict[str, Any] | None:
        data = self._request_json(f"/repos/{repo_full_name}")
        return data if isinstance(data, dict) else None

    def get_contents(self, repo_full_name: str, path: str = "") -> list[dict[str, Any]] | None:
        endpoint = f"/repos/{repo_full_name}/contents/{path}" if path else f"/repos/{repo_full_name}/contents"
        data = self._request_json(endpoint)
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            return [data]
        return None

    def get_json_by_url(self, url: str) -> dict[str, Any] | list[Any] | None:
        return self._request_json(url, absolute=True)
