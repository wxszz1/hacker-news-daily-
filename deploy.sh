#!/bin/bash
set -e

echo "=== Hacker News Agent 部署 ==="

# 1. 安装依赖
sudo apt update
sudo apt install -y python3.11 python3.11-venv

# 2. 克隆项目
sudo git clone <your-repo> /opt/hacker-news-agent
sudo chown -R $USER:$USER /opt/hacker-news-agent

cd /opt/hacker-news-agent

# 3. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 配置环境变量
cp .env.example .env
echo "请编辑 .env 文件填入 Server酱 SendKey"

# 6. 创建 systemd 服务
sudo cp config/hackernews.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable hackernews
sudo systemctl start hackernews

echo "=== 部署完成 ==="
echo "查看状态: sudo systemctl status hackernews"
echo "查看日志: sudo journalctl -u hackernews -f"
