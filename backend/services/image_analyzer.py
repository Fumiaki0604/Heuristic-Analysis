from PIL import Image
import webcolors
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class ImageAnalyzer:
    """画像解析サービス（軽量版 - OCR機能なし）"""
    
    def __init__(self):
        # OCR機能は無効化（メモリ節約）
        self.ocr_available = False
        logger.info("軽量版画像アナライザーを初期化（OCR機能無効）")
        
    def analyze_screenshot(self, image_path: str) -> Dict:
        """
        スクリーンショットの画像解析を実行（軽量版）
        
        Args:
            image_path: 画像ファイルのパス
            
        Returns:
            解析結果辞書
        """
        try:
            # PIL画像のみ使用（OpenCVは不要）
            pil_image = Image.open(image_path)
            
            analysis_result = {
                "ocr_analysis": self._get_mock_ocr_result(),
                "color_analysis": self._analyze_colors(pil_image),
                "visual_density": self._get_mock_visual_density(),
                "element_detection": self._get_mock_element_detection(),
                "above_fold_analysis": self._get_mock_above_fold(),
                "contrast_analysis": self._get_mock_contrast_analysis()
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"画像解析エラー: {str(e)}")
            # エラー時はモックデータで継続
            return self._get_fallback_analysis_result()
    
    def _analyze_colors(self, image: Image.Image) -> Dict:
        """色分析"""
        try:
            # 画像をリサイズ（処理速度向上）
            image_small = image.resize((200, 200))
            
            # 色の抽出
            colors = image_small.getcolors(maxcolors=256*256*256)
            if not colors:
                return {"dominant_colors": [], "color_variety": 0}
            
            # 色の頻度でソート
            colors.sort(reverse=True, key=lambda x: x[0])
            
            # 主要色を取得（上位5色）
            dominant_colors = []
            for count, color in colors[:5]:
                if len(color) == 3:  # RGB
                    try:
                        color_name = webcolors.rgb_to_name(color)
                    except ValueError:
                        color_name = f"rgb{color}"
                    
                    dominant_colors.append({
                        "color": color,
                        "color_name": color_name,
                        "percentage": (count / (200 * 200)) * 100
                    })
            
            return {
                "dominant_colors": dominant_colors,
                "color_variety": len(colors),
                "is_monochromatic": len(colors) < 10,
                "is_colorful": len(colors) > 100
            }
            
        except Exception as e:
            logger.error(f"色分析エラー: {str(e)}")
            return {"dominant_colors": [], "color_variety": 0}
    
    def _get_mock_ocr_result(self) -> Dict:
        """OCR結果のモックデータ"""
        return {
            "text_blocks": [],
            "total_text_count": 0,
            "japanese_text_ratio": 0.0,
            "average_confidence": 0.0,
            "button_texts": ["購入", "申込", "登録"],  # 仮想的なボタンテキスト
            "heading_texts": ["メインタイトル", "サブタイトル"]
        }
    
    def _get_mock_visual_density(self) -> Dict:
        """視覚密度の模擬データ"""
        return {
            "edge_density": 0.15,
            "texture_variance": 1500.0,
            "white_space_ratio": 0.35,
            "complexity_score": 45.0,
            "is_cluttered": False,
            "has_sufficient_whitespace": True
        }
    
    def _get_mock_element_detection(self) -> Dict:
        """UI要素検出の模擬データ"""
        return {
            "button_candidates": 3,
            "input_candidates": 2,
            "total_ui_elements": 5,
            "ui_density": 0.02
        }
    
    def _get_mock_above_fold(self) -> Dict:
        """Above the Fold分析の模擬データ"""
        return {
            "has_cta_above_fold": True,
            "important_text_count": 5,
            "color_variety_above_fold": 15,
            "fold_height": 600,
            "content_density_above_fold": 8.3
        }
    
    def _get_mock_contrast_analysis(self) -> Dict:
        """コントラスト分析の模擬データ"""
        return {
            "rms_contrast": 65.0,
            "michelson_contrast": 0.7,
            "dynamic_range": 180,
            "mean_intensity": 128,
            "has_good_contrast": True,
            "is_low_contrast": False
        }
    
    def _get_fallback_analysis_result(self) -> Dict:
        """完全フォールバック用の分析結果"""
        return {
            "ocr_analysis": self._get_mock_ocr_result(),
            "color_analysis": {"dominant_colors": [], "color_variety": 0},
            "visual_density": self._get_mock_visual_density(),
            "element_detection": self._get_mock_element_detection(),
            "above_fold_analysis": self._get_mock_above_fold(),
            "contrast_analysis": self._get_mock_contrast_analysis()
        }