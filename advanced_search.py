import re
from datetime import datetime
import jieba
from collections import Counter


class AdvancedJobSearch:
    """高級職缺搜尋功能"""

    def __init__(self):
        # 技能關鍵字字典
        self.skill_keywords = {
            "programming": ["python", "java", "javascript", "react", "vue", "angular", "node.js", "php", "c++", "c#",
                            "go", "rust"],
            "data": ["sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "pandas", "numpy", "tensorflow",
                     "pytorch"],
            "design": ["photoshop", "illustrator", "figma", "sketch", "ui", "ux", "wireframe", "prototype"],
            "marketing": ["google analytics", "facebook ads", "seo", "sem", "content marketing", "social media"],
            "management": ["project management", "agile", "scrum", "leadership", "team management"]
        }

        # 薪資關鍵字
        self.salary_keywords = ["薪資", "薪水", "月薪", "年薪", "待遇", "起薪", "萬", "k", "thousand"]

        # 地點關鍵字
        self.location_keywords = ["台北", "新北", "桃園", "台中", "台南", "高雄", "新竹", "遠端", "remote", "在家工作"]

        # 公司類型關鍵字
        self.company_type_keywords = ["外商", "新創", "上市", "傳統產業", "科技業", "金融業", "製造業"]

    def parse_search_query(self, query):
        """解析搜尋查詢，提取不同類型的條件"""
        query = query.strip()

        parsed = {
            "original_query": query,
            "main_keywords": [],
            "skills": [],
            "salary_range": None,
            "locations": [],
            "company_types": [],
            "experience_level": None,
            "work_type": None
        }

        # 轉換為小寫以便比較
        query_lower = query.lower()

        # 提取主要關鍵字（移除特殊條件後剩餘的）
        main_query = query

        # 提取薪資條件
        salary_matches = re.findall(r'(\d+)([k萬]?)\s*[-~]\s*(\d+)([k萬]?)', query_lower)
        if salary_matches:
            for match in salary_matches:
                min_sal, min_unit, max_sal, max_unit = match
                parsed["salary_range"] = {
                    "min": self._normalize_salary(min_sal, min_unit),
                    "max": self._normalize_salary(max_sal, max_unit)
                }
                # 從主查詢中移除薪資條件
                main_query = re.sub(rf'{min_sal}{min_unit}[-~]{max_sal}{max_unit}', '', main_query, flags=re.IGNORECASE)

        # 提取地點
        for location in self.location_keywords:
            if location in query:
                parsed["locations"].append(location)
                main_query = main_query.replace(location, '')

        # 提取公司類型
        for company_type in self.company_type_keywords:
            if company_type in query:
                parsed["company_types"].append(company_type)
                main_query = main_query.replace(company_type, '')

        # 提取技能
        all_skills = []
        for category, skills in self.skill_keywords.items():
            for skill in skills:
                if skill in query_lower:
                    parsed["skills"].append(skill)
                    all_skills.append(skill)

        # 提取經驗等級
        if any(word in query_lower for word in ["新鮮人", "應屆", "無經驗"]):
            parsed["experience_level"] = "entry"
        elif any(word in query_lower for word in ["資深", "senior", "主管", "經理"]):
            parsed["experience_level"] = "senior"
        elif any(word in query_lower for word in ["中級", "2-5年", "有經驗"]):
            parsed["experience_level"] = "mid"

        # 提取工作型態
        if any(word in query_lower for word in ["遠端", "remote", "在家", "居家"]):
            parsed["work_type"] = "remote"
        elif any(word in query_lower for word in ["現場", "辦公室", "on-site"]):
            parsed["work_type"] = "onsite"
        elif any(word in query_lower for word in ["混合", "hybrid", "彈性"]):
            parsed["work_type"] = "hybrid"

        # 清理主關鍵字
        main_query = re.sub(r'\s+', ' ', main_query.strip())
        main_query = main_query.replace('工程師', '').replace('設計師', '').strip()

        if main_query:
            # 使用 jieba 分詞提取關鍵字
            keywords = jieba.lcut(main_query)
            parsed["main_keywords"] = [kw.strip() for kw in keywords if len(kw.strip()) > 1]

        return parsed

    def _normalize_salary(self, amount, unit):
        """標準化薪資數字"""
        amount = int(amount)
        if unit in ['k', 'K']:
            return amount * 1000
        elif unit in ['萬']:
            return amount * 10000
        else:
            return amount

    def filter_jobs(self, jobs, search_conditions):
        """根據搜尋條件過濾職缺"""
        filtered_jobs = []

        for job in jobs:
            score = self._calculate_job_score(job, search_conditions)
            if score > 0:
                job_copy = job.copy()
                job_copy["relevance_score"] = score
                filtered_jobs.append(job_copy)

        # 按相關度排序
        filtered_jobs.sort(key=lambda x: x["relevance_score"], reverse=True)

        return filtered_jobs

    def _calculate_job_score(self, job, conditions):
        """計算職缺與搜尋條件的匹配分數"""
        score = 0
        max_score = 0

        # 職位標題匹配 (權重: 40%)
        title = job.get("title", "").lower()
        for keyword in conditions["main_keywords"]:
            max_score += 40
            if keyword.lower() in title:
                score += 40
            elif any(keyword.lower() in desc.lower() for desc in [job.get("description", ""), job.get("company", "")]):
                score += 20

        # 技能匹配 (權重: 30%)
        description_text = (job.get("description", "") + " " + job.get("title", "")).lower()
        for skill in conditions["skills"]:
            max_score += 30
            if skill.lower() in description_text:
                score += 30

        # 地點匹配 (權重: 15%)
        job_location = job.get("location", "").lower()
        for location in conditions["locations"]:
            max_score += 15
            if location.lower() in job_location:
                score += 15

        # 薪資匹配 (權重: 10%)
        if conditions["salary_range"]:
            max_score += 10
            job_salary = self._extract_salary_from_job(job)
            if job_salary and self._salary_in_range(job_salary, conditions["salary_range"]):
                score += 10

        # 公司類型匹配 (權重: 5%)
        company_info = (job.get("company", "") + " " + job.get("description", "")).lower()
        for company_type in conditions["company_types"]:
            max_score += 5
            if company_type in company_info:
                score += 5

        # 計算相對分數 (0-100)
        if max_score == 0:
            return 50  # 如果沒有特定條件，給予中等分數

        relative_score = (score / max_score) * 100

        # 如果分數太低，過濾掉
        return relative_score if relative_score >= 30 else 0

    def _extract_salary_from_job(self, job):
        """從職缺中提取薪資資訊"""
        salary_text = job.get("salary", "")
        if not salary_text or salary_text == "面議":
            return None

        # 提取數字
        numbers = re.findall(r'(\d+)', salary_text)
        if numbers:
            # 假設是月薪，轉換為年薪比較
            monthly_salary = int(numbers[0])
            if "萬" in salary_text:
                monthly_salary *= 10000
            elif "k" in salary_text.lower():
                monthly_salary *= 1000

            return monthly_salary

        return None

    def _salary_in_range(self, job_salary, salary_range):
        """檢查薪資是否在指定範圍內"""
        if not job_salary or not salary_range:
            return False

        min_salary = salary_range.get("min", 0)
        max_salary = salary_range.get("max", float('inf'))

        return min_salary <= job_salary <= max_salary

    def suggest_related_searches(self, query, jobs):
        """根據搜尋結果建議相關搜尋"""
        suggestions = []

        # 從搜尋結果中提取常見技能
        all_text = ""
        for job in jobs[:10]:  # 只分析前10個結果
            all_text += job.get("title", "") + " " + job.get("description", "") + " "

        # 提取技能建議
        skill_suggestions = []
        for category, skills in self.skill_keywords.items():
            for skill in skills:
                if skill.lower() in all_text.lower():
                    skill_suggestions.append(skill)

        # 取最常見的技能
        if skill_suggestions:
            skill_counter = Counter(skill_suggestions)
            top_skills = [skill for skill, count in skill_counter.most_common(3)]
            suggestions.extend([f"{query} {skill}" for skill in top_skills])

        # 地點建議
        location_suggestions = ["台北", "新竹", "台中", "遠端工作"]
        suggestions.extend([f"{query} {loc}" for loc in location_suggestions[:2]])

        # 經驗等級建議
        exp_suggestions = ["新鮮人", "資深", "主管"]
        suggestions.extend([f"{exp} {query}" for exp in exp_suggestions[:2]])

        return suggestions[:6]  # 最多返回6個建議

    def generate_search_summary(self, conditions, results_count):
        """生成搜尋摘要"""
        summary_parts = []

        if conditions["main_keywords"]:
            summary_parts.append(f"關鍵字: {', '.join(conditions['main_keywords'])}")

        if conditions["skills"]:
            summary_parts.append(f"技能: {', '.join(conditions['skills'])}")

        if conditions["locations"]:
            summary_parts.append(f"地點: {', '.join(conditions['locations'])}")

        if conditions["salary_range"]:
            min_sal = conditions["salary_range"]["min"]
            max_sal = conditions["salary_range"]["max"]
            summary_parts.append(f"薪資: {min_sal:,} - {max_sal:,}")

        if conditions["company_types"]:
            summary_parts.append(f"公司類型: {', '.join(conditions['company_types'])}")

        summary = "搜尋條件: " + " | ".join(summary_parts) if summary_parts else "一般搜尋"
        summary += f"\n找到 {results_count} 個相關職缺"

        return summary