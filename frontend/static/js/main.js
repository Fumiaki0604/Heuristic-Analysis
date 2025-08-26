// メイン JavaScript ファイル

class HeuristicAnalyzer {
    constructor() {
        this.form = document.getElementById('analysisForm');
        this.analyzeBtn = document.getElementById('analyzeBtn');
        this.resultsSection = document.getElementById('results');
        this.init();
    }

    init() {
        this.form.addEventListener('submit', this.handleSubmit.bind(this));
    }

    async handleSubmit(event) {
        event.preventDefault();
        
        const formData = new FormData(this.form);
        const requestData = {
            url: formData.get('url'),
            device_type: formData.get('device_type')
        };

        // UI状態の更新
        this.setLoading(true);
        this.hideResults();

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            this.displayResults(result);
            
        } catch (error) {
            console.error('分析エラー:', error);
            this.showError('分析中にエラーが発生しました。URLを確認してもう一度お試しください。');
        } finally {
            this.setLoading(false);
        }
    }

    setLoading(isLoading) {
        const btnText = this.analyzeBtn.querySelector('.btn-text');
        const spinner = this.analyzeBtn.querySelector('.loading-spinner');
        
        if (isLoading) {
            btnText.textContent = '分析中...';
            spinner.style.display = 'inline';
            this.analyzeBtn.disabled = true;
        } else {
            btnText.textContent = '分析開始';
            spinner.style.display = 'none';
            this.analyzeBtn.disabled = false;
        }
    }

    hideResults() {
        this.resultsSection.style.display = 'none';
    }

    displayResults(result) {
        // 総合スコアの表示
        document.getElementById('totalScore').textContent = result.total_score;

        // カテゴリ別スコアの表示とアニメーション
        this.updateCategoryScores(result.categories);

        // スクリーンショットの表示
        this.displayScreenshot(result.screenshot_path);

        // 改善提案の表示
        this.displayRecommendations(result.recommendations);

        // 結果セクションを表示
        this.resultsSection.style.display = 'block';
        
        // 結果セクションにスムーズスクロール
        this.resultsSection.scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });
    }

    updateCategoryScores(categories) {
        const maxScores = {
            information_architecture: 30,
            cta_visibility: 20,
            readability: 20,
            form_ux: 15,
            accessibility: 10,
            performance: 5
        };

        Object.entries(categories).forEach(([category, score]) => {
            const maxScore = maxScores[category];
            const percentage = (score / maxScore) * 100;

            // スコアバーの更新
            const scoreFill = document.querySelector(`[data-category="${category}"]`);
            if (scoreFill) {
                setTimeout(() => {
                    scoreFill.style.width = `${percentage}%`;
                }, 100);
            }

            // スコアテキストの更新
            const scoreText = document.querySelector(`[data-score="${category}"]`);
            if (scoreText) {
                scoreText.textContent = `${score}/${maxScore}`;
            }

            // スコアに基づいて色を変更
            this.updateScoreColor(scoreFill, percentage);
        });
    }

    updateScoreColor(element, percentage) {
        if (!element) return;

        if (percentage >= 80) {
            element.style.background = 'linear-gradient(90deg, #48bb78, #38a169)'; // 緑
        } else if (percentage >= 60) {
            element.style.background = 'linear-gradient(90deg, #ed8936, #dd6b20)'; // オレンジ
        } else {
            element.style.background = 'linear-gradient(90deg, #f56565, #e53e3e)'; // 赤
        }
    }

    displayScreenshot(screenshotPath) {
        const screenshot = document.getElementById('screenshot');
        if (screenshotPath && screenshotPath !== '/static/screenshots/temp.png') {
            screenshot.src = screenshotPath;
            screenshot.style.display = 'block';
        }
    }

    displayRecommendations(recommendations) {
        const recommendationsList = document.getElementById('recommendationsList');
        recommendationsList.innerHTML = '';

        recommendations.forEach(recommendation => {
            const li = document.createElement('li');
            li.textContent = recommendation;
            recommendationsList.appendChild(li);
        });
    }

    showError(message) {
        // エラー表示の実装
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.style.cssText = `
            background: #fed7d7;
            color: #c53030;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            border: 1px solid #feb2b2;
        `;
        errorDiv.textContent = message;

        // フォームの後にエラーメッセージを表示
        this.form.parentNode.insertBefore(errorDiv, this.form.nextSibling);

        // 5秒後にエラーメッセージを削除
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }
}

// DOMが読み込まれた後に初期化
document.addEventListener('DOMContentLoaded', () => {
    new HeuristicAnalyzer();
});

// プログレスバーのスムーズアニメーション用CSS追加
const style = document.createElement('style');
style.textContent = `
    .error-message {
        animation: slideIn 0.3s ease-out;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
`;
document.head.appendChild(style);