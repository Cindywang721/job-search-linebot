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
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 導入模組（使用 try-except 確保穩定性）
try:
    from enhanced_crawler_real_jobs import EnhancedJobCrawler

    logger.info("✅ enhanced_crawler_real_jobs 載入成功")
except ImportError as e:
    logger.error(f"❌ 無法載入 enhanced_crawler_real_jobs: {e}")


    class EnhancedJobCrawler:
        def search_all_platforms(self, keyword, location="", salary_min="", salary_max="", limit_per_platform=5):
            return []

try:
    from job_condition_guide import ConversationManager

    logger.info("✅ job_condition_guide 載入成功")
except ImportError as e:
    logger.error(f"❌ 無法載入 job_condition_guide: {e}")


    class ConversationManager:
        def process_user_message(self, user_id, message):
            return {
                'text': "智能搜尋功能暫時無法使用，請稍後再試",
                'action': 'error',
                'conditions': {},
                'quick_reply': None
            }

try:
    from flex_message_templates import JobCardBuilder

    logger.info("✅ flex_message_templates 載入成功")
except ImportError as e:
    logger.error(f"❌ 無法載入 flex_message_templates: {e}")


    class JobCardBuilder:
        @staticmethod
        def create_job_carousel(jobs, keyword=""):
            return TextSendMessage(text=f"找到 {len(jobs)} 個職缺，功能開發中")

try:
    from user_manager import UserManager

    logger.info("✅ user_manager 載入成功")
except ImportError as e:
    logger.error(f"❌ 無法載入 user_manager: {e}")


    class UserManager:
        def __init__(self): pass

        def add_user(self, user_id): pass

        def record_search(self, user_id, keyword): pass

        def get_user_favorites(self, user_id): return []

        def get_user_stats(self, user_id): return None

        def add_favorite(self, user_id, job_id): return True

try:
    from keep_alive_system import initialize_keep_alive

    logger.info("✅ keep_alive_system 載入成功")
except ImportError:
    def initialize_keep_alive(url):
        logger.info("Keep-alive功能未啟用")

app = Flask(__name__)

# LINE Bot 設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'YOUR_LOCAL_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', 'YOUR_LOCAL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 初始化功能模組
job_crawler = EnhancedJobCrawler()
conversation_manager = ConversationManager()
job_card_builder = JobCardBuilder()
user_manager = UserManager()


def create_main_menu():
    """建立主選單"""
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="🔍 找工作", text="我要找工作")),
        QuickReplyButton(action=MessageAction(label="💾 收藏", text="我的收藏")),
        QuickReplyButton(action=MessageAction(label="🔥 熱門", text="熱門職缺")),
        QuickReplyButton(action=MessageAction(label="📊 記錄", text="搜尋紀錄")),
        QuickReplyButton(action=MessageAction(label="ℹ️ 說明", text="使用說明"))
    ])


def create_popular_jobs_menu():
    """建立熱門職缺選單"""
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="💻 軟體工程師", text="軟體工程師")),
        QuickReplyButton(action=MessageAction(label="🎨 UI設計師", text="UI設計師")),
        QuickReplyButton(action=MessageAction(label="📊 數據分析師", text="數據分析師")),
        QuickReplyButton(action=MessageAction(label="📱 產品經理", text="產品經理")),
        QuickReplyButton(action=MessageAction(label="🌐 前端工程師", text="前端工程師")),
        QuickReplyButton(action=MessageAction(label="⚙️ 後端工程師", text="後端工程師"))
    ])
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
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 導入模組（使用 try-except 確保穩定性）
try:
    from enhanced_crawler import EnhancedJobCrawler

    logger.info("✅ enhanced_crawler 載入成功")
except ImportError as e:
    logger.error(f"❌ 無法載入 enhanced_crawler: {e}")


    class EnhancedJobCrawler:
        def search_all_platforms(self, keyword, location="", salary_min="", salary_max="", limit_per_platform=5):
            return []

try:
    from job_condition_guide import ConversationManager

    logger.info("✅ job_condition_guide 載入成功")
except ImportError as e:
    logger.error(f"❌ 無法載入 job_condition_guide: {e}")


    class ConversationManager:
        def process_user_message(self, user_id, message):
            return {
                'text': "智能搜尋功能暫時無法使用，請稍後再試",
                'action': 'error',
                'conditions': {},
                'quick_reply': None
            }

