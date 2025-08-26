// メイン JavaScript ファイル

class HeuristicAnalyzer {
    constructor() {
        this.form = document.getElementById('analysisForm');
        this.analyzeBtn = document.getElementById('analyzeBtn');
        this.resultsSection = document.getElementById('results');
        this.currentAnalysisData = null;
        this.init();
    }

    init() {
        this.form.addEventListener('submit', this.handleSubmit.bind(this));
        
        // 詳細表示ボタンのイベントリスナー
        const detailBtn = document.getElementById('showDetailedAnalysis');
        if (detailBtn) {
            detailBtn.addEventListener('click', this.loadDetailedAnalysis.bind(this));
        }
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
            this.currentAnalysisData = {
                url: result.url,
                device_type: result.url.includes('device_type') ? 'mobile' : 'desktop' // 簡易実装
            };
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
        
        // 詳細表示ボタンを表示
        const detailBtn = document.getElementById('showDetailedAnalysis');
        if (detailBtn) {
            detailBtn.style.display = 'block';
        }
        
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

    async loadDetailedAnalysis() {
        if (!this.currentAnalysisData) {
            this.showError('詳細分析データが利用できません');
            return;
        }

        const detailBtn = document.getElementById('showDetailedAnalysis');
        detailBtn.textContent = '📊 詳細分析を読み込み中...';
        detailBtn.disabled = true;

        try {
            const response = await fetch('/api/analyze-detailed', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(this.currentAnalysisData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const detailedResult = await response.json();
            this.displayDetailedAnalysis(detailedResult);
            
            // ボタンを非表示にして詳細セクションを表示
            detailBtn.style.display = 'none';
            document.getElementById('detailedAnalysisSection').style.display = 'block';
            
        } catch (error) {
            console.error('詳細分析エラー:', error);
            this.showError('詳細分析の読み込みに失敗しました');
            detailBtn.textContent = '📊 詳細な得点内訳を見る';
            detailBtn.disabled = false;
        }
    }

    displayDetailedAnalysis(result) {
        const categoryDetails = document.getElementById('categoryDetails');
        const categoryNames = {
            'information_architecture': '情報設計',
            'cta_visibility': 'CTA視認性',
            'readability': '可読性',
            'form_ux': 'フォームUX',
            'accessibility': 'アクセシビリティ',
            'performance': 'パフォーマンス'
        };

        const maxScores = {
            'information_architecture': 30,
            'cta_visibility': 20,
            'readability': 20,
            'form_ux': 15,
            'accessibility': 10,
            'performance': 5
        };

        let detailHTML = '';

        Object.entries(result.category_details || {}).forEach(([categoryKey, details]) => {
            const categoryName = categoryNames[categoryKey] || categoryKey;
            const maxScore = maxScores[categoryKey] || 0;
            const currentScore = details.score || 0;
            const rules = details.rules || [];

            detailHTML += `
                <div class="category-detail-card">
                    <div class="category-header">
                        <h4>${categoryName}</h4>
                        <span class="category-score">${currentScore}/${maxScore}点</span>
                    </div>
                    
                    <div class="rules-list">
                        ${rules.length > 0 ? 
                            rules.map(rule => `
                                <div class="rule-item ${rule.passed ? 'rule-passed' : 'rule-failed'}">
                                    <div class="rule-icon">${rule.passed ? '✅' : '❌'}</div>
                                    <div class="rule-content">
                                        <div class="rule-description">${rule.description}</div>
                                        <div class="rule-impact">${rule.score_impact > 0 ? '+' : ''}${rule.score_impact}点</div>
                                        ${!rule.passed ? `<div class="rule-recommendation">💡 ${rule.recommendation}</div>` : ''}
                                    </div>
                                </div>
                            `).join('') 
                            : '<div class="no-rules">このカテゴリの詳細ルールはありません</div>'
                        }
                    </div>
                </div>
            `;
        });

        categoryDetails.innerHTML = detailHTML;
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