import logging

logger = logging.getLogger(__name__)

class NewsFilter:
    def __init__(self, config):
        self.min_score = config.min_score
        self.keywords = [kw.lower() for kw in config.keywords]
        self.exclude_keywords = [kw.lower() for kw in config.exclude]

    def filter(self, stories: list[dict], pushed_ids: set[int]) -> list[dict]:
        """先按热度，再按关键词，去重"""
        result = self._filter_by_score(stories)
        result = self._filter_by_keywords(result)
        result = self._exclude_by_keywords(result)
        result = self._deduplicate(result, pushed_ids)
        return result

    def _filter_by_score(self, stories: list[dict]) -> list[dict]:
        return [s for s in stories if s.get("score", 0) >= self.min_score]

    def _filter_by_keywords(self, stories: list[dict]) -> list[dict]:
        return [s for s in stories
                if any(kw in s.get("title", "").lower() for kw in self.keywords)]

    def _exclude_by_keywords(self, stories: list[dict]) -> list[dict]:
        return [s for s in stories
                if not any(kw in s.get("title", "").lower() for kw in self.exclude_keywords)]

    def _deduplicate(self, stories: list[dict], pushed_ids: set[int]) -> list[dict]:
        return [s for s in stories if s["id"] not in pushed_ids]