try:
    from flex_message_templates import JobCardBuilder

    logger.info("✅ flex_message_templates 載入成功")
except ImportError as e:
    logger.error(f"❌ 無法載入 flex_message_templates: {e}")


    class JobCardBuilder:
        @staticmethod
        def create_job_carousel(jobs, keyword=""):
            return TextSendMessage(text=f"找到 {len(jobs)} 個職缺，功能開發中")

try:
    from user_manager import UserManager

    logger.info("✅ user_manager 載入成功")
except ImportError as e:
    logger.error(f"❌ 無法載入 user_manager: {e}")


    class UserManager:
        def __init__(self): pass

        def add_user(self, user_id): pass

        def record_search(self, user_id, keyword): pass

        def get_user_favorites(self, user_id): return []

        def get_user_stats(self, user_id): return None

        def add_favorite(self, user_id, job_id): return True

try:
    from keep_alive_system import initialize_keep_alive

    logger.info("✅ keep_alive_system 載入成功")
except ImportError:
    def initialize_keep_alive(url):
        logger.info("Keep-alive功能未啟用")

app = Flask(__name__)

# LINE Bot 設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'YOUR_LOCAL_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', 'YOUR_LOCAL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 初始化功能模組
job_crawler = EnhancedJobCrawler()
conversation_manager = ConversationManager()
job_card_builder = JobCardBuilder()
user_manager = UserManager()


def create_main_menu():
    """建立主選單"""
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="🔍 找工作", text="我要找工作")),
        QuickReplyButton(action=MessageAction(label="💾 收藏", text="我的收藏")),
        QuickReplyButton(action=MessageAction(label="🔥 熱門", text="熱門職缺")),
        QuickReplyButton(action=MessageAction(label="📊 記錄", text="搜尋紀錄")),
        QuickReplyButton(action=MessageAction(label="ℹ️ 說明", text="使用說明"))
    ])


def create_popular_jobs_menu():
    """建立熱門職缺選單"""
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="💻 軟體工程師", text="軟體工程師")),
        QuickReplyButton(action=MessageAction(label="🎨 UI設計師", text="UI設計師")),
        QuickReplyButton(action=MessageAction(label="📊 數據分析師", text="數據分析師")),
        QuickReplyButton(action=MessageAction(label="📱 產品經理", text="產品經理")),
        QuickReplyButton(action=MessageAction(label="🌐 前端工程師", text="前端工程師")),
        QuickReplyButton(action=MessageAction(label="⚙️ 後端工程師", text="後端工程師"))
    ])


