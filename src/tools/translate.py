# src/tools/translate.py
import os
import hashlib
import random
import httpx
import logging
from src.agent.tools import Tool

logger = logging.getLogger(__name__)


class TranslateTool(Tool):
    """翻译工具（百度翻译API）"""

    def __init__(self):
        super().__init__(
            name="translate",
            description="将英文翻译为中文",
            parameters={
                "text": {
                    "type": "string",
                    "description": "待翻译的英文文本"
                }
            }
        )
        self.app_id = os.getenv("BAIDU_FANYI_APPID", "")
        self.secret = os.getenv("BAIDU_FANYI_SECRET", "")
        self.enabled = bool(self.app_id and self.secret)

    def execute(self, text: str = "", **kwargs) -> dict:
        """执行翻译"""
        if not text:
            return {"error": "翻译文本不能为空"}

        if not self.enabled:
            return {"error": "翻译 API 未配置", "text": text}

        try:
            salt = str(random.randint(1, 65536))
            sign_str = f"{self.app_id}{text}{salt}{self.secret}"
            sign = hashlib.md5(sign_str.encode()).hexdigest()

            resp = httpx.get(
                "https://fanyi-api.baidu.com/api/trans/vip/translate",
                params={
                    "q": text,
                    "from": "en",
                    "to": "zh",
                    "appid": self.app_id,
                    "salt": salt,
                    "sign": sign
                },
                timeout=5
            )
            result = resp.json()

            if "trans_result" in result:
                translated = result["trans_result"][0]["dst"]
                return {
                    "original": text,
                    "translated": translated
                }
            else:
                return {"error": "翻译失败", "text": text}

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return {"error": str(e), "text": text}
