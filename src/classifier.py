import json
import httpx
import logging
import os

logger = logging.getLogger(__name__)

# 预设分类
CATEGORIES = {
    "ai_model": "AI模型/大语言模型",
    "dev_tool": "开发工具/编程",
    "industry": "行业新闻/公司动态",
    "opensource": "开源项目",
    "paper": "论文/研究",
    "other": "其他"
}

SYSTEM_PROMPT = f"""你是一个文章分类助手。根据文章标题，将其分到最合适的类别。

可选类别：
{json.dumps(CATEGORIES, ensure_ascii=False, indent=2)}

规则：
1. 只返回JSON格式：{{"category": "类别key", "reason": "简短理由"}}
2. 不要返回其他内容
3. 如果不确定，返回 "other"
"""


class Classifier:
    """使用智谱 GLM-4 进行文章分类"""

    def __init__(self):
        self.api_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        self.api_key = os.getenv("ZHIPU_API_KEY", "")
        self.model = "glm-4-flash"  # 免费模型
        self.enabled = bool(self.api_key)

    def classify(self, title: str) -> dict:
        """分类单篇文章"""
        if not self.enabled or not title:
            return {"category": "other", "reason": "分类未启用"}

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
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"请分类这篇文章：{title}"}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 100
                },
                timeout=10
            )

            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                # 提取JSON
                start = content.find("{")
                end = content.rfind("}") + 1
                if start != -1 and end > start:
                    return json.loads(content[start:end])
        except Exception as e:
            logger.warning(f"Classification failed for '{title}': {e}")

        return {"category": "other", "reason": "分类失败"}

    def classify_batch(self, titles: list[str]) -> list[dict]:
        """批量分类"""
        if not self.enabled:
            return [{"category": "other", "reason": "分类未启用"} for _ in titles]
        return [self.classify(t) for t in titles]