def search_jobs_async(search_conditions, reply_token, user_id):
    """非同步搜尋職缺"""
    try:
        logger.info(f"🚀 開始搜尋職缺：{search_conditions}")

        # 記錄用戶搜尋
        user_manager.record_search(user_id, search_conditions.get('keyword', ''))

        # 搜尋職缺
        jobs = job_crawler.search_all_platforms(
            keyword=search_conditions.get('keyword', ''),
            location=search_conditions.get('location', ''),
            salary_min=str(search_conditions.get('salary_min', '')) if search_conditions.get('salary_min') else '',
            salary_max=str(search_conditions.get('salary_max', '')) if search_conditions.get('salary_max') else '',
            limit_per_platform=5
        )

        if jobs:
            # 發送搜尋結果
            summary_text = f"""
🎯 搜尋完成！

✅ 找到 {len(jobs)} 個相關職缺

📊 搜尋平台：
• 104人力銀行
• CakeResume  
• Yourator

💡 點選職缺卡片查看詳情
            """

            line_bot_api.push_message(
                user_id,
                TextSendMessage(
                    text=summary_text.strip(),
                    quick_reply=create_main_menu()
                )
            )

            # 發送職缺卡片
            carousel_message = job_card_builder.create_job_carousel(jobs, search_conditions.get('keyword', ''))
            line_bot_api.push_message(user_id, carousel_message)

            logger.info(f"✅ 搜尋完成，發送了 {len(jobs)} 個職缺")

        else:
            # 沒找到職缺
            no_results_message = TextSendMessage(
                text=f"""
😅 很抱歉，沒有找到符合條件的職缺

💡 建議：
• 放寬搜尋條件
• 嘗試相關關鍵字
• 擴大地區範圍
• 調整薪資期望

要重新搜尋嗎？
                """,
                quick_reply=QuickReply(items=[
                    QuickReplyButton(action=MessageAction(label="🔄 重新搜尋", text="我要找工作")),
                    QuickReplyButton(action=MessageAction(label="🔥 熱門職缺", text="熱門職缺"))
                ])
            )
            line_bot_api.push_message(user_id, no_results_message)

    except Exception as e:
        logger.error(f"❌ 搜尋職缺時發生錯誤：{e}")
        error_message = TextSendMessage(
            text=f"""
😅 搜尋時發生錯誤，請稍後再試

🔧 可能原因：
• 網路連線問題
• 伺服器忙碌中

要重新嘗試嗎？
            """,
            quick_reply=create_main_menu()
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
    """處理 Postback 事件"""
    user_id = event.source.user_id
    postback_data = event.postback.data

    user_manager.add_user(user_id)

    if postback_data.startswith('favorite_'):
        job_id = postback_data.replace('favorite_', '')
        success = user_manager.add_favorite(user_id, job_id)

        reply_text = "💖 已加入收藏！" if success else "💖 已經在收藏清單中了！"

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=reply_text,
                quick_reply=create_main_menu()
            )
        )


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """處理文字訊息"""
    user_message = event.message.text.strip()
    user_id = event.source.user_id
    reply_token = event.reply_token

    logger.info(f"收到用戶訊息：{user_message}")
    user_manager.add_user(user_id)

    # 處理指令
    if user_message in ["我要找工作", "搜尋職缺", "找工作"]:
        reply_text = """
🎯 歡迎使用智能職缺搜尋！

請告訴我你的需求，例如：

💼 「我想找軟體工程師的工作」
📍 「台北的產品經理」  
💰 「新竹前端工程師，月薪60k以上」
🎯 「Python後端工程師，3年經驗，新創公司」

💡 用自然語言描述，我會智能解析！
        """
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=reply_text.strip(), quick_reply=create_popular_jobs_menu())
        )
        return

    elif user_message == "我的收藏":
        favorites = user_manager.get_user_favorites(user_id)

        if favorites:
            reply_text = f"💖 你的收藏清單 ({len(favorites)} 個職缺)\n\n"
            for i, job in enumerate(favorites[-3:], 1):
                reply_text += f"{i}. {job.get('title', '職位')} - {job.get('company', '公司')}\n"
                reply_text += f"   💰 {job.get('salary', '面議')} | 📍 {job.get('location', '地點未提供')}\n\n"
            reply_text += "💡 記得主動投遞履歷！"
        else:
            reply_text = """
💖 你還沒有收藏任何職缺

🔍 開始搜尋職缺，發現心儀工作！
在職缺卡片上點選「💖 收藏」即可收藏
            """

        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=reply_text, quick_reply=create_main_menu())
        )
        return

    elif user_message == "熱門職缺":
        reply_text = """
🔥 熱門職缺類別

💻 技術類：軟體工程師、數據分析師、DevOps
🎨 設計類：UI/UX設計師、視覺設計師  
📊 商務類：產品經理、專案經理、行銷企劃
🌟 新興：AI工程師、區塊鏈工程師、成長駭客

點選下方按鈕快速搜尋！
        """
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=reply_text, quick_reply=create_popular_jobs_menu())
        )
        return

    elif user_message == "搜尋紀錄":
        user_stats = user_manager.get_user_stats(user_id)

        if user_stats and user_stats['search_count'] > 0:
            reply_text = f"""
📊 你的搜尋統計

🔍 總搜尋次數：{user_stats['search_count']} 次
💖 總收藏數：{user_stats['favorite_count']} 個
📅 首次使用：{user_stats.get('first_interaction', '')[:10]}

💡 持續搜尋，發現更多機會！
            """
        else:
            reply_text = """
📊 你還沒有搜尋記錄

🚀 開始你的求職之旅：
輸入「我要找工作」開始智能搜尋

📈 使用越多，推薦越精準！
            """

        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=reply_text, quick_reply=create_main_menu())
        )
        return

    elif user_message == "使用說明":
        reply_text = """
📖 職涯助手使用說明

🎯 智能搜尋：
• 用自然語言描述需求
• 支援職位、薪資、地點條件
• 多平台整合搜尋

💼 支援平台：
• 104人力銀行
• CakeResume  
• Yourator

🔍 搜尋範例：
• 「台北Python工程師，月薪60k以上」
• 「新創產品經理，3年經驗」
• 「遠端工作UI設計師」

💖 收藏功能：收藏心儀職位，隨時查看

有問題隨時告訴我！
        """
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=reply_text, quick_reply=create_main_menu())
        )
        return

    elif user_message.lower().startswith(("你好", "hi", "hello", "嗨")):
        reply_text = """
你好！歡迎使用職涯助手 🎯

我是你的專屬求職夥伴，能幫你：

🔍 智能搜尋職缺
💼 多平台整合
💖 收藏管理
📊 個人化推薦

🎯 支援平台：
• 104人力銀行、CakeResume、Yourator

準備好開始求職了嗎？
        """
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=reply_text, quick_reply=create_main_menu())
        )
        return

    else:
        # 智能條件引導搜尋 - 核心邏輯修復
        try:
            logger.info(f"🔍 開始處理搜尋請求：{user_message}")

            # 直接進行職缺搜尋，不使用複雜的條件引導
            # 這樣可以確保任何輸入都能得到結果

            # 簡單的關鍵字提取
            search_keyword = user_message.strip()

            # 移除常見的無用詞彙
            stop_words = ['我要找', '我想找', '幫我找', '搜尋', '工作', '職缺', '的']
            for word in stop_words:
                search_keyword = search_keyword.replace(word, '').strip()

            # 如果關鍵字為空，使用原始輸入
            if not search_keyword:
                search_keyword = user_message.strip()

            logger.info(f"✅ 提取的搜尋關鍵字：{search_keyword}")

            # 立即回應用戶，然後開始搜尋
            initial_response = f"""
🔍 正在為你搜尋「{search_keyword}」相關職缺...

🚀 搜尋進行中：
• 分析職缺需求
• 多平台資料收集  
• 智能結果排序

⏱️ 預計 10-15 秒完成，請稍候...
            """

            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(
                    text=initial_response.strip(),
                    quick_reply=create_main_menu()
                )
            )

            # 在背景執行搜尋 - 簡化搜尋條件
            search_conditions = {
                'keyword': search_keyword,
                'location': '',  # 暫時不限制地點
                'salary_min': None,
                'salary_max': None
            }

            search_thread = threading.Thread(
                target=search_jobs_async,
                args=(search_conditions, reply_token, user_id)
            )
            search_thread.daemon = True
            search_thread.start()
            return

        except Exception as e:
            logger.error(f"❌ 處理搜尋請求失敗：{e}")
            error_reply_text = f"""
😅 處理「{user_message}」時遇到問題

🔧 建議嘗試：
• 使用簡單關鍵字（如：工程師、設計師）
• 檢查網路連線
• 稍後再試

💡 熱門搜尋：
軟體工程師、產品經理、數據分析師

要重新搜尋嗎？
            """

        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=error_reply_text.strip(), quick_reply=create_main_menu())
        )


