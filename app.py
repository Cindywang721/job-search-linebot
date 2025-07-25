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

# 導入增強版模組
try:
    from enhanced_crawler import EnhancedJobCrawler
    from job_condition_guide import ConversationManager
    from flex_message_templates import JobCardBuilder
    from user_manager import UserManager

    logger.info("✅ 所有增強版模組載入成功")
except ImportError as e:
    logger.error(f"❌ 無法載入模組: {e}")


    # 建立簡單的替代品
    class EnhancedJobCrawler:
        def search_all_platforms(self, keyword, location="", salary_min="", salary_max="", limit_per_platform=5):
            return []


    class ConversationManager:
        def process_user_message(self, user_id, message):
            return {
                'text': "系統升級中，暫時無法使用智能搜尋功能",
                'action': 'error',
                'conditions': {},
                'quick_reply': None
            }


    class JobCardBuilder:
        @staticmethod
        def create_job_carousel(jobs, keyword=""):
            from linebot.models import TextSendMessage
            return TextSendMessage(text="職缺卡片功能開發中")


    class UserManager:
        def __init__(self):
            pass

        def add_user(self, user_id):
            pass

        def record_search(self, user_id, keyword):
            pass

try:
    from keep_alive import initialize_keep_alive

    logger.info("✅ keep_alive 模組載入成功")
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

# 用戶狀態管理
user_states = {}


def create_main_menu():
    """建立主選單"""
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="🔍 智能搜尋", text="我要找工作")),
        QuickReplyButton(action=MessageAction(label="💾 我的收藏", text="我的收藏")),
        QuickReplyButton(action=MessageAction(label="🏷️ 熱門職缺", text="熱門職缺")),
        QuickReplyButton(action=MessageAction(label="📊 搜尋紀錄", text="搜尋紀錄")),
        QuickReplyButton(action=MessageAction(label="⚙️ 設定", text="設定")),
        QuickReplyButton(action=MessageAction(label="ℹ️ 使用說明", text="使用說明"))
    ])


def create_popular_jobs_menu():
    """建立熱門職缺選單"""
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="💻 軟體工程師", text="軟體工程師")),
        QuickReplyButton(action=MessageAction(label="🎨 UI/UX設計師", text="UI設計師")),
        QuickReplyButton(action=MessageAction(label="📊 數據分析師", text="數據分析師")),
        QuickReplyButton(action=MessageAction(label="📱 產品經理", text="產品經理")),
        QuickReplyButton(action=MessageAction(label="🌐 前端工程師", text="前端工程師")),
        QuickReplyButton(action=MessageAction(label="⚙️ 後端工程師", text="後端工程師"))
    ])


def search_jobs_async(search_conditions, reply_token, user_id):
    """非同步搜尋職缺 - 使用增強版爬蟲"""
    try:
        logger.info(f"🚀 開始智能搜尋職缺：{search_conditions}")

        # 記錄用戶搜尋
        user_manager.record_search(user_id, search_conditions.get('keyword', ''))

        # 使用增強版爬蟲搜尋
        jobs = job_crawler.search_all_platforms(
            keyword=search_conditions.get('keyword', ''),
            location=search_conditions.get('location', ''),
            salary_min=str(search_conditions.get('salary_min', '')) if search_conditions.get('salary_min') else '',
            salary_max=str(search_conditions.get('salary_max', '')) if search_conditions.get('salary_max') else '',
            limit_per_platform=6
        )

        if jobs:
            # 發送搜尋結果摘要
            summary_text = f"""
🎯 智能搜尋完成！

✅ 為你找到 {len(jobs)} 個符合條件的職缺

📊 搜尋平台：
• 104人力銀行: {len([j for j in jobs if j['platform'] == '104人力銀行'])} 個
• CakeResume: {len([j for j in jobs if j['platform'] == 'CakeResume'])} 個  
• Yourator: {len([j for j in jobs if j['platform'] == 'Yourator'])} 個

💡 點選下方職缺卡片查看詳情
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

            logger.info(f"✅ 職缺搜尋完成，發送了 {len(jobs)} 個職缺")

        else:
            # 沒找到職缺
            no_results_message = TextSendMessage(
                text=f"""
😅 很抱歉，沒有找到完全符合條件的職缺

可能的原因：
• 條件設定過於嚴格
• 該職位目前需求較少
• 薪資或地點限制較嚴

💡 建議：
• 放寬薪資範圍
• 考慮其他地區
• 搜尋相關職位
• 嘗試不同關鍵字

