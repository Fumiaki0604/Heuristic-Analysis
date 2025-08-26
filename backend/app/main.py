from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, HttpUrl
import uvicorn
import os
import logging
from backend.services.analysis_service import analysis_service

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI アプリケーション初期化
app = FastAPI(
    title="Heuristic Analysis Tool",
    description="Webページのヒューリスティック分析を行うツール",
    version="1.0.0"
)

# 静的ファイルとテンプレートの設定
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

# リクエストモデル
class AnalysisRequest(BaseModel):
    url: HttpUrl
    device_type: str = "desktop"  # desktop, tablet, mobile
    
# レスポンスモデル
class AnalysisResponse(BaseModel):
    url: str
    total_score: int
    categories: dict
    recommendations: list
    screenshot_path: str
    analysis_time: float

class DetailedAnalysisResponse(BaseModel):
    url: str
    total_score: int
    categories: dict
    recommendations: list
    screenshot_path: str
    analysis_time: float
    category_details: dict

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """メインページを表示"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "ok", "message": "Heuristic Analysis Tool is running"}

@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_website(analysis_request: AnalysisRequest):
    """
    Webページのヒューリスティック分析を実行
    """
    try:
        logger.info(f"分析リクエスト受信: {analysis_request.url}")
        
        # 実際の分析処理を実行
        analysis_result = await analysis_service.analyze_website(
            url=str(analysis_request.url),
            device_type=analysis_request.device_type
        )
        
        # APIレスポンス形式に変換
        response = AnalysisResponse(
            url=analysis_result["url"],
            total_score=analysis_result["total_score"],
            categories=analysis_result["categories"],
            recommendations=analysis_result["recommendations"],
            screenshot_path=analysis_result["screenshot_path"],
            analysis_time=analysis_result["analysis_time"]
        )
        
        logger.info(f"分析完了: {analysis_request.url} (スコア: {response.total_score})")
        return response
        
    except Exception as e:
        logger.error(f"分析エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析中にエラーが発生しました: {str(e)}")

@app.post("/api/analyze-detailed", response_model=DetailedAnalysisResponse)
async def analyze_website_detailed(analysis_request: AnalysisRequest):
    """
    Webページの詳細ヒューリスティック分析を実行（カテゴリ詳細付き）
    """
    try:
        logger.info(f"詳細分析リクエスト受信: {analysis_request.url}")
        
        # 実際の分析処理を実行
        analysis_result = await analysis_service.analyze_website(
            url=str(analysis_request.url),
            device_type=analysis_request.device_type
        )
        
        # 詳細APIレスポンス形式に変換
        response = DetailedAnalysisResponse(
            url=analysis_result["url"],
            total_score=analysis_result["total_score"],
            categories=analysis_result["categories"],
            recommendations=analysis_result["recommendations"],
            screenshot_path=analysis_result["screenshot_path"],
            analysis_time=analysis_result["analysis_time"],
            category_details=analysis_result.get("heuristic_analysis", {}).get("category_details", {})
        )
        
        logger.info(f"詳細分析完了: {analysis_request.url} (スコア: {response.total_score})")
        return response
        
    except Exception as e:
        logger.error(f"詳細分析エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"詳細分析中にエラーが発生しました: {str(e)}")

@app.get("/api/analyze/{analysis_id}")
async def get_analysis_result(analysis_id: str):
    """分析結果の取得（将来的に非同期処理対応）"""
    # TODO: 実際のデータベースから結果を取得
    return {"message": f"分析ID {analysis_id} の結果を取得"}

@app.get("/api/summary/{analysis_id}")
async def get_analysis_summary(analysis_id: str):
    """分析結果のサマリーを取得"""
    # TODO: 実装予定
    return {"message": f"分析ID {analysis_id} のサマリーを取得"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)