import json
import logging

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
    """使用 LLMClient 进行文章分类"""

    def __init__(self, llm_client=None, db=None):
        self.llm = llm_client
        self.enabled = llm_client is not None and llm_client.enabled
        self.db = db

    def classify(self, title: str) -> dict:
        """分类单篇文章"""
        if not self.enabled or not title:
            return {"category": "other", "reason": "分类未启用"}

        # 检查缓存
        if self.db:
            import json as json_mod
            cached = self.db.get_cache("classify", title)
            if cached:
                try:
                    return json_mod.loads(cached)
                except:
                    pass

        result = self.llm.chat_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=f"请分类这篇文章：{title}",
            max_tokens=100
        )

        if result:
            # 写入缓存
            if self.db:
                import json as json_mod
                self.db.set_cache("classify", title, json_mod.dumps(result, ensure_ascii=False))
            return result

        return {"category": "other", "reason": "分类失败"}

    def classify_batch(self, stories: list) -> list[dict]:
        """批量分类"""
        if not self.enabled:
            return [{"category": "other", "reason": "分类未启用"} for _ in stories]
        return [self.classify(s.title) for s in stories]