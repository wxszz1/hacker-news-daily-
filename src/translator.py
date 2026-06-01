import logging
import hashlib
import random
import httpx
import os

logger = logging.getLogger(__name__)

class Translator:
    """百度翻译 API"""

    API_URL = "https://fanyi-api.baidu.com/api/trans/vip/translate"

    def __init__(self):
        self.app_id = os.getenv("BAIDU_FANYI_APPID", "")
        self.secret = os.getenv("BAIDU_FANYI_SECRET", "")
        self.enabled = bool(self.app_id and self.secret)

    def translate(self, text: str) -> str:
        """翻译英文为中文"""
        if not text or not isinstance(text, str) or not self.enabled:
            return text

        try:
            salt = str(random.randint(1, 65536))
            sign_str = f"{self.app_id}{text}{salt}{self.secret}"
            sign = hashlib.md5(sign_str.encode()).hexdigest()

            resp = httpx.get(
                self.API_URL,
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
                return result["trans_result"][0]["dst"]
        except Exception as e:
            logger.warning(f"Translation failed: {e}")

        return text

    def translate_batch(self, texts: list[str]) -> list[str]:
        """批量翻译"""
        if not texts:
            return []
        return [self.translate(t) for t in texts]