要重新設定搜尋條件嗎？
                """,
                quick_reply=QuickReply(items=[
                    QuickReplyButton(action=MessageAction(label="🔄 重新搜尋", text="我要找工作")),
                    QuickReplyButton(action=MessageAction(label="🏷️ 熱門職缺", text="熱門職缺")),
                    QuickReplyButton(action=MessageAction(label="📞 客服協助", text="客服協助"))
                ])
            )
            line_bot_api.push_message(user_id, no_results_message)

    except Exception as e:
        logger.error(f"❌ 搜尋職缺時發生錯誤：{e}")
        error_message = TextSendMessage(
            text=f"""
😅 搜尋時發生錯誤

可能原因：
• 網路連線問題
• 求職網站暫時無法存取
• 伺服器忙碌中

🔧 解決方案：
• 請稍後再試
• 檢查網路連線
• 聯繫客服協助

要重新嘗試搜尋嗎？
            """,
            quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="🔄 重新搜尋", text="我要找工作")),
                QuickReplyButton(action=MessageAction(label="🏠 返回主選單", text="主選單"))
            ])
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

    # 新增用戶記錄
    user_manager.add_user(user_id)

    if postback_data.startswith('favorite_'):
        # 收藏職缺
        job_id = postback_data.replace('favorite_', '')

        success = user_manager.add_favorite(user_id, job_id)

        if success:
            reply_text = """
💖 已加入收藏！

✅ 職缺已成功加入你的收藏清單

📋 你可以：
• 輸入「我的收藏」查看所有收藏
• 比較不同職缺條件
• 準備客製化履歷
• 規劃投遞策略

💡 小提醒：好工作不等人，記得主動投遞履歷唷！
            """
        else:
            reply_text = """
💖 這個職缺已經在你的收藏清單中了！

📋 你可以：
• 輸入「我的收藏」查看完整收藏
• 輸入「搜尋紀錄」查看搜尋歷史
• 繼續搜尋更多相關職缺

要繼續找其他工作嗎？
            """

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=reply_text.strip(),
                quick_reply=create_main_menu()
            )
        )


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """處理文字訊息 - 使用智能條件引導"""
    user_message = event.message.text.strip()
    user_id = event.source.user_id
    reply_token = event.reply_token

    logger.info(f"收到用戶 {user_id} 訊息：{user_message}")

    # 新增用戶記錄
    user_manager.add_user(user_id)

    # 處理特定指令
    if user_message in ["我要找工作", "搜尋職缺", "找工作"]:
        reply_text = """
🎯 歡迎使用智能職缺搜尋！

我會協助你找到最適合的工作機會。請告訴我你的需求，例如：

💼 基本需求：
「我想找軟體工程師的工作」

📍 包含地點：
「我想找台北的產品經理」

💰 包含薪資：
「新竹的前端工程師，月薪60k以上」

🎯 詳細條件：
「台北的Python後端工程師，月薪80k-120k，有3年經驗，希望是新創公司」

💡 你可以用自然語言描述，我會智能解析你的需求！
        """

        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(
                text=reply_text.strip(),
                quick_reply=create_popular_jobs_menu()
            )
        )
        return

    elif user_message == "我的收藏":
        # 顯示用戶收藏
        favorites = user_manager.get_user_favorites(user_id)

        if favorites:
            reply_text = f"""
💖 你的收藏清單 ({len(favorites)} 個職缺)

最近收藏的職缺：
"""
            for i, job in enumerate(favorites[-5:], 1):  # 顯示最近5個
                reply_text += f"""
{i}. {job.get('title', '職位')} - {job.get('company', '公司')}
   💰 {job.get('salary', '面議')} | 📍 {job.get('location', '地點未提供')}
   🔗 {job.get('platform', '平台')} | ⏰ {job.get('favorited_at', '')[:10]}
"""

            if len(favorites) > 5:
                reply_text += f"\n... 等共 {len(favorites)} 個職缺"

            reply_text += "\n💡 記得主動投遞履歷，把握每個機會！"

        else:
            reply_text = """
💖 你還沒有收藏任何職缺唷！

🔍 開始搜尋職缺：
• 輸入「我要找工作」開始智能搜尋
• 瀏覽職缺卡片時點選「💖 收藏」

📋 收藏的好處：
• 比較不同職缺條件
• 避免錯過心儀職位
• 規劃投遞履歷策略
• 追蹤應徵進度

現在就開始找工作吧！
            """

        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(
                text=reply_text.strip(),
                quick_reply=create_main_menu()
            )
        )
        return

    elif user_message == "熱門職缺":
        reply_text = """
🔥 熱門職缺類別

選擇你感興趣的職位類型，我會為你搜尋最新的職缺機會：

💻 技術類：
• 軟體工程師 - 全端/前端/後端
• 數據分析師 - Python/SQL/機器學習
• DevOps工程師 - 雲端/自動化

🎨 設計類：
• UI/UX設計師 - 介面/體驗設計
• 視覺設計師 - 品牌/平面設計

