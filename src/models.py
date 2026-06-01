from dataclasses import dataclass, field


@dataclass
class Story:
    """文章数据模型"""
    id: int
    title: str
    url: str = ""
    score: int = 0
    descendants: int = 0
    time: int = 0
    by: str = ""

    # 分类
    category: str = ""
    category_reason: str = ""

    # 翻译
    title_cn: str = ""

    # Agent 处理结果
    agent_score: int = 0
    agent_score_reason: str = ""
    summary: str = ""
    key_points: list[str] = field(default_factory=list)
    research_report: str = ""
    research_highlights: list[str] = field(default_factory=list)

    @classmethod
    def from_hn(cls, data: dict) -> "Story":
        """从 HN API 返回的 dict 构建 Story"""
        return cls(
            id=data.get("id", 0),
            title=data.get("title", "Untitled"),
            url=data.get("url", ""),
            score=data.get("score", 0),
            descendants=data.get("descendants", 0),
            time=data.get("time", 0),
            by=data.get("by", ""),
        )
