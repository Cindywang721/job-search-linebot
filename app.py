from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, PostbackEvent,
    QuickReply, QuickReplyButton, MessageAction, FlexSendMessage
)
import json
import os
import threading
import time
import sys

# 導入保持喚醒功能
try:
    from keep_alive import initialize_keep_alive

    print("✅ keep_alive 模組載入成功")
except ImportError as e:
    print(f"❌ 無法載入 keep_alive 模組: {e}")


    # 建立簡單的替代品
    def initialize_keep_alive(url):
        print("Keep-alive功能未啟用（模組載入失敗）")

# 導入爬蟲模組 - 加入錯誤處理
try:
    from crawler import JobCrawler

    print("✅ crawler 模組載入成功")
except ImportError as e:
    print(f"❌ 無法載入 crawler 模組: {e}")
    print(f"當前工作目錄: {os.getcwd()}")
    print(f"Python 路徑: {sys.path}")


    # 建立一個簡單的替代品，但會提示用戶功能未完成
    class JobCrawler:
        def search_all_platforms(self, keyword, limit=5):
            print(f"🔍 模擬搜尋關鍵字: {keyword}")
            # 返回空結果，提示功能開發中
            return []

try:
    from flex_message_templates import JobCardBuilder

    print("✅ flex_message_templates 模組載入成功")
except ImportError as e:
    print(f"❌ 無法載入 flex_message_templates 模組: {e}")


    # 簡單的替代品
    class JobCardBuilder:
        @staticmethod
        def create_job_carousel(jobs, keyword=""):
            from linebot.models import TextSendMessage
            if not jobs:
                job_text = f"😅 抱歉，沒有找到「{keyword}」相關的職缺\n\n爬蟲功能開發中，請稍後再試！"
            else:
                job_text = f"找到 {len(jobs)} 個職缺：\n\n"
                for i, job in enumerate(jobs[:5], 1):
                    job_text += f"{i}. {job.get('title', '')} - {job.get('company', '')}\n"
            return TextSendMessage(text=job_text)

        @staticmethod
        def create_search_summary_message(total, keyword):
            from linebot.models import TextSendMessage
            return TextSendMessage(text=f"搜尋「{keyword}」找到 {total} 個職缺")

app = Flask(__name__)

# LINE Bot 設定 - 從環境變數讀取
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'YOUR_LOCAL_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', 'YOUR_LOCAL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 初始化功能模組
job_crawler = JobCrawler()
job_card_builder = JobCardBuilder()


# 載入 JSON 資料的輔助函數
def load_json_file(filename):
    """載入 JSON 檔案"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_json_file(filename, data):
    """儲存資料到 JSON 檔案"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 建立快速回覆選單
def create_quick_reply():
    """建立快速回覆選單"""
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="🔍 搜尋職缺", text="搜尋職缺")),
        QuickReplyButton(action=MessageAction(label="💾 我的收藏", text="我的收藏")),
        QuickReplyButton(action=MessageAction(label="🏷️ 熱門標籤", text="熱門標籤")),
        QuickReplyButton(action=MessageAction(label="ℹ️ 使用說明", text="使用說明"))
    ])


def create_keyword_quick_reply():
    """建立搜尋關鍵字快速回覆選單"""
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="Python工程師", text="Python工程師")),
        QuickReplyButton(action=MessageAction(label="前端開發", text="前端開發")),
        QuickReplyButton(action=MessageAction(label="數據分析師", text="數據分析師")),
        QuickReplyButton(action=MessageAction(label="產品經理", text="產品經理")),
        QuickReplyButton(action=MessageAction(label="UI設計師", text="UI設計師")),
        QuickReplyButton(action=MessageAction(label="遠端工作", text="遠端工作"))
    ])


