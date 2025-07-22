from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction
)
import json
import os

app = Flask(__name__)

# LINE Bot 設定 - 稍後需要填入你的實際 Token
# 改成從環境變數讀取，本地開發時使用預設值
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'YOUR_LOCAL_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', 'YOUR_LOCAL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


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


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """處理文字訊息"""
    user_message = event.message.text
    user_id = event.source.user_id

    # 載入用戶資料
    user_data = load_json_file('user_data.json')

    # 根據用戶訊息回應
    if user_message == "搜尋職缺":
        reply_text = "請輸入你想搜尋的職缺關鍵字，例如：\n• Python工程師\n• 前端開發\n• 數據分析師\n• 遠端工作"

    elif user_message == "我的收藏":
        # 檢查用戶是否有收藏職缺
        favorites = user_data.get('favorites', {}).get(user_id, [])
        if favorites:
            reply_text = f"你目前收藏了 {len(favorites)} 個職缺\n(收藏功能開發中...)"
        else:
            reply_text = "你還沒有收藏任何職缺唷！\n可以搜尋職缺後進行收藏 💾"

    elif user_message == "熱門標籤":
        reply_text = "🏷️ 熱門職缺標籤：\n\n• #遠端工作\n• #外商公司\n• #新創公司\n• #高薪職缺\n• #Python開發\n• #前端工程師\n• #數據分析\n• #產品經理"

    elif user_message == "使用說明":
        reply_text = """
🤖 職涯助手使用說明

🔍 搜尋職缺：
   輸入關鍵字搜尋相關職缺

💾 我的收藏：
   查看已收藏的職缺清單

🏷️ 熱門標籤：
   瀏覽熱門職缺分類

📝 其他功能：
   • 直接輸入職缺關鍵字進行搜尋
   • 收藏感興趣的職缺
   • 設定職缺提醒

如有問題請聯繫開發者！
        """

    elif user_message.startswith(("你好", "hi", "hello", "嗨")):
        reply_text = f"你好！歡迎使用職涯助手 🎯\n\n我可以幫你搜尋多個平台的職缺資訊，讓找工作更有效率！\n\n請選擇你需要的功能："

    else:
        # 當作職缺搜尋關鍵字處理
        reply_text = f"正在搜尋「{user_message}」相關職缺...\n\n(搜尋功能開發中，請稍後再試！)\n\n目前支援的功能請點選下方選單 👇"

    # 回應訊息
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=reply_text,
            quick_reply=create_quick_reply()
        )
    )


@app.route('/')
def home():
    """首頁 - 檢查服務狀態"""
    return "職涯助手 LINE Bot 正在運行中！ 🚀"


@app.route('/test')
def test():
    """測試頁面"""
    return {
        "status": "OK",
        "message": "LINE Bot 測試成功！",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    # 部署時使用環境變數的 PORT，本地開發使用 5001
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)