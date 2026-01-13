export const config = {
    // 默认后端地址（本地开发时自动替换）
    // 注意：在真机调试时，这里需要填写真实的局域网 IP 或服务器域名
    baseUrl: 'http://127.0.0.1:8000',

    // 初始化 API 地址
    initBaseUrl() {
        // Uni-app 环境下没有 window.location，无法像 HTML 那样自动检测
        // 但我们可以留个口子，在 storage 里读取配置
        try {
            const savedIp = uni.getStorageSync('book_ocr_api_ip');
            if (savedIp) {
                this.baseUrl = `http://${savedIp}:8000`;
                console.log('📦 使用已保存的 API IP:', this.baseUrl);
            }
        } catch (e) {
            console.error('读取 API 配置失败', e);
        }
    }
}

// 初始化
config.initBaseUrl();
