# src/tools/notify.py
import httpx
import logging
from src.agent.tools import Tool

logger = logging.getLogger(__name__)


class NotifyTool(Tool):
    """微信通知工具（Server酱）"""

    def __init__(self, send_key: str = ""):
        super().__init__(
            name="notify",
            description="通过微信发送消息通知",
            parameters={
                "title": {
                    "type": "string",
                    "description": "消息标题"
                },
                "content": {
                    "type": "string",
                    "description": "消息内容（Markdown格式）"
                }
            }
        )
        self.send_key = send_key
        self.api_url = "https://sctapi.ftqq.com/{key}.send"

    def execute(self, title: str = "", content: str = "", **kwargs) -> dict:
        """执行发送通知"""
        if not title or not content:
            return {"error": "标题和内容不能为空"}

        if not self.send_key:
            return {"error": "Server酱 SendKey 未配置"}

        try:
            resp = httpx.post(
                self.api_url.format(key=self.send_key),
                data={"title": title, "desp": content},
                timeout=10
            )
            result = resp.json()

            if resp.status_code == 200:
                return {
                    "success": True,
                    "title": title,
                    "message": "消息已发送"
                }
            else:
                return {
                    "success": False,
                    "error": result.get("message", "发送失败")
                }

        except Exception as e:
            logger.error(f"Notification failed: {e}")
            return {"error": str(e)}
