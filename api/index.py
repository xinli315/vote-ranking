import os
import requests
import json
import time
from flask import Flask, render_template, jsonify
from datetime import datetime

# 精准定位 api 目录下的 templates
base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, 'templates')

app = Flask(__name__, template_folder=template_dir)

# 配置信息
TOKEN = "M95GLnR"
API_BASE = "https://00.00pingxuan.cn/huodong2/api/"
REFERER = "https://2323.weixin00pingxuan.vote520.cn/42/?art=M95GLnR&tab=3"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Referer": REFERER,
    "X-Requested-With": "XMLHttpRequest"
}

cache = {"data": [], "last_updated": None, "active_name": "实时排名系统"}
session = requests.Session()

def fetch_ranking():
    all_players = []
    try:
        # 尝试获取 Cookie
        try: session.get(REFERER, timeout=5)
        except: pass

        for gid, gname in [(42937, "视频组"), (42936, "图文组")]:
            payload = {"page": 1, "token": TOKEN, "group_id": gid}
            res = session.post(API_BASE + "rankingdata.html", headers=HEADERS, data=payload, timeout=15)
            if res.status_code == 200:
                result = res.json()
                items = result.get("player", {}).get("data", [])
                for item in items:
                    all_players.append({
                        "name": item.get("playername"),
                        "votes": item.get("votenum", 0),
                        "group": gname,
                        "image": item.get("player_image", [""])[0] if item.get("player_image") else ""
                    })
        all_players.sort(key=lambda x: int(x["votes"]) if x["votes"] else 0, reverse=True)
        cache["data"] = all_players
        cache["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return True
    except: return False

@app.route('/')
def index():
    if not cache["data"]: fetch_ranking()
    return render_template('index.html', players=cache["data"], last_updated=cache["last_updated"], active_name=cache["active_name"])

@app.route('/api/refresh')
def refresh():
    success = fetch_ranking()
    return jsonify({"success": success, "data": cache["data"], "last_updated": cache["last_updated"]})

# 这一行是 Vercel 识别的关键
app.debug = False
