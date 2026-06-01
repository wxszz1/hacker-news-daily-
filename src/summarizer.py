import json
import logging
from src.models import Story

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个专业的技术文章摘要助手。请根据文章标题和内容，生成简洁的中文摘要。

要求：
1. 摘要必须使用中文
2. 摘要要简洁明了，突出核心内容
3. 如果有关键要点，以列表形式列出
4. 不要添加文章本身没有的信息"""

USER_PROMPT_TEMPLATE = """请为以下文章生成摘要：

标题：{title}
内容：{content}
链接：{url}

请返回JSON格式：{{"summary": "中文摘要", "key_points": ["要点1", "要点2", ...]}}"""


class Summarizer:
    """使用 LLM 生成文章智能摘要"""

    def __init__(self, llm_client, config, db=None):
        self.llm = llm_client
        self.max_length = config.max_length
        self.include_key_points = config.include_key_points
        self.enabled = llm_client.enabled and config.enabled
        self.db = db

    def summarize(self, story: Story) -> dict:
        """生成单篇文章摘要"""
        if not self.enabled or not story.title:
            return {"summary": "", "key_points": []}

        # 检查缓存
        cache_key = f"{story.title}:{story.url}"
        if self.db:
            cached = self.db.get_cache("summarize", cache_key)
            if cached:
                try:
                    return json.loads(cached)
                except:
                    pass

        # 截断过长的内容
        content = getattr(story, "content", "") or "（无内容）"
        truncated_content = content[:1500]

        user_prompt = USER_PROMPT_TEMPLATE.format(
            title=story.title,
            content=truncated_content,
            url=story.url
        )

        result = self.llm.chat_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=500
        )

        if result:
            summary = result.get("summary", "")
            key_points = result.get("key_points", []) if self.include_key_points else []
            output = {"summary": summary, "key_points": key_points}
            # 写入缓存
            if self.db:
                self.db.set_cache("summarize", cache_key, json.dumps(output, ensure_ascii=False))
            return output

        return {"summary": "", "key_points": []}

    def summarize_batch(self, stories: list[Story]) -> list[dict]:
        """批量生成摘要"""
        if not self.enabled:
            return [{"summary": "", "key_points": []} for _ in stories]

        results = []
        for story in stories:
            result = self.summarize(story)
            results.append(result)

        return results