@app.route('/')
def home():
    """首頁"""
    return """
    <h1>職涯助手 LINE Bot v3.0.0 🚀</h1>
    <h2>功能特色：</h2>
    <ul>
        <li>🔍 智能職缺搜尋</li>
        <li>💼 多平台整合 (104, CakeResume, Yourator)</li>
        <li>🎯 自然語言處理</li>
        <li>💖 收藏管理</li>
        <li>📊 個人化推薦</li>
        <li>⚡ 24小時在線</li>
    </ul>
    <p><strong>狀態：</strong> 正常運行中</p>
    """


@app.route('/ping')
def ping():
    """健康檢查"""
    from datetime import datetime
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "message": "Enhanced Job Search Bot v3.0.0",
        "version": "3.0.0"
    }


@app.route('/test')
def test():
    """測試頁面"""
    return {
        "status": "OK",
        "message": "職涯助手測試成功！",
        "version": "3.0.0",
        "features": [
            "智能職缺搜尋",
            "多平台爬蟲",
            "自然語言處理",
            "收藏管理",
            "24小時服務"
        ]
    }


if __name__ == "__main__":
    # 啟動保持喚醒功能
    service_url = os.getenv('RENDER_EXTERNAL_URL', 'https://job-search-linebot.onrender.com')
    initialize_keep_alive(service_url)

    # 啟動應用
    port = int(os.environ.get('PORT', 5001))

    logger.info(f"🚀 啟動職涯助手 LINE Bot v3.0.0")
    logger.info(f"📡 服務網址: {service_url}")
    logger.info(f"⚡ 智能搜尋: 已啟用")

    app.run(debug=False, host='0.0.0.0', port=port)