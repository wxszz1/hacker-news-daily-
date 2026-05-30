import logging

logger = logging.getLogger(__name__)

class NewsFilter:
    def __init__(self, config):
        self.min_score = config.min_score
        self.keywords = [kw.lower() for kw in config.keywords]
        self.exclude_keywords = [kw.lower() for kw in config.exclude]
        self.min_results = 3  # 至少保留的结果数

    def filter(self, stories: list[dict], pushed_ids: set[int]) -> list[dict]:
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

        # 第三步：如果关键词过滤后结果太少，回退到仅按热度
        if len(keyword_filtered) < self.min_results:
            logger.info(f"Keyword filtering too aggressive ({len(keyword_filtered)} results), "
                       f"falling back to score-based filtering")
            result = high_score_stories
        else:
            result = keyword_filtered

        # 第四步：排除排除词
        result = self._exclude_by_keywords(result)

        # 第五步：去重
        result = self._deduplicate(result, pushed_ids)

        logger.info(f"Filtered {len(stories)} -> {len(result)} stories")
        return result

    def _filter_by_score(self, stories: list[dict]) -> list[dict]:
        return [s for s in stories if s.get("score", 0) >= self.min_score]

    def _filter_by_keywords(self, stories: list[dict]) -> list[dict]:
        if not self.keywords:
            return stories

        return [s for s in stories
                if any(kw in s.get("title", "").lower() for kw in self.keywords)]

    def _exclude_by_keywords(self, stories: list[dict]) -> list[dict]:
        if not self.exclude_keywords:
            return stories

        return [s for s in stories
                if not any(kw in s.get("title", "").lower() for kw in self.exclude_keywords)]

    def _deduplicate(self, stories: list[dict], pushed_ids: set[int]) -> list[dict]:
        if not pushed_ids:
            return stories

        return [s for s in stories if s["id"] not in pushed_ids]
