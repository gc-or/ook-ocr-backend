import { config } from './config.js';

// 获取用户 ID (优先使用学号，没有则用旧的 UUID)
const getUserId = () => {
    // 优先使用学号作为用户标识
    const studentId = uni.getStorageSync('user_student_id');
    if (studentId) {
        return 'stu_' + studentId;
    }
    
    // 兼容旧用户：使用之前的 UUID
    let userId = uni.getStorageSync('user_uuid');
    if (!userId) {
        // 生成一个简单的 UUID (时间戳 + 随机数)
        userId = 'temp_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        uni.setStorageSync('user_uuid', userId);
        console.log('⚠️ 临时身份 ID (请填写学号):', userId);
    }
    return userId;
};

// 获取保存的联系方式
const getContact = () => {
    return uni.getStorageSync('user_qq') || '';
};

export const request = (options) => {
    return new Promise((resolve, reject) => {
        // 确保 URL 是完整的
        let url = options.url;
        if (!url.startsWith('http')) {
            url = config.baseUrl + url;
        }

        // 组装 Header
        const header = options.header || {};
        header['X-User-ID'] = getUserId();

        // 如果有联系方式，带上
        const contact = getContact();
        if (contact) {
            header['X-Contact'] = contact;
        }

        uni.request({
            url: url,
            method: options.method || 'GET',
            data: options.data,
            header: header,
            success: (res) => {
                if (res.statusCode >= 200 && res.statusCode < 300) {
                    resolve(res.data);
                } else {
                    uni.showToast({
                        title: res.data.detail || '请求失败',
                        icon: 'none'
                    });
                    reject(res);
                }
            },
            fail: (err) => {
                uni.showToast({
                    title: '网络连接失败',
                    icon: 'none'
                });
                reject(err);
            }
        });
    });
};

export const uploadFile = (filePath) => {
    return new Promise((resolve, reject) => {
        // 组装 Header
        const header = { 'X-User-ID': getUserId() };
        const contact = getContact();
        if (contact) header['X-Contact'] = contact;

        uni.uploadFile({
            url: config.baseUrl + '/api/upload',
            filePath: filePath,
            name: 'file',
            header: header,
            success: (res) => {
                if (res.statusCode >= 200 && res.statusCode < 300) {
                    resolve(JSON.parse(res.data));
                } else {
                    reject(res);
                }
            },
            fail: (err) => {
                reject(err);
            }
        });
    });
};

// 导出方法供业务层获取 ID (用于界面判断 is_mine)
export const getCurrentUserId = getUserId;
