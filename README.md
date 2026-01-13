# 📚 校园二手书 AI 识别

基于 PaddleOCR + LLM 的书籍信息智能识别系统。拍照识别书脊，一键获取书籍信息。

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Uni-app (Vue 3) / HTML |
| 后端 | Python FastAPI |
| OCR | PaddleOCR |
| LLM | DeepSeek V3 (SiliconCloud) |

## 📱 小程序版运行指南 (Uni-app)

前端代码位于 `frontend/` 目录，这是一个标准的 Uni-app 项目。

### 1. 准备工作
- **下载 HBuilderX**: [官网下载](https://www.dcloud.io/hbuilderx.html) (推荐 App 开发版)
- **下载 微信开发者工具**: [官网下载](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)
- **安装 Node.js**: [官网下载](https://nodejs.org/) (用于依赖安装)

### 2. 导入项目
1. 打开 HBuilderX
2. 点击菜单 `文件` -> `导入` -> `从本地目录导入`
3. 选择本项目中的 `frontend` 文件夹

### 3. 本地调试
1. 确保后端的 `启动后端.bat` 正在运行
2. 在 HBuilderX 中点击菜单 `运行` -> `运行到小程序模拟器` -> `微信开发者工具`
3. 如果提示需要设置开发者工具路径，请指向你安装的位置
4. **关键步骤**: 在微信开发者工具中，点击右上角 `详情` -> `本地设置` -> 勾选 `不校验合法域名、web-view（业务域名）、TLS版本以及HTTPS证书`
   - *（因为本地测试用的是 http://127.0.0.1，不勾选这个无法连接后端）*

### 4. 发布上传
1. 在微信开发者工具测试无误后
2. 点击右上角 `上传` 按钮
3. 登录微信公众平台后台提交审核

---

## 🛠️ 常见问题

**Q: 识别时提示网络错误？**
A: 
1. 检查后端是否开启
2. 检查开发者工具是否勾选了"不校验合法域名"
3. 如果是真机调试，确保手机和电脑在同一 WiFi，并在 `frontend/utils/config.js` 中配置了正确的 IP

**Q: 图标不显示？**
A: 项目默认未包含 TabBar 图标，请将你的图标 (png格式) 放入 `frontend/static/` 目录，并在 `pages.json` 中修改对应文件名。

## 📁 项目结构

```
ocr/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── main.py         # FastAPI 入口
│   │   ├── api/
│   │   │   └── books.py    # API 路由
│   │   └── services/
│   │       ├── ocr_service.py   # OCR 服务
│   │       └── llm_service.py   # LLM 服务
│   ├── uploads/            # 上传图片存储
│   ├── requirements.txt    # Python 依赖
│   └── .env               # 环境变量配置
│
└── frontend/               # 前端
    ├── test.html          # 纯 HTML 测试页面 ⭐
    ├── pages/             # Uni-app 页面
    └── ...                # Uni-app 配置文件
```

## 🚀 快速启动

### 1. 启动后端服务

```powershell
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

后端服务地址：http://127.0.0.1:8000

### 2. 打开前端测试页面

直接双击打开：`frontend/test.html`

或访问 API 文档：http://127.0.0.1:8000/docs

## 📡 API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/upload` | POST | 上传图片 |
| `/api/analyze/{file_id}` | POST | 分析图片 |
| `/api/analyze-direct` | POST | 一键上传并分析 |

## ⚙️ 配置

编辑 `backend/.env` 文件配置 API 密钥：

```
SILICONCLOUD_API_KEY=你的密钥
```

## 📝 开发说明

- OCR 首次运行会自动下载模型（约 100MB）
- 建议使用清晰的书脊照片
- 支持一次识别多本书
