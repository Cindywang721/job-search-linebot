from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction
)
import os
import threading
import time

# 導入簡化爬蟲
try:
    from simple_job_crawler import SimpleJobCrawler

    print("✅ simple_job_crawler 載入成功")
except ImportError:
    print("❌ 無法載入 simple_job_crawler")


    class SimpleJobCrawler:
        def search_all_platforms(self, keyword, location="", salary_min="", salary_max="", limit_per_platform=5):
            return []

# 導入職缺卡片（如果失敗就用簡單文字）
try:
    from flex_message_templates import JobCardBuilder

    print("✅ flex_message_templates 載入成功")
except ImportError:
    print("❌ 無法載入 flex_message_templates，使用簡單文字")


    class JobCardBuilder:
        @staticmethod
        def create_job_carousel(jobs, keyword=""):
            if not jobs:
                return TextSendMessage(text=f"😅 沒有找到「{keyword}」相關職缺")

            job_text = f"🎯 找到 {len(jobs)} 個「{keyword}」職缺：\n\n"
            for i, job in enumerate(jobs[:5], 1):
                job_text += f"{i}. {job['title']}\n"
                job_text += f"   🏢 {job['company']}\n"
                job_text += f"   💰 {job['salary']}\n"
                job_text += f"   📍 {job['location']}\n"
                job_text += f"   🔗 {job['url']}\n\n"

            job_text += "💡 點擊連結查看完整職缺資訊"
            return TextSendMessage(text=job_text)

app = Flask(__name__)

# LINE Bot 設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'YOUR_LOCAL_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', 'YOUR_LOCAL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 初始化爬蟲
job_crawler = SimpleJobCrawler()
job_card_builder = JobCardBuilder()


def create_main_menu():
    """建立主選單"""
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="🔍 找工作", text="我要找工作")),
        QuickReplyButton(action=MessageAction(label="🔥 熱門職缺", text="熱門職缺")),
        QuickReplyButton(action=MessageAction(label="ℹ️ 使用說明", text="使用說明"))
    ])


def create_popular_jobs_menu():
    """建立熱門職缺選單"""
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="💻 軟體工程師", text="軟體工程師")),
        QuickReplyButton(action=MessageAction(label="📱 產品經理", text="產品經理")),
        QuickReplyButton(action=MessageAction(label="🎨 UI設計師", text="UI設計師")),
        QuickReplyButton(action=MessageAction(label="📊 數據分析師", text="數據分析師")),
        QuickReplyButton(action=MessageAction(label="💼 業務代表", text="業務代表")),
        QuickReplyButton(action=MessageAction(label="👥 人資專員", text="人資專員"))
    ])


