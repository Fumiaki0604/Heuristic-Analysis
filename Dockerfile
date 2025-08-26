FROM python:3.12-slim

# 作業ディレクトリを設定
WORKDIR /app

# システムの依存関係をインストール
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    libglib2.0-0 \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    libatspi2.0-0 \
    libgtk-3-0 \
    libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係をコピーしてインストール
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Playwrightブラウザをインストール
RUN python -m playwright install chromium
RUN python -m playwright install-deps

# アプリケーションコードをコピー
COPY . .

# ポート番号を指定
EXPOSE 8000

# アプリケーションを起動
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]