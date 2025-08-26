from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Optional
from datetime import datetime

class HeuristicScore(BaseModel):
    """ヒューリスティック評価スコア"""
    information_architecture: int  # 情報設計 (30点)
    cta_visibility: int           # CTA視認性 (20点)
    readability: int              # 可読性 (20点)  
    form_ux: int                 # フォームUX (15点)
    accessibility: int           # アクセシビリティ (10点)
    performance: int            # パフォーマンス (5点)
    
    @property
    def total_score(self) -> int:
        return (
            self.information_architecture + 
            self.cta_visibility + 
            self.readability + 
            self.form_ux + 
            self.accessibility + 
            self.performance
        )

class AnalysisRule(BaseModel):
    """分析ルール"""
    rule_id: str
    category: str
    description: str
    severity: str  # high, medium, low
    passed: bool
    score_impact: int
    recommendation: str

class ImageAnalysis(BaseModel):
    """画像解析結果"""
    screenshot_path: str
    ocr_text: List[str]
    contrast_ratios: Dict[str, float]
    cta_elements: List[Dict]
    visual_density: float
    above_fold_content: List[str]

class HtmlAnalysis(BaseModel):
    """HTML解析結果"""
    title: str
    meta_description: str
    heading_structure: Dict[str, int]  # h1: 1, h2: 3, etc.
    form_analysis: Dict
    accessibility_violations: List[Dict]
    performance_metrics: Dict

class WebPageAnalysis(BaseModel):
    """Webページ分析結果"""
    url: HttpUrl
    analysis_id: str
    device_type: str
    timestamp: datetime
    
    # 分析結果
    html_analysis: HtmlAnalysis
    image_analysis: ImageAnalysis
    heuristic_scores: HeuristicScore
    rules_results: List[AnalysisRule]
    
    # 総合結果
    total_score: int
    recommendations: List[str]
    analysis_time: float
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }