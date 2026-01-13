# 🚀 微信小程序后端部署指南

恭喜！你的代码已经准备好上传云端了。请按照以下步骤操作：

## 第一步：上传代码到 GitHub

1.  登录 [GitHub](https://github.com/)（如果没有账号请注册）。
2.  点击右上角 **+** 号 -> **New repository**。
3.  Repository name 填：`book-ocr-backend`。
4.  其他不要动（不要勾选 Add a README file），点击 **Create repository**。
5.  复制由于生成的 HTTPS 地址（例如：`https://github.com/yourname/book-ocr-backend.git`）。
6.  回到你电脑的**终端**（PowerShell），执行以下命令（把地址换成你刚才复制的）：

```bash
git remote add origin https://github.com/gc-or/ook-ocr-backend.git
git branch -M main
git push -u origin main
```

## 第二步：在 Railway 部署

1.  登录 [Railway](https://railway.app/)（可以直接用 GitHub 登录）。
2.  点击 **+ New Project** -> **Deploy from GitHub repo**。
3.  选择你刚才创建的 `book-ocr-backend`。
4.  点击 **Deploy Now**。

## 第三步：配置环境变量 (重要！)

1.  在 Railway 项目面板中，点击刚才部署的服务卡片。
2.  进入 **Settings** 选项卡。
3.  找到 **Environment Variables** 区域。
4.  点击 **New Variable**，添加以下内容：
    *   **KEY**: `SILICONCLOUD_API_KEY`
    *   **VALUE**: `sk-tmdzipjmgxvqbavkeroezszxqqnmrmihnykerplgemtybfpv` (这是你的 Key)
5.  添加后，Railway 会自动重新部署。

## 第四步：配置数据库持久化 (重要！防止数据丢失) 💾

默认情况下，每次更新部署，Railway 会重置文件系统，导致数据库丢失。你需要挂载一个硬盘来保存 `books.db`。

1.  在 Railway 项目页面，点击你的服务。
2.  进入 **Volumes** 选项卡。
3.  点击 **Add Volume**。
4.  挂载路径 (Mount Path) 填写：`/app/data`
5.  进入 **Settings** -> **Variables**，添加一个新变量：
    *   **KEY**: `DB_PATH`
    *   **VALUE**: `/app/data/books.db`

设置完成后，Railway 会自动重新部署，以后你的数据就安全了！

## 第五步：获取后端网址

1.  等待部署成功（变成绿色）。
2.  在 **Settings** -> **Networking** 里，点击 **Generate Domain**。
3.  你会得到一个类似 `https://book-ocr-backend-production.up.railway.app` 的网址。
4.  **复制这个网址**，这就是你的后端地址！

---

## 最后的步骤：配置小程序

1.  用 HBuilderX 打开 `frontend` 目录。
2.  打开 `manifest.json` -> **微信小程序配置**。
3.  把 AppID 填进去。
4.  打开 `utils/config.js`（如果没有就直接改代码），把里面的 API 地址换成上面那个 Railway 的网址。
    *   或者更简单的，在微信开发者工具里：点击右上角 **详情** -> **本地设置** -> 勾选 **不校验合法域名**（仅限开发测试）。
    *   如果要正式发布给别人用，必须去 [微信公众平台](https://mp.weixin.qq.com/) -> **开发管理** -> **开发设置** -> **服务器域名**，把 Railway 的网址填到 `request合法域名` 和 `uploadFile合法域名` 里。

一切就绪！祝发布顺利！🎉
