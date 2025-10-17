# 📬 DMCA Google Play Monitor

一个自动化脚本，每天从 [Lumen Database](https://lumendatabase.org) 抓取与 **Google Play** 相关的 DMCA 投诉并发送邮件报告。

## 🚀 部署指南（Render）

1. Fork 或上传此项目到你的 GitHub。
2. 登录 [Render.com](https://render.com)。
3. 创建 **Cron Job**：
   - Command: `python dmca_crawler.py`
   - Schedule: `0 6 * * *`
4. 在 Render 项目中添加以下环境变量：