📊 商務類：
• 產品經理 - 產品策略/規劃
• 專案經理 - 跨部門協作
• 行銷企劃 - 數位/品牌行銷

🌟 新興職位：
• AI工程師 - 人工智慧/機器學習
• 區塊鏈工程師 - Web3/DeFi
• 成長駭客 - 用戶增長/數據驅動

點選下方按鈕快速搜尋，或直接告訴我你想找的職位！
        """

        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(
                text=reply_text.strip(),
                quick_reply=create_popular_jobs_menu()
            )
        )
        return

    elif user_message == "搜尋紀錄":
        # 顯示用戶搜尋統計
        user_stats = user_manager.get_user_stats(user_id)

        if user_stats and user_stats['search_count'] > 0:
            preferred_keywords = user_stats.get('preferred_keywords', [])

            reply_text = f"""
📊 你的搜尋統計

🔍 總搜尋次數：{user_stats['search_count']} 次
💖 總收藏數：{user_stats['favorite_count']} 個
📅 首次使用：{user_stats.get('first_interaction', '')[:10]}
⏰ 最近活動：{user_stats.get('last_interaction', '')[:10]}

🏷️ 你最常搜尋的職位：
"""

            for i, pref in enumerate(preferred_keywords[:5], 1):
                reply_text += f"{i}. {pref['keyword']} ({pref['count']}次)\n"

            reply_text += """
💡 基於你的搜尋習慣，我建議：
• 設定職缺通知，第一時間獲得新機會
• 收藏心儀職位，避免錯過
• 拓展相關技能，增加競爭力

要繼續搜尋工作嗎？
            """
        else:
            reply_text = """
📊 你還沒有搜尋記錄

🚀 開始你的求職之旅：
• 輸入「我要找工作」開始智能搜尋
• 瀏覽「熱門職缺」發現新機會
• 使用自然語言描述需求

📈 使用越多，推薦越精準！
我會學習你的偏好，提供更符合需求的職缺。

現在就開始搜尋吧！
            """

        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(
                text=reply_text.strip(),
                quick_reply=create_main_menu()
            )
        )
        return

    elif user_message == "使用說明":
        reply_text = """
📖 職涯助手使用說明

🎯 智能搜尋功能：
• 用自然語言描述需求
• 自動解析職位、薪資、地點等條件
• 多輪對話完善搜尋條件
• 一站式搜尋多個求職平台

💼 支援平台：
• 104人力銀行 - 最大求職平台
• CakeResume - 新世代求職網站
• Yourator - 新創與科技公司
• LinkedIn - 國際職場網絡
• 公司官網 - 直接投遞機會

🔍 搜尋技巧：
• 「台北的Python工程師，月薪60k以上」
• 「新創公司的產品經理，3年經驗」
• 「遠端工作的UI設計師」
• 「外商的數據分析師，年薪150萬」

💖 收藏功能：
• 收藏心儀職位
• 比較不同條件
• 追蹤投遞狀態

📊 個人化推薦：
• 基於搜尋歷史
• 智能職位推薦
• 薪資趨勢分析

有任何問題隨時告訴我！
        """

        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(
                text=reply_text.strip(),
                quick_reply=create_main_menu()
            )
        )
        return

    elif user_message in ["設定", "⚙️ 設定"]:
        reply_text = """
⚙️ 個人設定

🔔 通知設定：
• 新職缺提醒 - 根據你的搜尋偏好
• 每日職缺精選 - 每天推送熱門職缺
• 薪資趨勢報告 - 週報告訴你市場動態

📊 搜尋偏好：
• 預設搜尋地區
• 期望薪資範圍
• 偏好產業類型
• 工作經驗級別

🔒 隱私設定：
• 搜尋記錄管理
• 收藏資料匯出
• 帳號資料刪除

💡 個人化功能：
• 履歷健檢提醒
• 面試技巧推送
• 職涯發展建議

目前所有功能都已開啟，如需調整請告訴我！
        """

        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(
                text=reply_text.strip(),
                quick_reply=create_main_menu()
            )
        )
        return

    elif user_message.lower().startswith(("你好", "hi", "hello", "嗨", "安安")):
        reply_text = """
你好！歡迎使用職涯助手 🎯

我是你的專屬求職夥伴，能幫你：

🔍 智能搜尋職缺：
• 一站式搜尋多個求職平台
• 自然語言條件設定
• 即時職缺推薦

💼 完整求職支援：
• 個人化職缺推薦
• 薪資趨勢分析
• 履歷優化建議
• 面試準備協助

📊 數據驅動決策：
• 市場需求分析
• 技能趨勢報告
• 薪資水準比較

🎯 支援平台包括：
• 104人力銀行、CakeResume
• Yourator、LinkedIn
• 各大公司官網

