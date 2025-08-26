import asyncio
from playwright.async_api import async_playwright, Browser, Page
from pathlib import Path
import uuid
import time
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ScreenshotService:
    """Playwrightを使用したスクリーンショット撮影サービス"""
    
    def __init__(self):
        self.screenshots_dir = Path("frontend/static/screenshots")
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self._browser: Optional[Browser] = None
    
    async def __aenter__(self):
        """非同期コンテキストマネージャーの開始"""
        try:
            self.playwright = await async_playwright().start()
            self._browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--single-process',
                    '--disable-gpu'
                ]
            )
            self._browser_available = True
        except Exception as e:
            logger.error(f"Playwrightブラウザの起動に失敗: {str(e)}")
            self.playwright = None
            self._browser = None
            self._browser_available = False
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了"""
        if self._browser:
            await self._browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def capture_page(self, url: str, device_type: str = "desktop") -> Dict:
        """
        指定されたURLのスクリーンショットとHTMLを取得
        
        Args:
            url: 対象URL
            device_type: デバイスタイプ（desktop/tablet/mobile）
            
        Returns:
            スクリーンショット情報とHTMLデータ
        """
        if not self._browser_available:
            logger.warning("Playwrightが利用できません。モックデータを返します。")
            return self._create_mock_response(url, device_type)
        
        start_time = time.time()
        
        # デバイス設定
        viewport_settings = self._get_viewport_settings(device_type)
        
        # 新しいページを作成
        page = await self._browser.new_page()
        
        try:
            # ビューポート設定
            await page.set_viewport_size(
                width=viewport_settings["width"],
                height=viewport_settings["height"]
            )
            
            # ユーザーエージェント設定
            if viewport_settings.get("user_agent"):
                await page.set_extra_http_headers({
                    'User-Agent': viewport_settings["user_agent"]
                })
            
            # ページを読み込み
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Cookie同意バナーの自動処理
            await self._handle_cookie_banner(page)
            
            # 少し待機してページを安定させる
            await page.wait_for_timeout(2000)
            
            # HTML取得
            html_content = await page.content()
            
            # スクリーンショット撮影
            screenshot_filename = f"{uuid.uuid4()}_{device_type}.png"
            screenshot_path = self.screenshots_dir / screenshot_filename
            
            await page.screenshot(
                path=screenshot_path,
                full_page=True,
                type="png"
            )
            
            # ページタイトル取得
            title = await page.title()
            
            # メタ情報取得
            meta_description = await page.get_attribute('meta[name="description"]', 'content') or ""
            
            # 処理時間計算
            processing_time = time.time() - start_time
            
            return {
                "screenshot_path": f"/static/screenshots/{screenshot_filename}",
                "html_content": html_content,
                "title": title,
                "meta_description": meta_description,
                "url": url,
                "device_type": device_type,
                "viewport": viewport_settings,
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error(f"スクリーンショット撮影エラー: {str(e)}")
            raise Exception(f"ページの取得に失敗しました: {str(e)}")
        
        finally:
            await page.close()
    
    def _get_viewport_settings(self, device_type: str) -> Dict:
        """デバイスタイプに応じたビューポート設定を取得"""
        settings = {
            "desktop": {
                "width": 1920,
                "height": 1080,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            "tablet": {
                "width": 768,
                "height": 1024,
                "user_agent": "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
            },
            "mobile": {
                "width": 375,
                "height": 667,
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
            }
        }
        
        return settings.get(device_type, settings["desktop"])
    
    async def _handle_cookie_banner(self, page: Page):
        """Cookie同意バナーの自動処理"""
        try:
            # よくあるCookie同意ボタンのセレクタ
            cookie_selectors = [
                'button[id*="accept"]',
                'button[id*="cookie"]',
                'button[class*="accept"]',
                'button[class*="cookie"]',
                '[data-testid="accept-cookies"]',
                '.cookie-accept',
                '#cookie-accept',
                'button:has-text("同意")',
                'button:has-text("Accept")',
                'button:has-text("OK")',
                'button:has-text("承認")'
            ]
            
            for selector in cookie_selectors:
                try:
                    # 要素が見つかったらクリック
                    await page.click(selector, timeout=1000)
                    logger.info(f"Cookie同意ボタンをクリック: {selector}")
                    await page.wait_for_timeout(1000)
                    break
                except:
                    continue
                    
        except Exception as e:
            # Cookie処理はベストエフォートなのでエラーを無視
            logger.debug(f"Cookie処理をスキップ: {str(e)}")
            pass

    def _create_mock_response(self, url: str, device_type: str) -> Dict:
        """Playwrightが利用できない場合のモックレスポンス"""
        return {
            "screenshot_path": "/static/screenshots/mock.png",
            "html_content": f"""
            <html>
                <head>
                    <title>Mock Page for {url}</title>
                    <meta name="description" content="This is a mock page for demonstration purposes">
                </head>
                <body>
                    <h1>Mock Page</h1>
                    <p>This is a mock page generated because Playwright is not available.</p>
                    <button>Sample Button</button>
                    <form>
                        <label for="email">Email:</label>
                        <input type="email" id="email" name="email">
                        <input type="submit" value="Submit">
                    </form>
                </body>
            </html>
            """,
            "title": f"Mock Page for {url}",
            "meta_description": "This is a mock page for demonstration purposes",
            "url": url,
            "device_type": device_type,
            "viewport": self._get_viewport_settings(device_type),
            "processing_time": 0.1
        }

# シングルトンインスタンス用のファクトリー関数
async def get_screenshot_service():
    """ScreenshotServiceのインスタンスを取得"""
    return ScreenshotService()