import json
import httpx
import logging
import os
import time

logger = logging.getLogger(__name__)


class LLMClient:
    """智谱 GLM-4 API 客户端"""

    def __init__(self, config):
        self.api_url = config.api_url
        self.api_key = os.getenv("ZHIPU_API_KEY", "")
        self.model = config.model
        self.timeout = config.timeout
        self.max_retries = config.max_retries
        self.temperature = config.temperature
        self.enabled = bool(self.api_key)

    def chat(self, system_prompt: str, user_prompt: str,
             temperature: float = None, max_tokens: int = 1000) -> str | None:
        """单次对话调用，带重试"""
        if not self.enabled:
            return None

        temp = temperature if temperature is not None else self.temperature

        for attempt in range(self.max_retries + 1):
            try:
                resp = httpx.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": temp,
                        "max_tokens": max_tokens
                    },
                    timeout=self.timeout
                )

                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]

                logger.warning(f"LLM API error: {resp.status_code} - {resp.text}")
            except Exception as e:
                logger.warning(f"LLM API attempt {attempt + 1} failed: {e}")

            if attempt < self.max_retries:
                time.sleep(2 ** attempt)

        return None

    def chat_json(self, system_prompt: str, user_prompt: str,
                  temperature: float = None, max_tokens: int = 500) -> dict | None:
        """JSON 格式输出的对话调用（自动解析 JSON）"""
        content = self.chat(system_prompt, user_prompt, temperature, max_tokens)
        if not content:
            return None

        # 提取 JSON
        start = content.find("{")
        end = content.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(content[start:end])
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from LLM response: {e}")

        return None
