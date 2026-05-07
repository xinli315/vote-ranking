import os
import requests
import json
import time
from flask import Flask, render_template, jsonify
from datetime import datetime

# 核心修复：精准定位模板文件夹，适配云端和本地环境
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

# 缓存数据
cache = {
    "data": [],
    "last_updated": None,
    "active_name": "实时排名系统",
    "error_msg": None
}

session = requests.Session()

def fetch_ranking():
    """从 API 获取所有分组的排名数据，带有重试机制"""
    all_players = []
    active_name = cache["active_name"]
    
    # 分组列表
    groups = [
        {"id": 42937, "name": "视频组"},
        {"id": 42936, "name": "图文组"}
    ]
    
    try:
        # 先尝试访问主页获取 Cookie
        try:
            session.get("https://2323.weixin00pingxuan.vote520.cn/42/?art=M95GLnR&tab=3", headers={"User-Agent": HEADERS["User-Agent"]}, timeout=5)
        except:
            pass

        for group in groups:
            success = False
            last_err = ""
            for attempt in range(2):
                payload = {
                    "page": 1,
                    "token": TOKEN,
                    "group_id": group["id"]
                }
                try:
                    res = session.post(API_BASE + "rankingdata.html", headers=HEADERS, data=payload, timeout=15)
                    if res.status_code == 200:
                        result = res.json()
                        if "active" in result:
                            active_name = result["active"].get("active_name", active_name)
                        
                        items = result.get("player", {}).get("data", [])
                        if items:
                            for item in items:
                                all_players.append({
                                    "id": item.get("id"),
                                    "name": item.get("playername"),
                                    "votes": item.get("votenum", 0),
                                    "group": group["name"],
                                    "image": item.get("player_image", [""])[0] if item.get("player_image") else "",
                                    "rank_in_group": item.get("rond")
                                })
                            success = True
                            break
                        else:
                            last_err = f"{group['name']} 返回数据为空"
                    else:
                        last_err = f"API 返回状态码 {res.status_code}"
                except Exception as e:
                    last_err = str(e)
                    time.sleep(1)
            
            if not success:
                cache["error_msg"] = f"抓取 {group['name']} 失败: {last_err}"
                return False, cache["error_msg"]

        all_players.sort(key=lambda x: int(x["votes"]) if x["votes"] else 0, reverse=True)
        cache["data"] = all_players
        cache["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cache["active_name"] = active_name
        cache["error_msg"] = None
        return True, None
    except Exception as e:
        return False, str(e)

@app.route('/')
def index():
    if not cache["data"]:
        fetch_ranking()
    return render_template('index.html', 
                           players=cache["data"], 
                           last_updated=cache["last_updated"],
                           active_name=cache["active_name"])

@app.route('/api/refresh')
def refresh():
    success, error_msg = fetch_ranking()
    return jsonify({
        "success": success,
        "error": error_msg,
        "data": cache["data"],
        "last_updated": cache["last_updated"]
    })

if __name__ == '__main__':
    # 本地运行逻辑
    fetch_ranking()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
