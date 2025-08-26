# Heuristic Analysis Tool

WebページのヒューリスティックUI/UX分析を行うツールです。

## 機能
- URL入力によるWebページ分析
- HTML解析（構造・アクセシビリティ）
- 画像解析（OCR・視認性・コントラスト）  
- ヒューリスティック評価とスコアリング
- 改善提案の自動生成

## 技術スタック
- **Backend**: Python + FastAPI
- **Frontend**: HTML/CSS/JavaScript
- **スクリーンショット**: Playwright
- **OCR**: PaddleOCR
- **画像処理**: OpenCV, PIL
- **デプロイ**: Render

## 開発環境セットアップ
```bash
cd "Heuristic Analysis"
pip install -r requirements.txt
uvicorn backend.app.main:app --reload
```

## プロジェクト構成
```
Heuristic Analysis/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPIアプリケーション
│   │   └── routers/         # APIルーティング
│   ├── services/            # ビジネスロジック
│   ├── models/              # データモデル
│   └── utils/               # ユーティリティ
├── frontend/
│   ├── static/              # CSS/JavaScript
│   └── templates/           # HTMLテンプレート
└── tests/                   # テストファイル
```