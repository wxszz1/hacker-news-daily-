import logging
from src.models import Story

logger = logging.getLogger(__name__)

class NewsFilter:
    def __init__(self, config):
        self.min_score = config.min_score
        self.keywords = [kw.lower() for kw in config.keywords]
        self.exclude_keywords = [kw.lower() for kw in config.exclude]

    def filter(self, stories: list[Story], pushed_ids: set[int]) -> list[Story]:
        """先按热度，再按关键词，去重"""
        if not stories:
            return []

        # 第一步：按热度过滤
        high_score_stories = self._filter_by_score(stories)
        if not high_score_stories:
            logger.info("No stories meet minimum score threshold")
            return []

        # 第二步：按关键词过滤
        keyword_filtered = self._filter_by_keywords(high_score_stories)

        # 第三步：如果关键词过滤后没有结果，不推送（避免推送不相关内容）
        if not keyword_filtered:
            logger.info("No stories match keywords, skipping push")
            return []

        # 第四步：排除排除词
        result = self._exclude_by_keywords(keyword_filtered)

        # 第五步：去重
        result = self._deduplicate(result, pushed_ids)

        logger.info(f"Filtered {len(stories)} -> {len(result)} stories")
        return result

    def _filter_by_score(self, stories: list[Story]) -> list[Story]:
        return [s for s in stories if s.score >= self.min_score]

    def _filter_by_keywords(self, stories: list[Story]) -> list[Story]:
        if not self.keywords:
            return stories

        return [s for s in stories
                if any(kw in s.title.lower() for kw in self.keywords)]

    def _exclude_by_keywords(self, stories: list[Story]) -> list[Story]:
        if not self.exclude_keywords:
            return stories

        return [s for s in stories
                if not any(kw in s.title.lower() for kw in self.exclude_keywords)]

    def _deduplicate(self, stories: list[Story], pushed_ids: set[int]) -> list[Story]:
        if not pushed_ids:
            return stories

        return [s for s in stories if s.id not in pushed_ids]
