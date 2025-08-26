from typing import Dict, List
from backend.models.analysis import HeuristicScore, AnalysisRule
import logging

logger = logging.getLogger(__name__)

class HeuristicAnalyzer:
    """ヒューリスティック分析・スコアリングサービス"""
    
    def __init__(self):
        # 各カテゴリの最大スコア
        self.max_scores = {
            "information_architecture": 30,
            "cta_visibility": 20,
            "readability": 20,
            "form_ux": 15,
            "accessibility": 10,
            "performance": 5
        }
    
    def analyze(self, html_analysis: Dict, image_analysis: Dict, url: str) -> Dict:
        """
        総合的なヒューリスティック分析を実行
        
        Args:
            html_analysis: HTML解析結果
            image_analysis: 画像解析結果
            url: 対象URL
            
        Returns:
            ヒューリスティック分析結果
        """
        try:
            # 各カテゴリの分析実行
            info_arch_result = self._analyze_information_architecture(html_analysis, image_analysis)
            cta_result = self._analyze_cta_visibility(html_analysis, image_analysis)
            readability_result = self._analyze_readability(html_analysis, image_analysis)
            form_result = self._analyze_form_ux(html_analysis, image_analysis)
            accessibility_result = self._analyze_accessibility(html_analysis, image_analysis)
            performance_result = self._analyze_performance(html_analysis, image_analysis)
            
            # スコア集計
            scores = HeuristicScore(
                information_architecture=info_arch_result["score"],
                cta_visibility=cta_result["score"],
                readability=readability_result["score"],
                form_ux=form_result["score"],
                accessibility=accessibility_result["score"],
                performance=performance_result["score"]
            )
            
            # 全ルール結果を統合
            all_rules = []
            all_rules.extend(info_arch_result["rules"])
            all_rules.extend(cta_result["rules"])
            all_rules.extend(readability_result["rules"])
            all_rules.extend(form_result["rules"])
            all_rules.extend(accessibility_result["rules"])
            all_rules.extend(performance_result["rules"])
            
            # 改善提案の生成
            recommendations = self._generate_recommendations(all_rules)
            
            return {
                "scores": scores,
                "rules": all_rules,
                "recommendations": recommendations,
                "total_score": scores.total_score,
                "category_details": {
                    "information_architecture": info_arch_result,
                    "cta_visibility": cta_result,
                    "readability": readability_result,
                    "form_ux": form_result,
                    "accessibility": accessibility_result,
                    "performance": performance_result
                }
            }
            
        except Exception as e:
            logger.error(f"ヒューリスティック分析エラー: {str(e)}")
            raise Exception(f"ヒューリスティック分析に失敗しました: {str(e)}")
    
    def _analyze_information_architecture(self, html_analysis: Dict, image_analysis: Dict) -> Dict:
        """情報設計の分析（最大30点）"""
        rules = []
        score = self.max_scores["information_architecture"]
        
        # 見出し構造の評価
        heading_analysis = html_analysis.get("heading_analysis", {})
        
        # H1の存在チェック
        has_h1 = heading_analysis.get("has_h1", False)
        if not has_h1:
            rule = AnalysisRule(
                rule_id="ia_001",
                category="information_architecture",
                description="H1見出しが存在しない",
                severity="high",
                passed=False,
                score_impact=-5,
                recommendation="ページに適切なH1見出しを設定してください"
            )
            rules.append(rule)
            score += rule.score_impact
        
        # H1の重複チェック
        multiple_h1 = heading_analysis.get("multiple_h1", False)
        if multiple_h1:
            rule = AnalysisRule(
                rule_id="ia_002",
                category="information_architecture",
                description="H1見出しが複数存在",
                severity="medium",
                passed=False,
                score_impact=-3,
                recommendation="H1見出しは1ページに1つまでにしてください"
            )
            rules.append(rule)
            score += rule.score_impact
        
        # 見出し階層の評価
        hierarchy_issues = heading_analysis.get("hierarchy_issues", [])
        if hierarchy_issues:
            rule = AnalysisRule(
                rule_id="ia_003",
                category="information_architecture",
                description="見出し階層に問題があります",
                severity="medium",
                passed=False,
                score_impact=-4,
                recommendation="見出しの階層構造を正しく設定してください（H1→H2→H3の順序）"
            )
            rules.append(rule)
            score += rule.score_impact
        
        # ナビゲーション構造の評価
        nav_analysis = html_analysis.get("navigation_analysis", {})
        
        # パンくずナビゲーション
        has_breadcrumbs = nav_analysis.get("has_breadcrumbs", False)
        if not has_breadcrumbs:
            rule = AnalysisRule(
                rule_id="ia_004",
                category="information_architecture",
                description="パンくずナビゲーションが見つかりません",
                severity="low",
                passed=False,
                score_impact=-2,
                recommendation="ユーザーの現在位置を示すパンくずナビゲーションを追加してください"
            )
            rules.append(rule)
            score += rule.score_impact
        
        # リンクの重複チェック
        duplicate_links = nav_analysis.get("duplicate_link_texts", 0)
        if duplicate_links > 5:
            rule = AnalysisRule(
                rule_id="ia_005",
                category="information_architecture",
                description="重複するリンクテキストが多すぎます",
                severity="medium",
                passed=False,
                score_impact=-3,
                recommendation="同じテキストのリンクを整理し、区別しやすくしてください"
            )
            rules.append(rule)
            score += rule.score_impact
        
        return {
            "score": max(score, 0),
            "rules": rules,
            "max_score": self.max_scores["information_architecture"]
        }
    
    def _analyze_cta_visibility(self, html_analysis: Dict, image_analysis: Dict) -> Dict:
        """CTA視認性の分析（最大20点）"""
        rules = []
        score = self.max_scores["cta_visibility"]
        
        # Above the Fold分析
        above_fold = image_analysis.get("above_fold_analysis", {})
        
        # Above the FoldにCTAがあるかチェック
        has_cta_above_fold = above_fold.get("has_cta_above_fold", False)
        if not has_cta_above_fold:
            rule = AnalysisRule(
                rule_id="cta_001",
                category="cta_visibility",
                description="Above the Fold領域にCTAが見つかりません",
                severity="high",
                passed=False,
                score_impact=-8,
                recommendation="ページの上部（スクロールしない領域）に主要なCTAを配置してください"
            )
            rules.append(rule)
            score += rule.score_impact
        
        # ボタンテキストの分析
        ocr_analysis = image_analysis.get("ocr_analysis", {})
        button_texts = ocr_analysis.get("button_texts", [])
        
        if len(button_texts) == 0:
            rule = AnalysisRule(
                rule_id="cta_002",
                category="cta_visibility",
                description="明確なボタンテキストが検出されませんでした",
                severity="medium",
                passed=False,
                score_impact=-5,
                recommendation="「購入」「申込」「登録」など明確なアクションを示すボタンを設置してください"
            )
            rules.append(rule)
            score += rule.score_impact
        
        # コントラスト分析
        contrast_analysis = image_analysis.get("contrast_analysis", {})
        has_good_contrast = contrast_analysis.get("has_good_contrast", True)
        
        if not has_good_contrast:
            rule = AnalysisRule(
                rule_id="cta_003",
                category="cta_visibility",
                description="全体的なコントラストが不十分です",
                severity="medium",
                passed=False,
                score_impact=-4,
                recommendation="ボタンや重要な要素のコントラスト比を改善してください"
            )
            rules.append(rule)
            score += rule.score_impact
        
        # UI要素の検出
        element_detection = image_analysis.get("element_detection", {})
        button_candidates = element_detection.get("button_candidates", 0)
        
        if button_candidates < 2:
            rule = AnalysisRule(
                rule_id="cta_004",
                category="cta_visibility",
                description="視覚的に識別可能なボタンが少ないです",
                severity="low",
                passed=False,
                score_impact=-3,
                recommendation="ボタンをより視覚的に目立つデザインにしてください"
            )
            rules.append(rule)
            score += rule.score_impact
        
        return {
            "score": max(score, 0),
            "rules": rules,
            "max_score": self.max_scores["cta_visibility"]
        }
    
    def _analyze_readability(self, html_analysis: Dict, image_analysis: Dict) -> Dict:
        """可読性の分析（最大20点）"""
        rules = []
        score = self.max_scores["readability"]
        
        # メタ情報の評価
        meta_analysis = html_analysis.get("meta_analysis", {})
        
        # タイトルの長さチェック
        title_length = meta_analysis.get("title_length", 0)
        if title_length == 0:
            rule = AnalysisRule(
                rule_id="read_001",
                category="readability",
                description="ページタイトルが設定されていません",
                severity="high",
                passed=False,
                score_impact=-5,
                recommendation="適切なページタイトルを設定してください"
            )
            rules.append(rule)
            score += rule.score_impact
        elif title_length > 60:
            rule = AnalysisRule(
                rule_id="read_002",
                category="readability",
                description="ページタイトルが長すぎます",
                severity="low",
                passed=False,
                score_impact=-2,
                recommendation="ページタイトルを60文字以内に収めてください"
            )
            rules.append(rule)
            score += rule.score_impact
        
        # メタディスクリプションのチェック
        description_length = meta_analysis.get("description_length", 0)
        if description_length == 0:
            rule = AnalysisRule(
                rule_id="read_003",
                category="readability",
                description="メタディスクリプションが設定されていません",
                severity="medium",
                passed=False,
                score_impact=-3,
                recommendation="検索結果に表示されるメタディスクリプションを設定してください"
            )
            rules.append(rule)
            score += rule.score_impact
        
        # コンテンツ分析
        content_analysis = html_analysis.get("content_analysis", {})
        
        # 段落の平均長
        avg_paragraph_length = content_analysis.get("avg_paragraph_length", 0)
        if avg_paragraph_length > 200:
            rule = AnalysisRule(
                rule_id="read_004",
                category="readability",
                description="段落が長すぎます",
                severity="low",
                passed=False,
                score_impact=-2,
                recommendation="段落をより短く、読みやすい長さに分割してください"
            )
            rules.append(rule)
            score += rule.score_impact
        
        # 視覚的密度の評価
        visual_density = image_analysis.get("visual_density", {})
        is_cluttered = visual_density.get("is_cluttered", False)
        
        if is_cluttered:
            rule = AnalysisRule(
                rule_id="read_005",
                category="readability",
                description="ページの視覚的密度が高すぎます",
                severity="medium",
                passed=False,
                score_impact=-4,
                recommendation="要素間の余白を増やし、視覚的に整理してください"
            )
            rules.append(rule)
            score += rule.score_impact
        
        # 余白の評価
        has_sufficient_whitespace = visual_density.get("has_sufficient_whitespace", True)
        if not has_sufficient_whitespace:
            rule = AnalysisRule(
                rule_id="read_006",
                category="readability",
                description="余白が不足しています",
                severity="medium",
                passed=False,
                score_impact=-4,
                recommendation="要素間により多くの余白を設けて、読みやすくしてください"
            )
            rules.append(rule)
            score += rule.score_impact
        
        return {
            "score": max(score, 0),
            "rules": rules,
            "max_score": self.max_scores["readability"]
        }
    
    def _analyze_form_ux(self, html_analysis: Dict, image_analysis: Dict) -> Dict:
        """フォームUXの分析（最大15点）"""
        rules = []
        score = self.max_scores["form_ux"]
        
        form_analysis = html_analysis.get("form_analysis", {})
        form_count = form_analysis.get("form_count", 0)
        
        # フォームがある場合のみ評価
        if form_count > 0:
            # ラベルなし入力フィールドのチェック
            unlabeled_count = form_analysis.get("unlabeled_count", 0)
            if unlabeled_count > 0:
                rule = AnalysisRule(
                    rule_id="form_001",
                    category="form_ux",
                    description=f"{unlabeled_count}個の入力フィールドにラベルがありません",
                    severity="high",
                    passed=False,
                    score_impact=-6,
                    recommendation="すべての入力フィールドに適切なラベルを設定してください"
                )
                rules.append(rule)
                score += rule.score_impact
            
            # エラーハンドリングのチェック
            has_error_handling = form_analysis.get("has_error_handling", False)
            if not has_error_handling:
                rule = AnalysisRule(
                    rule_id="form_002",
                    category="form_ux",
                    description="エラーメッセージ表示の仕組みが見つかりません",
                    severity="medium",
                    passed=False,
                    score_impact=-4,
                    recommendation="入力エラー時に分かりやすいエラーメッセージを表示してください"
                )
                rules.append(rule)
                score += rule.score_impact
            
            # 必須フィールドの明示
            required_fields = form_analysis.get("required_fields", 0)
            input_count = form_analysis.get("input_count", 1)
            
            if required_fields == 0 and input_count > 2:
                rule = AnalysisRule(
                    rule_id="form_003",
                    category="form_ux",
                    description="必須フィールドが明示されていません",
                    severity="low",
                    passed=False,
                    score_impact=-2,
                    recommendation="必須入力項目を明確に示してください（*印やrequired属性）"
                )
                rules.append(rule)
                score += rule.score_impact
            
            # 入力フィールドの視覚的検出
            element_detection = image_analysis.get("element_detection", {})
            input_candidates = element_detection.get("input_candidates", 0)
            
            if input_candidates < input_count * 0.5:
                rule = AnalysisRule(
                    rule_id="form_004",
                    category="form_ux",
                    description="入力フィールドが視覚的に識別しにくい可能性があります",
                    severity="low",
                    passed=False,
                    score_impact=-3,
                    recommendation="入力フィールドの境界線や背景色を明確にしてください"
                )
                rules.append(rule)
                score += rule.score_impact
        
        return {
            "score": max(score, 0),
            "rules": rules,
            "max_score": self.max_scores["form_ux"]
        }
    
    def _analyze_accessibility(self, html_analysis: Dict, image_analysis: Dict) -> Dict:
        """アクセシビリティの分析（最大10点）"""
        rules = []
        score = self.max_scores["accessibility"]
        
        accessibility_analysis = html_analysis.get("accessibility_analysis", {})
        
        # alt属性のチェック
        alt_coverage = accessibility_analysis.get("alt_text_coverage", 1.0)
        if alt_coverage < 0.8:
            rule = AnalysisRule(
                rule_id="a11y_001",
                category="accessibility",
                description="画像のalt属性が不足しています",
                severity="medium",
                passed=False,
                score_impact=-4,
                recommendation="すべての画像に適切なalt属性を設定してください"
            )
            rules.append(rule)
            score += rule.score_impact
        
        # ARIA属性の使用
        aria_elements = accessibility_analysis.get("aria_elements_count", 0)
        if aria_elements == 0:
            rule = AnalysisRule(
                rule_id="a11y_002",
                category="accessibility",
                description="ARIA属性が使用されていません",
                severity="low",
                passed=False,
                score_impact=-2,
                recommendation="スクリーンリーダー対応のためARIA属性を活用してください"
            )
            rules.append(rule)
            score += rule.score_impact
        
        # ランドマークロールの使用
        landmarks = accessibility_analysis.get("landmark_roles_count", 0)
        if landmarks == 0:
            rule = AnalysisRule(
                rule_id="a11y_003",
                category="accessibility",
                description="ランドマークロールが設定されていません",
                severity="low",
                passed=False,
                score_impact=-2,
                recommendation="main、navigation、banner等のランドマークロールを設定してください"
            )
            rules.append(rule)
            score += rule.score_impact
        
        # コントラストチェック
        contrast_analysis = image_analysis.get("contrast_analysis", {})
        is_low_contrast = contrast_analysis.get("is_low_contrast", False)
        
        if is_low_contrast:
            rule = AnalysisRule(
                rule_id="a11y_004",
                category="accessibility",
                description="コントラスト比が不十分です",
                severity="medium",
                passed=False,
                score_impact=-4,
                recommendation="WCAG基準（4.5:1）以上のコントラスト比を確保してください"
            )
            rules.append(rule)
            score += rule.score_impact
        
        return {
            "score": max(score, 0),
            "rules": rules,
            "max_score": self.max_scores["accessibility"]
        }
    
    def _analyze_performance(self, html_analysis: Dict, image_analysis: Dict) -> Dict:
        """パフォーマンスの分析（最大5点）"""
        rules = []
        score = self.max_scores["performance"]
        
        # 基本的なパフォーマンス指標（簡易版）
        meta_analysis = html_analysis.get("meta_analysis", {})
        
        # 構造化データの使用
        structured_data_count = meta_analysis.get("structured_data_count", 0)
        if structured_data_count == 0:
            rule = AnalysisRule(
                rule_id="perf_001",
                category="performance",
                description="構造化データが設定されていません",
                severity="low",
                passed=False,
                score_impact=-1,
                recommendation="JSON-LD形式で構造化データを追加してください"
            )
            rules.append(rule)
            score += rule.score_impact
        
        # 画像最適化の簡易チェック
        total_images = html_analysis.get("accessibility_analysis", {}).get("total_images", 0)
        if total_images > 10:
            rule = AnalysisRule(
                rule_id="perf_002",
                category="performance",
                description="画像数が多く、読み込み速度に影響する可能性があります",
                severity="low",
                passed=False,
                score_impact=-2,
                recommendation="画像の最適化（圧縮・WebP形式）を検討してください"
            )
            rules.append(rule)
            score += rule.score_impact
        
        # OGP設定
        has_og_image = meta_analysis.get("has_og_image", False)
        if not has_og_image:
            rule = AnalysisRule(
                rule_id="perf_003",
                category="performance",
                description="OGP画像が設定されていません",
                severity="low",
                passed=False,
                score_impact=-1,
                recommendation="SNSでのシェア用にOGP画像を設定してください"
            )
            rules.append(rule)
            score += rule.score_impact
        
        return {
            "score": max(score, 0),
            "rules": rules,
            "max_score": self.max_scores["performance"]
        }
    
    def _generate_recommendations(self, rules: List[AnalysisRule]) -> List[str]:
        """ルール結果から改善提案を生成"""
        recommendations = []
        
        # 重要度でソート
        severity_order = {"high": 3, "medium": 2, "low": 1}
        failed_rules = [rule for rule in rules if not rule.passed]
        failed_rules.sort(key=lambda x: severity_order.get(x.severity, 0), reverse=True)
        
        # 上位10件の改善提案を取得
        for rule in failed_rules[:10]:
            recommendations.append(rule.recommendation)
        
        # 汎用的な改善提案を追加（ルールが少ない場合）
        if len(recommendations) < 3:
            generic_recommendations = [
                "ページ全体のコントラスト比を向上させてください",
                "重要な情報をページ上部に配置してください",
                "ナビゲーションをより直感的にしてください"
            ]
            
            for rec in generic_recommendations:
                if len(recommendations) >= 10:
                    break
                if rec not in recommendations:
                    recommendations.append(rec)
        
        return recommendations