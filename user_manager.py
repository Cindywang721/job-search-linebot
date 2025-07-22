import json
from datetime import datetime
import os


class UserManager:
    """用戶資料管理器"""

    def __init__(self, user_data_file='user_data.json', jobs_file='jobs.json'):
        self.user_data_file = user_data_file
        self.jobs_file = jobs_file
        self.init_files()

    def init_files(self):
        """初始化資料檔案"""
        # 初始化 user_data.json
        if not os.path.exists(self.user_data_file):
            initial_data = {
                "users": {},
                "favorites": {},
                "search_history": {},
                "settings": {}
            }
            self.save_user_data(initial_data)

        # 初始化 jobs.json
        if not os.path.exists(self.jobs_file):
            initial_jobs = {
                "jobs": [],
                "last_updated": "",
                "total_count": 0
            }
            self.save_jobs_data(initial_jobs)

    def load_user_data(self):
        """載入用戶資料"""
        try:
            with open(self.user_data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"users": {}, "favorites": {}, "search_history": {}, "settings": {}}

    def save_user_data(self, data):
        """儲存用戶資料"""
        try:
            with open(self.user_data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ 儲存用戶資料失敗：{e}")
            return False

    def load_jobs_data(self):
        """載入職缺資料"""
        try:
            with open(self.jobs_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"jobs": [], "last_updated": "", "total_count": 0}

    def save_jobs_data(self, data):
        """儲存職缺資料"""
        try:
            with open(self.jobs_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ 儲存職缺資料失敗：{e}")
            return False

    def add_user(self, user_id, user_info=None):
        """新增或更新用戶"""
        data = self.load_user_data()

        if user_id not in data["users"]:
            data["users"][user_id] = {
                "first_interaction": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "last_interaction": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "search_count": 0,
                "favorite_count": 0,
                "preferred_keywords": [],
                "user_info": user_info or {}
            }
        else:
            # 更新最後互動時間
            data["users"][user_id]["last_interaction"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return self.save_user_data(data)

    def add_favorite(self, user_id, job_id):
        """將職缺加入用戶收藏"""
        data = self.load_user_data()

        # 確保用戶存在
        self.add_user(user_id)

        # 初始化收藏列表
        if user_id not in data["favorites"]:
            data["favorites"][user_id] = []

        # 檢查是否已經收藏
        if job_id not in data["favorites"][user_id]:
            data["favorites"][user_id].append({
                "job_id": job_id,
                "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            # 更新收藏統計
            if user_id in data["users"]:
                data["users"][user_id]["favorite_count"] = len(data["favorites"][user_id])

            self.save_user_data(data)
            return True

        return False  # 已經收藏過了

    def remove_favorite(self, user_id, job_id):
        """移除用戶收藏的職缺"""
        data = self.load_user_data()

        if user_id in data["favorites"]:
            # 找到並移除職缺
            data["favorites"][user_id] = [
                fav for fav in data["favorites"][user_id]
                if fav.get("job_id") != job_id
            ]

            # 更新收藏統計
            if user_id in data["users"]:
                data["users"][user_id]["favorite_count"] = len(data["favorites"][user_id])

            self.save_user_data(data)
            return True

        return False

    def get_user_favorites(self, user_id):
        """取得用戶收藏的職缺"""
        data = self.load_user_data()
        jobs_data = self.load_jobs_data()

        if user_id not in data["favorites"]:
            return []

        favorite_jobs = []
        user_favorites = data["favorites"][user_id]

        for fav_item in user_favorites:
            job_id = fav_item.get("job_id")
            added_at = fav_item.get("added_at")

            # 在職缺資料中找到對應的職缺
            for job in jobs_data.get("jobs", []):
                if job.get("id") == job_id:
                    job_copy = job.copy()
                    job_copy["favorited_at"] = added_at
                    favorite_jobs.append(job_copy)
                    break

        return favorite_jobs

    def record_search(self, user_id, keyword):
        """記錄用戶搜尋歷史"""
        data = self.load_user_data()

        # 確保用戶存在
        self.add_user(user_id)

        # 初始化搜尋歷史
        if user_id not in data["search_history"]:
            data["search_history"][user_id] = []

        # 記錄搜尋
        search_record = {
            "keyword": keyword,
            "searched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        data["search_history"][user_id].append(search_record)

        # 只保留最近 50 次搜尋
        data["search_history"][user_id] = data["search_history"][user_id][-50:]

        # 更新搜尋統計
        if user_id in data["users"]:
            data["users"][user_id]["search_count"] += 1

            # 更新偏好關鍵字
            self._update_preferred_keywords(data, user_id, keyword)

        return self.save_user_data(data)

    def _update_preferred_keywords(self, data, user_id, keyword):
        """更新用戶偏好關鍵字"""
        if "preferred_keywords" not in data["users"][user_id]:
            data["users"][user_id]["preferred_keywords"] = []

        preferred = data["users"][user_id]["preferred_keywords"]

        # 找到是否已存在此關鍵字
        found = False
        for item in preferred:
            if item["keyword"].lower() == keyword.lower():
                item["count"] += 1
                item["last_searched"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                found = True
                break

        if not found:
            preferred.append({
                "keyword": keyword,
                "count": 1,
                "last_searched": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        # 按搜尋次數排序，保留前 10 個
        preferred.sort(key=lambda x: x["count"], reverse=True)
        data["users"][user_id]["preferred_keywords"] = preferred[:10]

    def get_user_stats(self, user_id):
        """取得用戶統計資訊"""
        data = self.load_user_data()

        if user_id not in data["users"]:
            return None

        user_data = data["users"][user_id]
        favorite_count = len(data["favorites"].get(user_id, []))
        search_history_count = len(data["search_history"].get(user_id, []))

        return {
            "first_interaction": user_data.get("first_interaction"),
            "last_interaction": user_data.get("last_interaction"),
            "search_count": search_history_count,
            "favorite_count": favorite_count,
            "preferred_keywords": user_data.get("preferred_keywords", [])
        }

    def get_popular_keywords(self, limit=10):
        """取得熱門搜尋關鍵字"""
        data = self.load_user_data()
        keyword_counts = {}

        # 統計所有用戶的搜尋關鍵字
        for user_id, searches in data["search_history"].items():
            for search in searches:
                keyword = search["keyword"].lower()
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

        # 排序並回傳前 N 個
        popular = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        return popular[:limit]

    def cleanup_old_data(self, days=30):
        """清理舊資料"""
        from datetime import datetime, timedelta

        cutoff_date = datetime.now() - timedelta(days=days)
        data = self.load_user_data()

        # 清理搜尋歷史
        for user_id in data["search_history"]:
            data["search_history"][user_id] = [
                search for search in data["search_history"][user_id]
                if datetime.strptime(search["searched_at"], "%Y-%m-%d %H:%M:%S") > cutoff_date
            ]

        return self.save_user_data(data)

    def export_user_data(self, user_id):
        """匯出用戶資料"""
        data = self.load_user_data()

        user_export = {
            "user_info": data["users"].get(user_id, {}),
            "favorites": data["favorites"].get(user_id, []),
            "search_history": data["search_history"].get(user_id, []),
            "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        return user_export