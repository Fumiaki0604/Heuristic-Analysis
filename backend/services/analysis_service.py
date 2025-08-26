import time
import uuid
import asyncio
from datetime import datetime
from typing import Dict
from pathlib import Path

from backend.services.screenshot_service import ScreenshotService
from backend.services.html_analyzer import HtmlAnalyzer
from backend.services.image_analyzer import ImageAnalyzer
from backend.services.heuristic_analyzer import HeuristicAnalyzer
from backend.models.analysis import WebPageAnalysis, HtmlAnalysis, ImageAnalysis
import logging

logger = logging.getLogger(__name__)

class AnalysisService:
    """メイン分析サービス - 全ての分析を統合"""
    
    def __init__(self):
        self.html_analyzer = HtmlAnalyzer()
        self.image_analyzer = ImageAnalyzer()
        self.heuristic_analyzer = HeuristicAnalyzer()
    
    async def analyze_website(self, url: str, device_type: str = "desktop") -> Dict:
        """
        Webサイトの総合分析を実行
        
        Args:
            url: 分析対象URL
            device_type: デバイスタイプ（desktop/tablet/mobile）
            
        Returns:
            分析結果辞書
        """
        start_time = time.time()
        analysis_id = str(uuid.uuid4())
        
        try:
            logger.info(f"分析開始: {url} (device: {device_type})")
            
            # 1. スクリーンショット・HTML取得
            async with ScreenshotService() as screenshot_service:
                screenshot_data = await screenshot_service.capture_page(url, device_type)
            
            logger.info("スクリーンショット取得完了")
            
            # 2. HTML解析
            html_analysis_result = self.html_analyzer.analyze(
                screenshot_data["html_content"], 
                url
            )
            
            logger.info("HTML解析完了")
            
            # 3. 画像解析・OCR
            screenshot_full_path = Path("frontend") / "static" / "screenshots" / Path(screenshot_data["screenshot_path"]).name
            image_analysis_result = self.image_analyzer.analyze_screenshot(str(screenshot_full_path))
            
            logger.info("画像解析完了")
            
            # 4. ヒューリスティック分析
            heuristic_result = self.heuristic_analyzer.analyze(
                html_analysis_result,
                image_analysis_result,
                url
            )
            
            logger.info("ヒューリスティック分析完了")
            
            # 処理時間計算
            processing_time = time.time() - start_time
            
            # 結果の統合
            result = {
                "analysis_id": analysis_id,
                "url": url,
                "device_type": device_type,
                "timestamp": datetime.now().isoformat(),
                
                # 基本データ
                "screenshot_path": screenshot_data["screenshot_path"],
                "page_title": screenshot_data["title"],
                "processing_time": processing_time,
                
                # 分析結果
                "html_analysis": html_analysis_result,
                "image_analysis": image_analysis_result,
                "heuristic_analysis": heuristic_result,
                
                # APIレスポンス用のデータ
                "total_score": heuristic_result["total_score"],
                "categories": {
                    "information_architecture": heuristic_result["scores"].information_architecture,
                    "cta_visibility": heuristic_result["scores"].cta_visibility,
                    "readability": heuristic_result["scores"].readability,
                    "form_ux": heuristic_result["scores"].form_ux,
                    "accessibility": heuristic_result["scores"].accessibility,
                    "performance": heuristic_result["scores"].performance
                },
                "recommendations": heuristic_result["recommendations"],
                "analysis_time": processing_time
            }
            
            logger.info(f"分析完了: {url} (総スコア: {heuristic_result['total_score']}/100)")
            
            return result
            
        except Exception as e:
            logger.error(f"分析エラー ({url}): {str(e)}")
            raise Exception(f"分析処理中にエラーが発生しました: {str(e)}")
    
    def get_analysis_summary(self, analysis_result: Dict) -> Dict:
        """分析結果のサマリーを生成"""
        try:
            total_score = analysis_result["total_score"]
            
            # スコアレベルの判定
            if total_score >= 80:
                score_level = "excellent"
                score_message = "優秀"
            elif total_score >= 60:
                score_level = "good" 
                score_message = "良好"
            elif total_score >= 40:
                score_level = "fair"
                score_message = "普通"
            else:
                score_level = "poor"
                score_message = "要改善"
            
            # カテゴリ別の強み・弱み
            categories = analysis_result["categories"]
            max_scores = {
                "information_architecture": 30,
                "cta_visibility": 20, 
                "readability": 20,
                "form_ux": 15,
                "accessibility": 10,
                "performance": 5
            }
            
            category_scores = []
            for category, score in categories.items():
                max_score = max_scores[category]
                percentage = (score / max_score) * 100
                category_scores.append({
                    "category": category,
                    "score": score,
                    "max_score": max_score,
                    "percentage": percentage
                })
            
            # スコアでソート
            category_scores.sort(key=lambda x: x["percentage"], reverse=True)
            
            strengths = [cat for cat in category_scores if cat["percentage"] >= 70]
            weaknesses = [cat for cat in category_scores if cat["percentage"] < 50]
            
            return {
                "overall_score": total_score,
                "score_level": score_level,
                "score_message": score_message,
                "strengths": strengths[:3],  # 上位3つ
                "weaknesses": weaknesses[:3],  # 下位3つ
                "top_recommendations": analysis_result["recommendations"][:5]
            }
            
        except Exception as e:
            logger.error(f"サマリー生成エラー: {str(e)}")
            return {
                "overall_score": 0,
                "score_level": "error",
                "score_message": "分析エラー",
                "strengths": [],
                "weaknesses": [],
                "top_recommendations": ["分析結果の取得に失敗しました"]
            }

# シングルトンサービス
analysis_service = AnalysisService()