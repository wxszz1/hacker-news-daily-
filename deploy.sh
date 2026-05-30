#!/bin/bash
set -e

echo "=== Hacker News Agent Deployment ==="

# 1. Install dependencies
sudo apt update
sudo apt install -y python3.11 python3.11-venv

# 2. Clone project
sudo git clone <your-repo> /opt/hacker-news-agent
sudo chown -R $USER:$USER /opt/hacker-news-agent

cd /opt/hacker-news-agent

# 3. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure environment
cp .env.example .env
echo "Please edit .env to add your Server酱 SendKey"

# 6. Create systemd service
sudo cp config/hackernews.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable hackernews
sudo systemctl start hackernews

echo "=== Deployment Complete ==="
echo "Check status: sudo systemctl status hackernews"
echo "View logs: sudo journalctl -u hackernews -f"
