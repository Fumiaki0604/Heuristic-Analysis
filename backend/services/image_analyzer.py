import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import easyocr
import webcolors
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
import math

logger = logging.getLogger(__name__)

class ImageAnalyzer:
    """画像解析・OCR処理サービス"""
    
    def __init__(self):
        # EasyOCRの初期化（日本語+英語対応）
        try:
            self.ocr = easyocr.Reader(['en', 'ja'], gpu=False)
            self.ocr_available = True
        except Exception as e:
            logger.error(f"OCR初期化エラー: {str(e)}")
            self.ocr_available = False
        
    def analyze_screenshot(self, image_path: str) -> Dict:
        """
        スクリーンショットの画像解析を実行
        
        Args:
            image_path: 画像ファイルのパス
            
        Returns:
            解析結果辞書
        """
        try:
            # 画像を読み込み
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"画像を読み込めません: {image_path}")
            
            # PIL画像も作成（色分析用）
            pil_image = Image.open(image_path)
            
            analysis_result = {
                "ocr_analysis": self._analyze_ocr(image_path),
                "color_analysis": self._analyze_colors(pil_image),
                "visual_density": self._analyze_visual_density(image),
                "element_detection": self._detect_ui_elements(image),
                "above_fold_analysis": self._analyze_above_fold(image, pil_image),
                "contrast_analysis": self._analyze_contrast(image)
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"画像解析エラー: {str(e)}")
            raise Exception(f"画像解析に失敗しました: {str(e)}")
    
    def _analyze_ocr(self, image_path: str) -> Dict:
        """OCR解析"""
        try:
            if not self.ocr_available:
                return {
                    "text_blocks": [],
                    "total_text_count": 0,
                    "japanese_text_ratio": 0.0,
                    "average_confidence": 0.0,
                    "button_texts": [],
                    "heading_texts": []
                }
            
            # EasyOCR実行
            ocr_results = self.ocr.readtext(image_path)
            
            if not ocr_results:
                return {
                    "text_blocks": [],
                    "total_text_count": 0,
                    "japanese_text_ratio": 0.0,
                    "average_confidence": 0.0,
                    "button_texts": [],
                    "heading_texts": []
                }
            
            text_blocks = []
            button_keywords = ['ボタン', 'クリック', '購入', '申し込み', '登録', 'button', 'click', 'buy', 'purchase']
            heading_keywords = ['タイトル', '見出し', 'お知らせ', 'ニュース', '特集']
            
            button_texts = []
            heading_texts = []
            japanese_chars = 0
            total_chars = 0
            confidences = []
            
            for result in ocr_results:
                # EasyOCRの結果形式: [coordinates, text, confidence]
                coordinates = result[0]
                text = result[1]
                confidence = result[2]
                
                confidences.append(confidence)
                
                # 文字数統計
                total_chars += len(text)
                japanese_chars += len([c for c in text if ord(c) > 127])
                
                # テキストブロック情報
                text_block = {
                    "text": text,
                    "confidence": confidence,
                    "bounding_box": coordinates,
                    "position": self._get_text_position(coordinates),
                    "estimated_font_size": self._estimate_font_size(coordinates),
                    "text_length": len(text)
                }
                text_blocks.append(text_block)
                
                # ボタンテキストの判定
                if any(keyword in text.lower() for keyword in button_keywords):
                    button_texts.append(text)
                
                # 見出しテキストの判定（フォントサイズも考慮）
                if (any(keyword in text for keyword in heading_keywords) or 
                    text_block["estimated_font_size"] > 20):
                    heading_texts.append(text)
            
            return {
                "text_blocks": text_blocks,
                "total_text_count": len(text_blocks),
                "japanese_text_ratio": japanese_chars / max(total_chars, 1),
                "average_confidence": sum(confidences) / max(len(confidences), 1),
                "button_texts": button_texts,
                "heading_texts": heading_texts
            }
            
        except Exception as e:
            logger.error(f"OCR分析エラー: {str(e)}")
            return {
                "text_blocks": [],
                "total_text_count": 0,
                "japanese_text_ratio": 0.0,
                "average_confidence": 0.0,
                "button_texts": [],
                "heading_texts": []
            }
    
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
    
    def _analyze_visual_density(self, image: np.ndarray) -> Dict:
        """視覚的密度の分析"""
        try:
            # グレースケール変換
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # エッジ検出
            edges = cv2.Canny(gray, 50, 150)
            
            # エッジピクセルの割合
            edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
            
            # テクスチャ解析（分散ベース）
            texture_variance = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # 空白領域の検出
            _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
            white_space_ratio = np.sum(binary == 255) / (binary.shape[0] * binary.shape[1])
            
            # 視覚的複雑度の計算
            complexity_score = (edge_density * 100) + (texture_variance / 1000)
            
            return {
                "edge_density": edge_density,
                "texture_variance": texture_variance,
                "white_space_ratio": white_space_ratio,
                "complexity_score": min(complexity_score, 100),  # 0-100スケール
                "is_cluttered": complexity_score > 50,
                "has_sufficient_whitespace": white_space_ratio > 0.3
            }
            
        except Exception as e:
            logger.error(f"視覚密度分析エラー: {str(e)}")
            return {
                "edge_density": 0,
                "texture_variance": 0,
                "white_space_ratio": 0,
                "complexity_score": 0,
                "is_cluttered": False,
                "has_sufficient_whitespace": True
            }
    
    def _detect_ui_elements(self, image: np.ndarray) -> Dict:
        """UI要素の検出"""
        try:
            # グレースケール変換
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 矩形検出（ボタン候補）
            contours, _ = cv2.findContours(
                cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )
            
            button_candidates = []
            input_candidates = []
            
            for contour in contours:
                # 矩形近似
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                if len(approx) == 4:  # 矩形
                    x, y, w, h = cv2.boundingRect(contour)
                    area = w * h
                    aspect_ratio = w / h
                    
                    # ボタンの特徴（アスペクト比、サイズ）
                    if 1.5 <= aspect_ratio <= 5 and 1000 <= area <= 50000:
                        button_candidates.append({
                            "position": (x, y, w, h),
                            "area": area,
                            "aspect_ratio": aspect_ratio
                        })
                    
                    # 入力フィールドの特徴
                    elif 2 <= aspect_ratio <= 10 and 2000 <= area <= 20000:
                        input_candidates.append({
                            "position": (x, y, w, h),
                            "area": area,
                            "aspect_ratio": aspect_ratio
                        })
            
            return {
                "button_candidates": len(button_candidates),
                "input_candidates": len(input_candidates),
                "total_ui_elements": len(button_candidates) + len(input_candidates),
                "ui_density": (len(button_candidates) + len(input_candidates)) / (image.shape[0] * image.shape[1]) * 1000000
            }
            
        except Exception as e:
            logger.error(f"UI要素検出エラー: {str(e)}")
            return {
                "button_candidates": 0,
                "input_candidates": 0,
                "total_ui_elements": 0,
                "ui_density": 0
            }
    
    def _analyze_above_fold(self, image: np.ndarray, pil_image: Image.Image) -> Dict:
        """Above the Fold領域の分析"""
        try:
            # Above the Fold領域（上部600px）を抽出
            height = image.shape[0]
            fold_height = min(600, height // 2)
            
            above_fold = image[:fold_height, :]
            
            cta_keywords = ['購入', '申込', '登録', '予約', 'buy', 'purchase', 'register', 'book']
            cta_found = False
            important_text_count = 0
            
            # OCRが利用可能な場合のみ実行
            if self.ocr_available:
                try:
                    # Above the Fold領域のOCR
                    temp_path = "/tmp/above_fold_temp.png"
                    cv2.imwrite(temp_path, above_fold)
                    
                    ocr_results = self.ocr.readtext(temp_path)
                    
                    if ocr_results:
                        for result in ocr_results:
                            text = result[1]
                            if any(keyword in text.lower() for keyword in cta_keywords):
                                cta_found = True
                            if len(text) > 5:  # 重要そうなテキスト
                                important_text_count += 1
                except Exception as ocr_error:
                    logger.warning(f"Above the Fold OCR処理をスキップ: {str(ocr_error)}")
            
            # Above the Fold領域の色分析
            above_fold_pil = pil_image.crop((0, 0, pil_image.width, fold_height))
            colors = above_fold_pil.getcolors(maxcolors=256*256*256)
            color_variety = len(colors) if colors else 0
            
            return {
                "has_cta_above_fold": cta_found,
                "important_text_count": important_text_count,
                "color_variety_above_fold": color_variety,
                "fold_height": fold_height,
                "content_density_above_fold": important_text_count / max(fold_height / 100, 1)
            }
            
        except Exception as e:
            logger.error(f"Above the Fold分析エラー: {str(e)}")
            return {
                "has_cta_above_fold": False,
                "important_text_count": 0,
                "color_variety_above_fold": 0,
                "fold_height": 600,
                "content_density_above_fold": 0
            }
    
    def _analyze_contrast(self, image: np.ndarray) -> Dict:
        """コントラスト分析"""
        try:
            # グレースケール変換
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # ヒストグラム計算
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            
            # コントラストメトリクス
            # RMSコントラスト
            mean_intensity = np.mean(gray)
            rms_contrast = np.sqrt(np.mean((gray - mean_intensity) ** 2))
            
            # Michelsonコントラスト
            max_intensity = np.max(gray)
            min_intensity = np.min(gray)
            if max_intensity + min_intensity > 0:
                michelson_contrast = (max_intensity - min_intensity) / (max_intensity + min_intensity)
            else:
                michelson_contrast = 0
            
            # 動的レンジ
            dynamic_range = max_intensity - min_intensity
            
            return {
                "rms_contrast": rms_contrast,
                "michelson_contrast": michelson_contrast,
                "dynamic_range": dynamic_range,
                "mean_intensity": mean_intensity,
                "has_good_contrast": rms_contrast > 50 and dynamic_range > 100,
                "is_low_contrast": rms_contrast < 30
            }
            
        except Exception as e:
            logger.error(f"コントラスト分析エラー: {str(e)}")
            return {
                "rms_contrast": 0,
                "michelson_contrast": 0,
                "dynamic_range": 0,
                "mean_intensity": 0,
                "has_good_contrast": False,
                "is_low_contrast": True
            }
    
    def _get_text_position(self, coordinates) -> str:
        """テキストの位置を判定"""
        try:
            # EasyOCRの座標形式 [[x1,y1],[x2,y2],[x3,y3],[x4,y4]] に対応
            center_x = sum(point[0] for point in coordinates) / len(coordinates)
            center_y = sum(point[1] for point in coordinates) / len(coordinates)
            
            # 画面上での相対位置（暫定的な判定）
            if center_y < 200:
                return "top"
            elif center_y > 800:
                return "bottom"
            else:
                return "middle"
        except Exception:
            return "middle"
    
    def _estimate_font_size(self, coordinates) -> int:
        """フォントサイズの推定"""
        try:
            # バウンディングボックスの高さからフォントサイズを推定
            if len(coordinates) >= 4:
                # 上端と下端のY座標の差を計算
                y_coords = [point[1] for point in coordinates]
                height = max(y_coords) - min(y_coords)
            else:
                height = 16  # デフォルト値
            
            # 高さからフォントサイズを推定（経験的な値）
            estimated_font_size = int(height * 0.8)
            
            return max(estimated_font_size, 8)  # 最小8px
        except Exception:
            return 16  # デフォルト値