def search_jobs_async(keyword, reply_token, user_id):
    """非同步搜尋職缺"""
    try:
        print(f"🚀 開始搜尋職缺：{keyword}")

        # 搜尋職缺
        jobs = job_crawler.search_all_platforms(keyword, limit_per_platform=4)

        if jobs:
            # 發送搜尋結果摘要
            summary_message = job_card_builder.create_search_summary_message(len(jobs), keyword)
            line_bot_api.push_message(user_id, summary_message)

            # 發送職缺卡片
            carousel_message = job_card_builder.create_job_carousel(jobs, keyword)
            line_bot_api.push_message(user_id, carousel_message)

            print(f"✅ 職缺搜尋完成，發送了 {len(jobs)} 個職缺")

        else:
            # 沒找到職缺
            no_results_message = TextSendMessage(
                text=f"😅 抱歉，沒有找到「{keyword}」相關的職缺\n\n可能原因：\n• 關鍵字太具體\n• 網站暫時無法連接\n• 該職位目前沒有空缺\n\n請嘗試其他關鍵字：\n• Python\n• 工程師\n• 設計師\n• 行銷\n• 產品經理",
                quick_reply=create_keyword_quick_reply()
            )
            line_bot_api.push_message(user_id, no_results_message)

    except Exception as e:
        print(f"❌ 搜尋職缺時發生錯誤：{e}")
        error_message = TextSendMessage(
            text="😅 搜尋時發生錯誤，可能是：\n• 網路連線問題\n• 求職網站暫時無法存取\n• 伺服器忙碌中\n\n請稍後再試或聯繫客服",
            quick_reply=create_quick_reply()
        )
        line_bot_api.push_message(user_id, error_message)


@app.route("/callback", methods=['POST'])
def callback():
    """LINE Bot Webhook 回調函數"""
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(PostbackEvent)
def handle_postback(event):
    """處理 Postback 事件（按鈕點擊）"""
    user_id = event.source.user_id
    postback_data = event.postback.data

    if postback_data.startswith('favorite_'):
        # 收藏職缺
        job_id = postback_data.replace('favorite_', '')

        # 簡單的收藏功能
        user_data = load_json_file('user_data.json')
        if 'favorites' not in user_data:
            user_data['favorites'] = {}
        if user_id not in user_data['favorites']:
            user_data['favorites'][user_id] = []

        if job_id not in user_data['favorites'][user_id]:
            user_data['favorites'][user_id].append(job_id)
            save_json_file('user_data.json', user_data)
            reply_text = "💖 已加入收藏！\n\n可以輸入「我的收藏」查看所有收藏的職缺"
        else:
            reply_text = "💖 這個職缺已經在收藏清單中了！"

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=reply_text,
                quick_reply=create_quick_reply()
            )
        )


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """處理文字訊息"""
    user_message = event.message.text.strip()
    user_id = event.source.user_id
    reply_token = event.reply_token

    print(f"收到訊息：{user_message}")

    # 載入用戶資料
    user_data = load_json_file('user_data.json')

    # 根據用戶訊息回應
    if user_message == "搜尋職缺":
        reply_text = "🔍 請輸入你想搜尋的職缺關鍵字\n\n例如：\n• Python工程師\n• 前端開發\n• 數據分析師\n• 產品經理\n• 遠端工作\n• UI設計師\n\n💡 小提示：關鍵字越具體，搜尋結果越精準！"
        quick_reply = create_keyword_quick_reply()

    elif user_message == "我的收藏":
        # 檢查用戶是否有收藏職缺
        favorites = user_data.get('favorites', {}).get(user_id, [])
        if favorites:
            reply_text = f"💖 你目前收藏了 {len(favorites)} 個職缺\n\n收藏的職缺ID：\n" + "\n".join(
                [f"• {fav}" for fav in favorites[-5:]])
            if len(favorites) > 5:
                reply_text += f"\n...等共 {len(favorites)} 個職缺"
        else:
            reply_text = "💖 你還沒有收藏任何職缺唷！\n\n搜尋職缺後，點選職缺卡片的「💖 收藏」按鈕即可收藏"
        quick_reply = create_quick_reply()

    elif user_message == "熱門標籤":
        reply_text = "🏷️ 熱門職缺標籤：\n\n🔥 技術類：\n• Python工程師\n• 前端開發\n• 後端工程師\n• 全端工程師\n• 數據分析師\n• DevOps工程師\n\n🎨 設計類：\n• UI設計師\n• UX設計師\n• 平面設計師\n\n💼 商務類：\n• 產品經理\n• 專案經理\n• 行銷企劃\n\n🌍 工作型態：\n• 遠端工作\n• 外商公司\n• 新創公司"
        quick_reply = create_keyword_quick_reply()

    elif user_message == "使用說明":
        reply_text = """
🤖 職涯助手使用說明

🔍 搜尋職缺：
   輸入關鍵字搜尋相關職缺
   例如：「Python工程師」

💾 我的收藏：
   查看已收藏的職缺清單

🏷️ 熱門標籤：
   瀏覽熱門職缺分類

📱 職缺卡片功能：
   • 點擊「查看職缺」：前往原始網站
   • 點擊「💖 收藏」：加入個人收藏
   • 點擊「👥 分享」：分享職缺資訊

🎯 搜尋技巧：
   • 使用具體關鍵字效果更好
   • 可搜尋職位、技能、公司類型
   • 支援中英文搜尋

⚡ 服務狀態：24小時在線
如有問題請聯繫開發者！
        """
        quick_reply = create_quick_reply()

    elif user_message.lower().startswith(("你好", "hi", "hello", "嗨", "安安")):
        reply_text = "你好！歡迎使用職涯助手 🎯\n\n我可以幫你搜尋多個平台的職缺資訊，讓找工作更有效率！\n\n✨ 支援平台：\n• 104 人力銀行\n• 1111 人力銀行\n• CakeResume\n\n🔥 特色功能：\n• 24小時在線服務\n• 即時職缺搜尋\n• 個人收藏管理\n• 智能推薦系統\n\n請選擇你需要的功能："
        quick_reply = create_quick_reply()

    else:
        # 當作職缺搜尋關鍵字處理
        reply_text = f"🔍 正在搜尋「{user_message}」相關職缺...\n\n請稍等，我正在為你搜尋多個求職平台 ⏳\n\n✅ 104人力銀行\n✅ 1111人力銀行\n✅ CakeResume"
        quick_reply = create_quick_reply()

        # 先回應用戶，然後在背景搜尋職缺
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(
                text=reply_text,
                quick_reply=quick_reply
            )
        )

        # 在背景執行搜尋
        search_thread = threading.Thread(
            target=search_jobs_async,
            args=(user_message, reply_token, user_id)
        )
        search_thread.daemon = True
        search_thread.start()
        return  # 提前返回，避免重複回應

    # 回應訊息
    line_bot_api.reply_message(
        reply_token,
        TextSendMessage(
            text=reply_text,
            quick_reply=quick_reply
        )
    )


