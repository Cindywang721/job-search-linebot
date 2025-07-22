import schedule
import time
import threading
from datetime import datetime, timedelta
from linebot.models import TextSendMessage, FlexSendMessage
from crawler import JobCrawler
from flex_message_templates import JobCardBuilder
from user_manager import UserManager
from advanced_search import AdvancedJobSearch


class NotificationSystem:
    """通知與定時任務系統"""

    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.job_crawler = JobCrawler()
        self.job_card_builder = JobCardBuilder()
        self.user_manager = UserManager()
        self.advanced_search = AdvancedJobSearch()

        # 通知設定
        self.notification_settings = {
            "daily_job_alerts": True,
            "new_job_notifications": True,
            "favorite_reminders": True
        }

        # 啟動定時任務
        self.setup_scheduled_tasks()
        self.start_scheduler()

    def setup_scheduled_tasks(self):
        """設置定時任務"""

        # 每日上午9點推送熱門職缺
        schedule.every().day.at("09:00").do(self.send_daily_job_digest)

        # 每日下午6點推送個人化推薦
        schedule.every().day.at("18:00").do(self.send_personalized_recommendations)

        # 每週一上午10點推送週報
        schedule.every().monday.at("10:00").do(self.send_weekly_report)

        # 每小時更新熱門職缺 (僅在工作時間)
        for hour in range(9, 18):
            schedule.every().day.at(f"{hour:02d}:00").do(self.update_trending_jobs)

        # 每天凌晨2點清理舊資料
        schedule.every().day.at("02:00").do(self.cleanup_old_data)

        print("📅 定時任務已設置完成")

    def start_scheduler(self):
        """啟動排程器"""

        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分鐘檢查一次

        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        print("⏰ 定時任務排程器已啟動")

    def send_daily_job_digest(self):
        """發送每日職缺摘要"""
        try:
            print("📧 開始發送每日職缺摘要...")

            # 獲取熱門關鍵字
            popular_keywords = self.user_manager.get_popular_keywords(5)

            if not popular_keywords:
                print("沒有熱門關鍵字，跳過每日摘要")
                return

            # 為每個熱門關鍵字搜尋職缺
            digest_jobs = []
            for keyword, count in popular_keywords[:3]:  # 取前3個熱門關鍵字
                jobs = self.job_crawler.search_all_platforms(keyword, 3)
                digest_jobs.extend(jobs)

            if not digest_jobs:
                print("沒有找到職缺，跳過每日摘要")
                return

            # 獲取所有活躍用戶
            active_users = self._get_active_users(days=7)

            for user_id in active_users:
                try:
                    # 建立每日摘要訊息
                    summary_text = f"""
🌅 早安！今日職缺精選

🔥 熱門搜尋：
{chr(10).join([f"• {keyword} ({count}次搜尋)" for keyword, count in popular_keywords[:3]])}

💼 為你找到 {len(digest_jobs)} 個新職缺
點選下方卡片查看詳情 👇
                    """

                    # 發送摘要文字
                    self.line_bot_api.push_message(
                        user_id,
                        TextSendMessage(text=summary_text.strip())
                    )

                    # 發送職缺卡片
                    if digest_jobs:
                        carousel = self.job_card_builder.create_job_carousel(
                            digest_jobs[:5], "熱門職缺"
                        )
                        self.line_bot_api.push_message(user_id, carousel)

                    time.sleep(1)  # 避免發送太快

                except Exception as e:
                    print(f"發送每日摘要給用戶 {user_id} 失敗：{e}")

            print(f"✅ 每日摘要發送完成，發送給 {len(active_users)} 位用戶")

        except Exception as e:
            print(f"❌ 發送每日職缺摘要失敗：{e}")

    def send_personalized_recommendations(self):
        """發送個人化推薦"""
        try:
            print("🎯 開始發送個人化推薦...")

            # 獲取有搜尋歷史的用戶
            users_with_history = self._get_users_with_search_history()

            for user_id in users_with_history:
                try:
                    # 獲取用戶偏好
                    user_stats = self.user_manager.get_user_stats(user_id)
                    if not user_stats or not user_stats.get("preferred_keywords"):
                        continue

                    # 基於用戶偏好搜尋職缺
                    preferred_keywords = user_stats["preferred_keywords"][:2]  # 取前2個偏好

                    recommendation_jobs = []
                    for pref in preferred_keywords:
                        keyword = pref["keyword"]
                        jobs = self.job_crawler.search_all_platforms(keyword, 3)
                        recommendation_jobs.extend(jobs)

                    if recommendation_jobs:
                        # 發送個人化推薦
                        recommendation_text = f"""
🎯 專為你推薦

基於你的搜尋偏好：
{chr(10).join([f"• {pref['keyword']} (搜尋{pref['count']}次)" for pref in preferred_keywords])}

💡 為你找到 {len(recommendation_jobs)} 個相關職缺
                        """

                        self.line_bot_api.push_message(
                            user_id,
                            TextSendMessage(text=recommendation_text.strip())
                        )

                        # 發送推薦職缺卡片
                        carousel = self.job_card_builder.create_job_carousel(
                            recommendation_jobs[:5], "個人化推薦"
                        )
                        self.line_bot_api.push_message(user_id, carousel)

                    time.sleep(1)

                except Exception as e:
                    print(f"發送個人化推薦給用戶 {user_id} 失敗：{e}")

            print(f"✅ 個人化推薦發送完成，發送給 {len(users_with_history)} 位用戶")

        except Exception as e:
            print(f"❌ 發送個人化推薦失敗：{e}")

    def send_weekly_report(self):
        """發送週報"""
        try:
            print("📊 開始發送週報...")

    def send_weekly_report(self):
        """發送週報"""
        try:
            print("📊 開始發送週報...")

            # 獲取活躍用戶
            active_users = self._get_active_users(days=7)

            # 統計本週資料
            weekly_stats = self._get_weekly_stats()

            for user_id in active_users[:50]:  # 限制發送數量
                try:
                    user_stats = self.user_manager.get_user_stats(user_id)
                    if not user_stats:
                        continue

                    # 建立週報訊息
                    report_text = f"""
📊 本週職涯助手報告

👤 你的活動：
• 搜尋了 {user_stats.get('search_count', 0)} 次職缺
• 收藏了 {user_stats.get('favorite_count', 0)} 個職缺

🔥 本週平台統計：
• 新增 {weekly_stats.get('new_jobs', 0)} 個職缺
• 最熱門關鍵字：{weekly_stats.get('top_keyword', 'Python')}
• 活躍用戶：{weekly_stats.get('active_users', 0)} 位

💡 建議：
持續搜尋你感興趣的職位，
保持活躍有助於獲得更精準的推薦！

祝你求職順利！🍀
                    """

                    self.line_bot_api.push_message(
                        user_id,
                        TextSendMessage(text=report_text.strip())
                    )

                    time.sleep(1)

                except Exception as e:
                    print(f"發送週報給用戶 {user_id} 失敗：{e}")

            print(f"✅ 週報發送完成，發送給 {len(active_users)} 位用戶")

        except Exception as e:
            print(f"❌ 發送週報失敗：{e}")

    def update_trending_jobs(self):
        """更新熱門職缺"""
        try:
            print("🔄 更新熱門職缺...")

            # 獲取熱門關鍵字
            popular_keywords = self.user_manager.get_popular_keywords(3)

            all_jobs = []
            for keyword, count in popular_keywords:
                jobs = self.job_crawler.search_all_platforms(keyword, 5)
                all_jobs.extend(jobs)

            if all_jobs:
                # 更新職缺資料
                jobs_data = {
                    "jobs": all_jobs,
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "total_count": len(all_jobs)
                }
                self.user_manager.save_jobs_data(jobs_data)
                print(f"✅ 更新了 {len(all_jobs)} 個熱門職缺")

        except Exception as e:
            print(f"❌ 更新熱門職缺失敗：{e}")

    def cleanup_old_data(self):
        """清理舊資料"""
        try:
            print("🧹 清理舊資料...")

            # 清理30天前的搜尋歷史
            self.user_manager.cleanup_old_data(30)

            print("✅ 舊資料清理完成")

        except Exception as e:
            print(f"❌ 清理舊資料失敗：{e}")

    def send_favorite_reminder(self, user_id):
        """發送收藏提醒"""
        try:
            favorites = self.user_manager.get_user_favorites(user_id)

            if len(favorites) >= 5:
                reminder_text = f"""
💖 收藏提醒

你已經收藏了 {len(favorites)} 個職缺！
記得定期查看並投遞履歷唷 📝

💡 小提示：
• 整理收藏清單
• 比較不同職缺
• 準備客製化履歷
• 主動投遞應徵

不要讓好機會溜走！💪
                """

                self.line_bot_api.push_message(
                    user_id,
                    TextSendMessage(text=reminder_text.strip())
                )

                return True

        except Exception as e:
            print(f"❌ 發送收藏提醒失敗：{e}")

        return False

    def _get_active_users(self, days=7):
        """獲取活躍用戶列表"""
        user_data = self.user_manager.load_user_data()
        active_users = []

        cutoff_date = datetime.now() - timedelta(days=days)

        for user_id, user_info in user_data.get("users", {}).items():
            last_interaction = user_info.get("last_interaction")
            if last_interaction:
                try:
                    last_date = datetime.strptime(last_interaction, "%Y-%m-%d %H:%M:%S")
                    if last_date > cutoff_date:
                        active_users.append(user_id)
                except ValueError:
                    continue

        return active_users

    def _get_users_with_search_history(self):
        """獲取有搜尋歷史的用戶"""
        user_data = self.user_manager.load_user_data()
        users_with_history = []

        for user_id, searches in user_data.get("search_history", {}).items():
            if searches:  # 有搜尋紀錄
                users_with_history.append(user_id)

        return users_with_history

    def _get_weekly_stats(self):
        """獲取本週統計資料"""
        user_data = self.user_manager.load_user_data()

        # 計算本週新增職缺數量
        jobs_data = self.user_manager.load_jobs_data()

        # 計算活躍用戶數
        active_users_count = len(self._get_active_users(7))

        # 獲取最熱門關鍵字
        popular = self.user_manager.get_popular_keywords(1)
        top_keyword = popular[0][0] if popular else "Python"

        return {
            "new_jobs": len(jobs_data.get("jobs", [])),
            "active_users": active_users_count,
            "top_keyword": top_keyword
        }

    def send_custom_notification(self, user_id, message):
        """發送自訂通知"""
        try:
            self.line_bot_api.push_message(
                user_id,
                TextSendMessage(text=message)
            )
            return True
        except Exception as e:
            print(f"❌ 發送自訂通知失敗：{e}")
            return False

    def notify_new_jobs(self, keyword, jobs):
        """通知有新職缺"""
        if not jobs:
            return

        # 找出搜尋過此關鍵字的用戶
        user_data = self.user_manager.load_user_data()
        interested_users = []

        for user_id, searches in user_data.get("search_history", {}).items():
            for search in searches:
                if keyword.lower() in search.get("keyword", "").lower():
                    interested_users.append(user_id)
                    break

        # 發送通知
        for user_id in interested_users[:20]:  # 限制通知數量
            try:
                notification_text = f"""
🆕 新職缺通知

你關注的「{keyword}」有 {len(jobs)} 個新職缺！

{chr(10).join([f"• {job.get('title', '')} - {job.get('company', '')}" for job in jobs[:3]])}

快來查看詳情吧！
                """

                self.send_custom_notification(user_id, notification_text.strip())
                time.sleep(1)

            except Exception as e:
                print(f"發送新職缺通知給用戶 {user_id} 失敗：{e}")

    def get_notification_stats(self):
        """獲取通知統計"""
        active_users = len(self._get_active_users(7))
        users_with_history = len(self._get_users_with_search_history())

        return {
            "active_users_7d": active_users,
            "users_with_search_history": users_with_history,
            "scheduled_tasks": len(schedule.jobs),
            "notification_settings": self.notification_settings
        }