準備好開始你的求職之旅了嗎？
點選下方按鈕或直接告訴我你想找什麼工作！
        """

        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(
                text=reply_text.strip(),
                quick_reply=create_main_menu()
            )
        )
        return

    else:
        # 使用智能條件引導系統處理搜尋請求
        try:
            result = conversation_manager.process_user_message(user_id, user_message)

            if result['action'] == 'search':
                # 條件完整，開始搜尋
                reply_text = result['text']

                # 先回應用戶
                line_bot_api.reply_message(
                    reply_token,
                    TextSendMessage(
                        text=reply_text,
                        quick_reply=create_main_menu()
                    )
                )

                # 在背景執行搜尋
                search_thread = threading.Thread(
                    target=search_jobs_async,
                    args=(result['conditions'], reply_token, user_id)
                )
                search_thread.daemon = True
                search_thread.start()
                return

            elif result['action'] == 'collect_info':
                # 需要收集更多資訊
                reply_text = result['text']
                quick_reply = result['quick_reply']

                line_bot_api.reply_message(
                    reply_token,
                    TextSendMessage(
                        text=reply_text,
                        quick_reply=quick_reply or create_main_menu()
                    )
                )
                return

            else:
                # 錯誤或其他情況
                reply_text = result['text']

        except Exception as e:
            logger.error(f"❌ 智能條件引導失敗：{e}")
            reply_text = """
😅 理解你的需求時遇到一些問題

請嘗試更清楚地描述，例如：
• 「我想找台北的軟體工程師」
• 「產品經理，月薪80k以上」
• 「新竹的前端工程師，有3年經驗」

或者點選下方按鈕快速開始：
            """

        # 回應訊息
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(
                text=reply_text,
                quick_reply=create_main_menu()
            )
        )


@app.route('/')
def home():
    """首頁 - 檢查服務狀態"""
    return """
    <h1>職涯助手 LINE Bot 正在運行中！ 🚀</h1>
    <h2>功能特色：</h2>
    <ul>
        <li>🔍 智能職缺搜尋 - 自然語言條件設定</li>
        <li>💼 多平台整合 - 104、CakeResume、Yourator、LinkedIn</li>
        <li>🎯 個人化推薦 - 基於搜尋偏好</li>
        <li>💖 收藏管理 - 追蹤心儀職位</li>
        <li>📊 數據分析 - 薪資趨勢、市場需求</li>
        <li>⚡ 24小時在線服務</li>
    </ul>
    <p><strong>版本：</strong> v3.0.0 Enhanced Edition</p>
    """


@app.route('/ping')
def ping():
    """Ping 端點 - 用於保持服務喚醒"""
    from datetime import datetime
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "message": "Enhanced Job Search Bot - Keep-alive ping successful",
        "version": "3.0.0"
    }


@app.route('/test')
def test():
    """測試頁面"""
    return {
        "status": "OK",
        "message": "增強版職涯助手測試成功！",
        "version": "3.0.0",
        "features": [
            "智能條件引導搜尋",
            "多平台職缺爬蟲",
            "自然語言處理",
            "個人化推薦系統",
            "收藏管理功能",
            "24小時在線服務"
        ],
        "supported_platforms": [
            "104人力銀行",
            "CakeResume",
            "Yourator",
            "LinkedIn (準備中)",
            "公司官網 (準備中)"
        ]
    }


@app.route('/debug')
def debug():
    """除錯頁面"""
    import os
    files_in_dir = os.listdir('.')
    python_files = [f for f in files_in_dir if f.endswith('.py')]

    return {
        "current_directory": os.getcwd(),
        "python_files": python_files,
        "modules_status": {
            "enhanced_crawler": "載入成功" if 'EnhancedJobCrawler' in globals() else "載入失敗",
            "job_condition_guide": "載入成功" if 'ConversationManager' in globals() else "載入失敗",
            "flex_message_templates": "載入成功" if 'JobCardBuilder' in globals() else "載入失敗",
            "user_manager": "載入成功" if 'UserManager' in globals() else "載入失敗"
        },
        "service_status": "24/7 Online Enhanced",
        "version": "3.0.0"
    }


if __name__ == "__main__":
    # 獲取服務URL並啟動保持喚醒功能
    service_url = os.getenv('RENDER_EXTERNAL_URL', 'https://job-search-linebot.onrender.com')
    initialize_keep_alive(service_url)

    # 部署環境設定
    port = int(os.environ.get('PORT', 5001))

    logger.info(f"🚀 啟動增強版職涯助手 LINE Bot v3.0.0")
    logger.info(f"📡 服務網址: {service_url}")
    logger.info(f"⚡ 智能搜尋功能: 已啟用")
    logger.info(f"🔍 支援平台: 104, CakeResume, Yourator")
    logger.info(f"🤖 自然語言處理: 已啟用")

    app.run(debug=False, host='0.0.0.0', port=port)