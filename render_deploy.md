# Render 部署配置
# 1. 访问 https://dashboard.render.com/
# 2. 创建 New Web Service
# 3. 连接 GitHub 仓库或手动上传
# 4. 设置:
#    - Build Command: pip install -r requirements.txt
#    - Start Command: gunicorn app:app
# 5. 免费版即可运行

# 或者使用 Render Blueprint (render.yaml):
# https://render.com/docs/blueprint-spec

# 本地测试生产环境:
# gunicorn -w 4 -b 0.0.0.0:5000 app:app
