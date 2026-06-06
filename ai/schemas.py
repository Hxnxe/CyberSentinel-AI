from typing import List, Optional

from pydantic import BaseModel


class SecurityAnalysisResult(BaseModel):
    short_description: str
    summary: str
    risk_level: str
    key_points: List[str]
    technical_details: List[str]
    affected_components: List[str]
    is_valuable: bool
    value_reason: str
    security_type: str
    update_type: str
    exploit_status: str
    relevance_score: Optional[str] = None


class ArticleClassificationItem(BaseModel):
    title: str
    category: str


class ArticleClassificationResult(BaseModel):
    articles: List[ArticleClassificationItem]
