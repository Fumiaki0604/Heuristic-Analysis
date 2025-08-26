from bs4 import BeautifulSoup, Tag
import re
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
import logging

logger = logging.getLogger(__name__)

class HtmlAnalyzer:
    """HTML解析サービス"""
    
    def __init__(self):
        pass
    
    def analyze(self, html_content: str, url: str) -> Dict:
        """
        HTML解析を実行
        
        Args:
            html_content: HTML文字列
            url: 元のURL
            
        Returns:
            解析結果辞書
        """
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            
            analysis_result = {
                "meta_analysis": self._analyze_meta(soup),
                "heading_analysis": self._analyze_headings(soup),
                "navigation_analysis": self._analyze_navigation(soup),
                "form_analysis": self._analyze_forms(soup),
                "accessibility_analysis": self._analyze_accessibility(soup),
                "content_analysis": self._analyze_content(soup),
                "link_analysis": self._analyze_links(soup, url)
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"HTML解析エラー: {str(e)}")
            raise Exception(f"HTML解析に失敗しました: {str(e)}")
    
    def _analyze_meta(self, soup: BeautifulSoup) -> Dict:
        """メタ情報の解析"""
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else ""
        
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '').strip() if meta_desc else ""
        
        # OGPタグ
        og_title = soup.find('meta', attrs={'property': 'og:title'})
        og_description = soup.find('meta', attrs={'property': 'og:description'})
        og_image = soup.find('meta', attrs={'property': 'og:image'})
        
        # 構造化データ（JSON-LD）
        json_ld_scripts = soup.find_all('script', attrs={'type': 'application/ld+json'})
        
        return {
            "title": title,
            "title_length": len(title),
            "description": description,
            "description_length": len(description),
            "has_og_title": og_title is not None,
            "has_og_description": og_description is not None,
            "has_og_image": og_image is not None,
            "structured_data_count": len(json_ld_scripts),
            "charset": self._get_charset(soup)
        }
    
    def _analyze_headings(self, soup: BeautifulSoup) -> Dict:
        """見出し構造の解析"""
        headings = {}
        heading_order = []
        
        for level in range(1, 7):
            h_tags = soup.find_all(f'h{level}')
            headings[f'h{level}'] = len(h_tags)
            
            for h_tag in h_tags:
                heading_order.append({
                    'level': level,
                    'text': h_tag.get_text().strip(),
                    'length': len(h_tag.get_text().strip())
                })
        
        # 見出し階層の問題をチェック
        hierarchy_issues = self._check_heading_hierarchy(heading_order)
        
        return {
            "heading_counts": headings,
            "total_headings": sum(headings.values()),
            "heading_order": heading_order,
            "hierarchy_issues": hierarchy_issues,
            "has_h1": headings.get('h1', 0) > 0,
            "h1_count": headings.get('h1', 0),
            "multiple_h1": headings.get('h1', 0) > 1
        }
    
    def _analyze_navigation(self, soup: BeautifulSoup) -> Dict:
        """ナビゲーション構造の解析"""
        nav_elements = soup.find_all('nav')
        menu_lists = soup.find_all('ul', class_=re.compile(r'.*nav.*|.*menu.*', re.I))
        
        # パンくずナビゲーション
        breadcrumb_selectors = [
            '[class*="breadcrumb"]',
            '[id*="breadcrumb"]',
            '.breadcrumbs',
            'nav ol',
            '[role="navigation"] ol'
        ]
        
        breadcrumbs = []
        for selector in breadcrumb_selectors:
            breadcrumbs.extend(soup.select(selector))
        
        # リンクの重複チェック
        all_links = soup.find_all('a', href=True)
        link_texts = [link.get_text().strip() for link in all_links if link.get_text().strip()]
        duplicate_links = len(link_texts) - len(set(link_texts))
        
        return {
            "nav_elements_count": len(nav_elements),
            "menu_lists_count": len(menu_lists),
            "has_breadcrumbs": len(breadcrumbs) > 0,
            "total_links": len(all_links),
            "duplicate_link_texts": duplicate_links,
            "link_density": len(all_links) / max(len(soup.get_text().split()), 1)
        }
    
    def _analyze_forms(self, soup: BeautifulSoup) -> Dict:
        """フォーム要素の解析"""
        forms = soup.find_all('form')
        inputs = soup.find_all('input')
        labels = soup.find_all('label')
        
        # ラベルとフォーム要素の関連付けチェック
        unlabeled_inputs = []
        for input_tag in inputs:
            input_type = input_tag.get('type', 'text')
            if input_type not in ['hidden', 'submit', 'button']:
                input_id = input_tag.get('id')
                has_label = False
                
                if input_id:
                    label_for_input = soup.find('label', attrs={'for': input_id})
                    if label_for_input:
                        has_label = True
                
                # aria-label または placeholder のチェック
                if not has_label:
                    if input_tag.get('aria-label') or input_tag.get('placeholder'):
                        has_label = True
                
                if not has_label:
                    unlabeled_inputs.append(input_tag.get('name', 'unnamed'))
        
        # エラーメッセージ表示の仕組み
        error_elements = soup.find_all(attrs={'class': re.compile(r'.*error.*', re.I)})
        
        return {
            "form_count": len(forms),
            "input_count": len(inputs),
            "label_count": len(labels),
            "unlabeled_inputs": unlabeled_inputs,
            "unlabeled_count": len(unlabeled_inputs),
            "has_error_handling": len(error_elements) > 0,
            "required_fields": len(soup.find_all(attrs={'required': True}))
        }
    
    def _analyze_accessibility(self, soup: BeautifulSoup) -> Dict:
        """アクセシビリティの解析"""
        # alt属性のチェック
        images = soup.find_all('img')
        images_without_alt = [img for img in images if not img.get('alt')]
        
        # ARIA属性の使用
        aria_elements = soup.find_all(attrs=lambda x: x and any(attr.startswith('aria-') for attr in x.keys()))
        
        # ランドマークロール
        landmarks = soup.find_all(attrs={'role': re.compile(r'main|navigation|banner|complementary|contentinfo')})
        
        # タブインデックス
        tabindex_elements = soup.find_all(attrs={'tabindex': True})
        
        # 色のみに依存する情報（基本チェック）
        color_dependent_elements = soup.find_all(text=re.compile(r'赤.*クリック|青.*リンク|緑.*ボタン', re.I))
        
        return {
            "total_images": len(images),
            "images_without_alt": len(images_without_alt),
            "alt_text_coverage": (len(images) - len(images_without_alt)) / max(len(images), 1),
            "aria_elements_count": len(aria_elements),
            "landmark_roles_count": len(landmarks),
            "tabindex_elements": len(tabindex_elements),
            "potential_color_dependency": len(color_dependent_elements)
        }
    
    def _analyze_content(self, soup: BeautifulSoup) -> Dict:
        """コンテンツの解析"""
        # テキスト量
        text_content = soup.get_text()
        word_count = len(text_content.split())
        char_count = len(text_content.replace(' ', '').replace('\n', ''))
        
        # 日本語文字の検出
        japanese_chars = len(re.findall(r'[ひらがなカタカナ漢字]', text_content))
        
        # 段落とリスト
        paragraphs = soup.find_all('p')
        lists = soup.find_all(['ul', 'ol'])
        
        # テーブル
        tables = soup.find_all('table')
        tables_with_headers = len([t for t in tables if t.find('th')])
        
        return {
            "word_count": word_count,
            "char_count": char_count,
            "japanese_char_ratio": japanese_chars / max(char_count, 1),
            "paragraph_count": len(paragraphs),
            "list_count": len(lists),
            "table_count": len(tables),
            "tables_with_headers": tables_with_headers,
            "avg_paragraph_length": sum(len(p.get_text()) for p in paragraphs) / max(len(paragraphs), 1)
        }
    
    def _analyze_links(self, soup: BeautifulSoup, base_url: str) -> Dict:
        """リンク解析"""
        links = soup.find_all('a', href=True)
        
        external_links = []
        internal_links = []
        mailto_links = []
        tel_links = []
        
        base_domain = urlparse(base_url).netloc
        
        for link in links:
            href = link.get('href', '')
            
            if href.startswith('mailto:'):
                mailto_links.append(href)
            elif href.startswith('tel:'):
                tel_links.append(href)
            elif href.startswith('http'):
                if urlparse(href).netloc != base_domain:
                    external_links.append(href)
                else:
                    internal_links.append(href)
            else:
                internal_links.append(href)
        
        # リンクテキストの質をチェック
        vague_link_texts = ['こちら', 'here', 'click', 'more', '詳細', '続きを読む']
        vague_links = []
        for link in links:
            text = link.get_text().strip().lower()
            if text in vague_link_texts:
                vague_links.append(text)
        
        return {
            "total_links": len(links),
            "external_links": len(external_links),
            "internal_links": len(internal_links),
            "mailto_links": len(mailto_links),
            "tel_links": len(tel_links),
            "vague_link_texts": len(vague_links),
            "external_ratio": len(external_links) / max(len(links), 1)
        }
    
    def _check_heading_hierarchy(self, heading_order: List[Dict]) -> List[str]:
        """見出し階層の問題をチェック"""
        issues = []
        
        if not heading_order:
            return issues
        
        # H1から始まっているかチェック
        if heading_order[0]['level'] != 1:
            issues.append("見出しがH1から始まっていません")
        
        # 階層の飛びをチェック
        for i in range(1, len(heading_order)):
            prev_level = heading_order[i-1]['level']
            curr_level = heading_order[i]['level']
            
            if curr_level > prev_level + 1:
                issues.append(f"見出し階層に飛びがあります (H{prev_level} -> H{curr_level})")
        
        return issues
    
    def _get_charset(self, soup: BeautifulSoup) -> Optional[str]:
        """文字エンコーディングを取得"""
        charset_meta = soup.find('meta', attrs={'charset': True})
        if charset_meta:
            return charset_meta.get('charset')
        
        http_equiv_meta = soup.find('meta', attrs={'http-equiv': re.compile(r'content-type', re.I)})
        if http_equiv_meta:
            content = http_equiv_meta.get('content', '')
            charset_match = re.search(r'charset=([^;]+)', content, re.I)
            if charset_match:
                return charset_match.group(1)
        
        return None