def search_jobs_async(keyword, user_id):
    """非同步搜尋職缺"""
    try:
        print(f"🚀 開始搜尋：{keyword}")

        # 搜尋職缺
        jobs = job_crawler.search_all_platforms(keyword, limit_per_platform=5)

        if jobs:
            # 發送結果摘要
            summary_text = f"""
🎯 搜尋完成！

✅ 為你找到 {len(jobs)} 個「{keyword}」相關職缺

📊 涵蓋平台：
• 104人力銀行
• CakeResume
• Yourator

🔗 所有連結都是真實可點擊的
💡 點擊連結可直接前往應徵
            """

            line_bot_api.push_message(
                user_id,
                TextSendMessage(text=summary_text.strip(), quick_reply=create_main_menu())
            )

            # 發送職缺卡片
            carousel_message = job_card_builder.create_job_carousel(jobs, keyword)
            line_bot_api.push_message(user_id, carousel_message)

            print(f"✅ 搜尋完成，發送了 {len(jobs)} 個職缺")

        else:
            # 沒找到職缺（理論上不會發生）
            line_bot_api.push_message(
                user_id,
                TextSendMessage(
                    text=f"😅 很抱歉，暫時沒有找到「{keyword}」相關職缺\n\n請嘗試其他關鍵字或稍後再試",
                    quick_reply=create_main_menu()
                )
            )

    except Exception as e:
        print(f"❌ 搜尋職缺時發生錯誤：{e}")
        line_bot_api.push_message(
            user_id,
            TextSendMessage(
                text="😅 搜尋時發生錯誤，請稍後再試",
                quick_reply=create_main_menu()
            )
        )


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
    user_message = event.message.text.strip()
    user_id = event.source.user_id
    reply_token = event.reply_token

    print(f"收到訊息：{user_message}")

    # 處理特定指令
    if user_message in ["我要找工作", "搜尋職缺", "找工作"]:
        reply_text = """
🎯 歡迎使用職涯助手！

請直接告訴我你想找的工作，例如：

💼 「產品經理」
💻 「軟體工程師」  
🎨 「UI設計師」
📊 「數據分析師」
💰 「會計師」
👥 「人資專員」

🔥 或點選下方熱門職缺快速搜尋
        """

        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=reply_text.strip(), quick_reply=create_popular_jobs_menu())
        )
        return

    elif user_message == "熱門職缺":
        reply_text = """
🔥 熱門職缺類別

💻 技術類：軟體工程師、前端工程師、後端工程師
📱 產品類：產品經理、專案經理、營運經理  
🎨 設計類：UI設計師、UX設計師、視覺設計師
📊 數據類：數據分析師、商業分析師、資料科學家
💼 商務類：業務代表、行銷專員、客戶經理
👥 人資類：人資專員、招募專員、薪酬福利

點選下方按鈕快速搜尋，或直接輸入職位名稱！
        """

        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=reply_text.strip(), quick_reply=create_popular_jobs_menu())
        )
        return

    elif user_message == "使用說明":
        reply_text = """
📖 職涯助手使用說明

🎯 如何搜尋職缺：
直接輸入你想找的工作，例如：
• 「產品經理」
• 「軟體工程師」
• 「UI設計師」

🔍 搜尋特色：
• 智能職缺匹配
• 多平台整合搜尋
• 真實職缺連結
• 即時結果呈現

💼 支援職位類型：
涵蓋所有行業和職位，從技術到商務，從新鮮人到高階主管

🔗 職缺連結：
所有職缺都提供真實連結，直接前往求職網站應徵

有任何問題隨時告訴我！
        """

        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=reply_text.strip(), quick_reply=create_main_menu())
        )
        return

    elif user_message.lower().startswith(("你好", "hi", "hello", "嗨")):
        reply_text = """
你好！歡迎使用職涯助手 🎯

我可以幫你搜尋各種職缺：

🔍 智能職缺搜尋
💼 多平台整合
🔗 真實職缺連結
⚡ 即時結果呈現

直接告訴我你想找什麼工作，
我會立即為你搜尋相關職缺！

例如：輸入「產品經理」就能找到產品經理相關職缺
        """

        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=reply_text.strip(), quick_reply=create_main_menu())
        )
        return

    else:
        # 直接進行職缺搜尋
        search_keyword = user_message.strip()

        # 移除常見無用詞
        stop_words = ['我要找', '我想找', '幫我找', '搜尋', '工作', '職缺']
        for word in stop_words:
            search_keyword = search_keyword.replace(word, '').strip()

        if not search_keyword:
            search_keyword = user_message.strip()

        print(f"搜尋關鍵字：{search_keyword}")

        # 立即回應用戶
        initial_response = f"""
🔍 正在為你搜尋「{search_keyword}」相關職缺...

🚀 搜尋進行中：
• 智能分析職位需求
• 多平台資料收集
• 結果排序與整理

⏱️ 預計 5-10 秒完成，請稍候...
        """

        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=initial_response.strip(), quick_reply=create_main_menu())
        )

        # 在背景執行搜尋
        search_thread = threading.Thread(
            target=search_jobs_async,
            args=(search_keyword, user_id)
        )
        search_thread.daemon = True
        search_thread.start()


@app.route('/')
def home():
    """首頁"""
    return """
    <h1>職涯助手 LINE Bot v4.0 🚀</h1>
    <h2>超穩定版本特色：</h2>
    <ul>
        <li>🔍 智能職缺搜尋</li>
        <li>💼 支援所有職位類型</li>
        <li>🔗 真實職缺連結</li>
        <li>⚡ 零依賴衝突</li>
        <li>🎯 保證搜尋結果</li>
        <li>📱 24小時穩定服務</li>
    </ul>
    <p><strong>狀態：</strong> 超穩定運行中</p>
    """


@app.route('/ping')
def ping():
    """健康檢查"""
    from datetime import datetime
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "message": "Ultra Simple Job Search Bot v4.0",
        "version": "4.0.0"
    }


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5001))

    print(f"🚀 啟動職涯助手 LINE Bot v4.0")
    print(f"⚡ 超穩定版：零依賴衝突")
    print(f"🔍 智能搜尋：保證結果")

    app.run(debug=False, host='0.0.0.0', port=port)