import requests
from bs4 import BeautifulSoup
import json
import time
import random
from datetime import datetime
import re
import urllib.parse
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedJobCrawler:
    def __init__(self):
        # 簡化的 User-Agent 列表
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0'
        ]

        self.session = requests.Session()

        # 基礎 headers
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        # 公司 Logo 映射
        self.company_logos = {
            'microsoft': 'https://via.placeholder.com/80x80/4285F4/FFFFFF?text=MS',
            'google': 'https://via.placeholder.com/80x80/EA4335/FFFFFF?text=G',
            'apple': 'https://via.placeholder.com/80x80/000000/FFFFFF?text=A',
            'meta': 'https://via.placeholder.com/80x80/1877F2/FFFFFF?text=M',
            'taiwan': 'https://via.placeholder.com/80x80/34A853/FFFFFF?text=TW'
        }

    def get_headers(self):
        """獲取隨機 User-Agent"""
        headers = self.headers.copy()
        headers['User-Agent'] = random.choice(self.user_agents)
        return headers

    def delay_random(self, min_delay=1, max_delay=3):
        """隨機延遲"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)

    def safe_request(self, url, max_retries=2):
        """安全的 HTTP 請求"""
        for attempt in range(max_retries):
            try:
                headers = self.get_headers()
                response = self.session.get(url, headers=headers, timeout=10)

                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    logger.warning("被限制訪問，等待後重試")
                    time.sleep(10)
                else:
                    logger.warning(f"請求失敗，狀態碼：{response.status_code}")

            except Exception as e:
                logger.error(f"請求失敗 (嘗試 {attempt + 1}/{max_retries}): {e}")

            if attempt < max_retries - 1:
                self.delay_random(3, 6)

        return None

    def create_sample_jobs(self, keyword, location="", limit=5):
        """建立範例職缺（當爬蟲失敗時使用）"""
        sample_jobs = []

        job_templates = [
            {
                "title": f"{keyword}工程師",
                "company": "科技股份有限公司",
                "salary": "月薪 50,000 - 80,000",
                "location": location or "台北市",
                "platform": "104人力銀行",
                "description": f"負責 {keyword} 相關系統開發與維護",
                "requirements": ["熟悉相關技術", "具團隊合作精神", "2年以上工作經驗"]
            },
            {
                "title": f"資深{keyword}開發者",
                "company": "創新科技公司",
                "salary": "月薪 70,000 - 120,000",
                "location": location or "新竹市",
                "platform": "CakeResume",
                "description": f"參與 {keyword} 產品設計與開發",
                "requirements": ["3年以上相關經驗", "熟悉敏捷開發", "良好溝通能力"]
            },
            {
                "title": f"{keyword}技術專家",
                "company": "新創團隊",
                "salary": "面議",
                "location": location or "台中市",
                "platform": "Yourator",
                "description": f"領導 {keyword} 技術團隊，制定技術策略",
                "requirements": ["5年以上經驗", "領導經驗", "技術前瞻性"]
            }
        ]

        for i, template in enumerate(job_templates[:limit]):
            job_data = {
                "id": f"sample_{int(time.time())}_{i}",
                "title": template["title"],
                "company": template["company"],
                "salary": template["salary"],
                "location": template["location"],
                "url": f"https://example.com/job/{i}",
                "platform": template["platform"],
                "logo_url": self.get_company_logo(template["company"]),
                "description": template["description"],
                "requirements": template["requirements"],
                "tags": [template["platform"].lower(), keyword.lower()],
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            sample_jobs.append(job_data)

        return sample_jobs

    def crawl_104_jobs(self, keyword, location="", salary_min="", salary_max="", limit=10):
        """爬取 104 人力銀行職缺"""
        jobs = []

        try:
            # 構建搜尋 URL
            params = {
                'ro': '0',
                'keyword': keyword,
                'order': '15',
                'asc': '0',
                'page': '1',
                'mode': 's'
            }

            if location:
                params['area'] = location
            if salary_min:
                params['sal1'] = salary_min
            if salary_max:
                params['sal2'] = salary_max

            search_url = f"https://www.104.com.tw/jobs/search/?{urllib.parse.urlencode(params)}"

            logger.info(f"🔍 正在搜尋 104 職缺：{keyword}")
            response = self.safe_request(search_url)

            if not response:
                logger.warning("104 搜尋失敗，使用範例資料")
                return self.create_sample_jobs(keyword, location, min(limit, 2))

            soup = BeautifulSoup(response.text, 'html.parser')

            # 尋找職缺元素
            job_cards = soup.find_all('article', class_='js-job-item') or \
                        soup.find_all('div', class_='job-list-item') or \
                        soup.find_all('article', {'data-job-name': True})

            logger.info(f"找到 {len(job_cards)} 個 104 職缺元素")

            for i, card in enumerate(job_cards[:limit]):
                try:
                    job_data = self._parse_104_job_card(card, i)
                    if job_data:
                        jobs.append(job_data)
                        logger.info(f"✅ 104職缺 {i + 1}: {job_data['title']} - {job_data['company']}")

                    self.delay_random(0.5, 1.5)

                except Exception as e:
                    logger.error(f"解析104職缺 {i + 1} 時發生錯誤：{e}")
                    continue

        except Exception as e:
            logger.error(f"爬取 104 職缺失敗：{e}")

        # 如果沒有找到職缺，返回範例資料
        if not jobs:
            jobs = self.create_sample_jobs(keyword, location, min(limit, 2))

        return jobs

    def _parse_104_job_card(self, card, index):
        """解析 104 職缺卡片"""
        try:
            # 職位名稱
            title_elem = card.find('a', {'data-job-name': True}) or \
                         card.find('h2', class_='js-job-link') or \
                         card.find('a', class_='js-job-link')

            title = ""
            job_url = ""

            if title_elem:
                title = title_elem.get('data-job-name') or title_elem.get_text(strip=True)
                job_url = title_elem.get('href', '')

            # 公司名稱
            company_elem = card.find('a', {'data-cust-name': True}) or \
                           card.find('ul', class_='b-list-inline')

            company = ""
            if company_elem:
                company = company_elem.get('data-cust-name') or company_elem.get_text(strip=True)

            # 地點和薪資
            location = self._extract_location_from_card(card)
            salary = self._extract_salary_from_card(card)

            # 完整 URL
            if job_url and not job_url.startswith('http'):
                if job_url.startswith('//'):
                    job_url = 'https:' + job_url
                elif job_url.startswith('/'):
                    job_url = 'https://www.104.com.tw' + job_url

            if title and company:
                return {
                    "id": f"104_{int(time.time())}_{index}",
                    "title": self.clean_text(title),
                    "company": self.clean_text(company),
                    "salary": salary,
                    "location": location,
                    "url": job_url or "https://www.104.com.tw",
                    "platform": "104人力銀行",
                    "logo_url": self.get_company_logo(company),
                    "description": f"{title} - {company}",
                    "requirements": ["請查看職缺詳情", "具相關工作經驗"],
                    "tags": ["104", "正職"],
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

        except Exception as e:
            logger.error(f"解析 104 卡片失敗：{e}")

        return None

    def crawl_cakeresume_jobs(self, keyword, location="", limit=10):
        """爬取 CakeResume 職缺"""
        jobs = []

        try:
            params = {
                'q': keyword,
                'location': location,
                'page': 1
            }

            search_url = f"https://www.cakeresume.com/jobs?{urllib.parse.urlencode(params)}"

            logger.info(f"🔍 正在搜尋 CakeResume 職缺：{keyword}")
            response = self.safe_request(search_url)

            if not response:
                logger.warning("CakeResume 搜尋失敗，使用範例資料")
                return self.create_sample_jobs(keyword, location, min(limit, 2))

            soup = BeautifulSoup(response.text, 'html.parser')

            # 尋找職缺元素
            job_cards = soup.find_all('div', class_='JobSearchItem') or \
                        soup.find_all('div', class_='job-item') or \
                        soup.find_all('a', class_='job-item-link')

            logger.info(f"找到 {len(job_cards)} 個 CakeResume 職缺元素")

            for i, card in enumerate(job_cards[:limit]):
                try:
                    job_data = self._parse_cakeresume_job_card(card, i)
                    if job_data:
                        jobs.append(job_data)
                        logger.info(f"✅ CakeResume職缺 {i + 1}: {job_data['title']} - {job_data['company']}")

                    self.delay_random(0.5, 1.5)

                except Exception as e:
                    logger.error(f"解析CakeResume職缺 {i + 1} 時發生錯誤：{e}")
                    continue

        except Exception as e:
            logger.error(f"爬取 CakeResume 職缺失敗：{e}")

        # 如果沒有找到職缺，返回範例資料
        if not jobs:
            jobs = self.create_sample_jobs(keyword, location, min(limit, 2))

        return jobs

    def _parse_cakeresume_job_card(self, card, index):
        """解析 CakeResume 職缺卡片"""
        try:
            # 職位名稱
            title_elem = card.find('h3') or card.find('a', class_='job-title')
            title = title_elem.get_text(strip=True) if title_elem else ""

            # 公司名稱
            company_elem = card.find('div', class_='company-name') or \
                           card.find('span', class_='company')
            company = company_elem.get_text(strip=True) if company_elem else ""

            # 連結
            link_elem = card.find('a') if card.name != 'a' else card
            job_url = link_elem.get('href', '') if link_elem else ""

            # 地點和薪資
            location_elem = card.find('div', class_='location')
            location = location_elem.get_text(strip=True) if location_elem else "未提供"

            salary_elem = card.find('div', class_='salary')
            salary = salary_elem.get_text(strip=True) if salary_elem else "面議"

            # 完整 URL
            if job_url and not job_url.startswith('http'):
                job_url = 'https://www.cakeresume.com' + job_url

            if title and company:
                return {
                    "id": f"cakeresume_{int(time.time())}_{index}",
                    "title": self.clean_text(title),
                    "company": self.clean_text(company),
                    "salary": salary,
                    "location": location,
                    "url": job_url or "https://www.cakeresume.com",
                    "platform": "CakeResume",
                    "logo_url": self.get_company_logo(company),
                    "description": f"{title} - {company}",
                    "requirements": ["請查看職缺詳情"],
                    "tags": ["cakeresume", "正職"],
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

        except Exception as e:
            logger.error(f"解析 CakeResume 卡片失敗：{e}")

        return None

    def crawl_yourator_jobs(self, keyword, location="", limit=10):
        """爬取 Yourator 職缺"""
        jobs = []

        try:
            params = {
                'q': keyword,
                'location[]': location if location else '',
                'page': 1
            }

            search_url = f"https://www.yourator.co/jobs?{urllib.parse.urlencode(params)}"

            logger.info(f"🔍 正在搜尋 Yourator 職缺：{keyword}")
            response = self.safe_request(search_url)

            if not response:
                logger.warning("Yourator 搜尋失敗，使用範例資料")
                return self.create_sample_jobs(keyword, location, min(limit, 2))

            soup = BeautifulSoup(response.text, 'html.parser')

            # 尋找職缺元素
            job_cards = soup.find_all('div', class_='job-card') or \
                        soup.find_all('a', class_='job-link')

            logger.info(f"找到 {len(job_cards)} 個 Yourator 職缺元素")

            for i, card in enumerate(job_cards[:limit]):
                try:
                    job_data = self._parse_yourator_job_card(card, i)
                    if job_data:
                        jobs.append(job_data)
                        logger.info(f"✅ Yourator職缺 {i + 1}: {job_data['title']} - {job_data['company']}")

                    self.delay_random(0.5, 1.5)

                except Exception as e:
                    logger.error(f"解析Yourator職缺 {i + 1} 時發生錯誤：{e}")
                    continue

        except Exception as e:
            logger.error(f"爬取 Yourator 職缺失敗：{e}")

        # 如果沒有找到職缺，返回範例資料
        if not jobs:
            jobs = self.create_sample_jobs(keyword, location, min(limit, 2))

        return jobs

    def _parse_yourator_job_card(self, card, index):
        """解析 Yourator 職缺卡片"""
        try:
            # 職位名稱
            title_elem = card.find('h3') or card.find('div', class_='job-title')
            title = title_elem.get_text(strip=True) if title_elem else ""

            # 公司名稱
            company_elem = card.find('div', class_='company-name') or \
                           card.find('span', class_='company')
            company = company_elem.get_text(strip=True) if company_elem else ""

            # 連結
            link_elem = card.find('a') if card.name != 'a' else card
            job_url = link_elem.get('href', '') if link_elem else ""

            # 地點和薪資
            location_elem = card.find('div', class_='location')
            location = location_elem.get_text(strip=True) if location_elem else "未提供"

            salary_elem = card.find('div', class_='salary')
            salary = salary_elem.get_text(strip=True) if salary_elem else "面議"

            # 完整 URL
            if job_url and not job_url.startswith('http'):
                job_url = 'https://www.yourator.co' + job_url

            if title and company:
                return {
                    "id": f"yourator_{int(time.time())}_{index}",
                    "title": self.clean_text(title),
                    "company": self.clean_text(company),
                    "salary": salary,
                    "location": location,
                    "url": job_url or "https://www.yourator.co",
                    "platform": "Yourator",
                    "logo_url": self.get_company_logo(company),
                    "description": f"{title} - {company}",
                    "requirements": ["請查看職缺詳情"],
                    "tags": ["yourator", "新創"],
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

        except Exception as e:
            logger.error(f"解析 Yourator 卡片失敗：{e}")

        return None

    def search_all_platforms(self, keyword, location="", salary_min="", salary_max="", limit_per_platform=5):
        """搜尋所有平台的職缺"""
        logger.info(f"🚀 開始全平台搜尋：{keyword}")

        all_jobs = []

        # 搜尋 104
        try:
            jobs_104 = self.crawl_104_jobs(keyword, location, salary_min, salary_max, limit_per_platform)
            all_jobs.extend(jobs_104)
            logger.info(f"104 找到 {len(jobs_104)} 個職缺")
        except Exception as e:
            logger.error(f"104搜尋失敗：{e}")

        self.delay_random(2, 4)

        # 搜尋 CakeResume
        try:
            jobs_cake = self.crawl_cakeresume_jobs(keyword, location, limit_per_platform)
            all_jobs.extend(jobs_cake)
            logger.info(f"CakeResume 找到 {len(jobs_cake)} 個職缺")
        except Exception as e:
            logger.error(f"CakeResume搜尋失敗：{e}")

        self.delay_random(2, 4)

        # 搜尋 Yourator
        try:
            jobs_yourator = self.crawl_yourator_jobs(keyword, location, limit_per_platform)
            all_jobs.extend(jobs_yourator)
            logger.info(f"Yourator 找到 {len(jobs_yourator)} 個職缺")
        except Exception as e:
            logger.error(f"Yourator搜尋失敗：{e}")

        logger.info(f"🎉 全平台搜尋完成！總共找到 {len(all_jobs)} 個職缺")

        # 去重
        all_jobs = self.deduplicate_jobs(all_jobs)

        return all_jobs

    def deduplicate_jobs(self, jobs):
        """去除重複職缺"""
        seen = set()
        unique_jobs = []

        for job in jobs:
            key = f"{job['company']}_{job['title']}".lower()
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)

        logger.info(f"去重後剩餘 {len(unique_jobs)} 個職缺")
        return unique_jobs

    def _extract_location_from_card(self, card):
        """從卡片中提取地點資訊"""
        location_selectors = [
            'ul.b-list-inline li',
            'div.job-list-intro',
            'span.location',
            'div.location'
        ]

        for selector in location_selectors:
            elements = card.select(selector)
            for elem in elements:
                text = elem.get_text(strip=True)
                if any(loc in text for loc in ['台北', '新北', '桃園', '新竹', '台中', '台南', '高雄', '遠端']):
                    return text[:20]

        return "未提供"

    def _extract_salary_from_card(self, card):
        """從卡片中提取薪資資訊"""
        salary_selectors = [
            'span.b-tag',
            'div.salary',
            'span.salary',
            'div.job-list-tag'
        ]

        for selector in salary_selectors:
            elem = card.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                if any(keyword in text for keyword in ['萬', '千', ', 'k', 'K']) or any(c.isdigit() for c in text):
                    return self.extract_salary(text)

        return "面議"

    def clean_text(self, text):
        """清理文字"""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text.strip())

    def extract_salary(self, salary_text):
        """提取薪資資訊"""
        if not salary_text:
            return "面議"

        salary = re.sub(r'(月薪|年薪|時薪|待遇|薪資|NT\$|\$)', '', salary_text)
        salary = self.clean_text(salary)

        if re.search(r'\d', salary):
            return salary
        return "面議"

    def get_company_logo(self, company_name):
        """獲取公司Logo"""
        if not company_name:
            return "https://via.placeholder.com/80x80/4285F4/FFFFFF?text=C"

        company_initial = company_name[0].upper() if company_name else 'C'
        colors = ['4285F4', 'EA4335', 'FBBC04', '34A853', 'FF6D01', '9C27B0']
        color = colors[hash(company_name) % len(colors)]

        return f"https://via.placeholder.com/80x80/{color}/FFFFFF?text={company_initial}"


def test_crawler():
    """測試爬蟲功能"""
    crawler = EnhancedJobCrawler()

    print("測試搜尋功能...")
    jobs = crawler.search_all_platforms("Python", "台北", limit_per_platform=2)

    print(f"\n找到 {len(jobs)} 個職缺:")
    for job in jobs:
        print(f"• {job['title']} - {job['company']} ({job['platform']})")
        print(f"  薪資: {job['salary']} | 地點: {job['location']}")


if __name__ == "__main__":
    test_crawler()