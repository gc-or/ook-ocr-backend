export const config = {
    // 后端地址（Railway 生产环境）
    baseUrl: 'https://web-production-58f3e.up.railway.app',

    // 初始化 API 地址
    initBaseUrl() {
        // Uni-app 环境下没有 window.location，无法像 HTML 那样自动检测
        // 但我们可以留个口子，在 storage 里读取配置
        try {
            const savedUrl = uni.getStorageSync('book_ocr_api_url');
            if (savedUrl) {
                this.baseUrl = savedUrl;
                console.log('📦 使用已保存的 API URL:', this.baseUrl);
            }
        } catch (e) {
            console.error('读取 API 配置失败', e);
        }
    }
}

// 初始化
config.initBaseUrl();