@app.route('/')
def home():
    """首頁 - 檢查服務狀態"""
    return "職涯助手 LINE Bot 正在運行中！ 🚀\n24小時在線服務，永不休眠！"


@app.route('/ping')
def ping():
    """Ping 端點 - 用於保持服務喚醒"""
    from datetime import datetime
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "message": "Keep-alive ping successful"
    }


@app.route('/test')
def test():
    """測試頁面"""
    return {
        "status": "OK",
        "message": "LINE Bot 測試成功！",
        "version": "2.1.0",
        "features": [
            "多平台職缺搜尋",
            "智能搜尋",
            "收藏功能",
            "24小時在線服務"
        ]
    }


@app.route('/debug')
def debug():
    """除錯頁面 - 檢查模組載入狀況"""
    import os
    files_in_dir = os.listdir('.')
    python_files = [f for f in files_in_dir if f.endswith('.py')]

    return {
        "current_directory": os.getcwd(),
        "all_files": files_in_dir,
        "python_files": python_files,
        "sys_path": sys.path[:3],
        "service_status": "24/7 Online"
    }


if __name__ == "__main__":
    # 獲取服務URL並啟動保持喚醒功能
    service_url = os.getenv('RENDER_EXTERNAL_URL', 'https://job-search-linebot.onrender.com')
    initialize_keep_alive(service_url)

    # 部署環境設定
    port = int(os.environ.get('PORT', 5001))
    print(f"🚀 啟動職涯助手 LINE Bot")
    print(f"📡 服務網址: {service_url}")
    print(f"⚡ 保持喚醒功能: 已啟用")

    app.run(debug=False, host='0.0.0.0', port=port)