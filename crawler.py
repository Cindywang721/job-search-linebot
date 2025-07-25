import requests
from bs4 import BeautifulSoup
import json
import time
import random
from datetime import datetime
import re
import urllib.parse
from urllib.parse import urlencode
import logging
from fake_useragent import UserAgent

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedJobCrawler:
    def __init__(self):
        # 使用隨機 User-Agent
        self.ua = UserAgent()
        self.session = requests.Session()

        # 反爬蟲設置
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }

        # 代理池（如果需要）
        self.proxies = [
            # 可以添加代理服務器
        ]

    def get_headers(self):
        """獲取隨機 User-Agent"""
        headers = self.headers.copy()
        headers['User-Agent'] = self.ua.random
        return headers

    def delay_random(self, min_delay=2, max_delay=5):
        """隨機延遲，避免被反爬蟲偵測"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
        logger.info(f"延遲 {delay:.1f} 秒")

    def safe_request(self, url, max_retries=3):
        """安全的 HTTP 請求，包含重試機制"""
        for attempt in range(max_retries):
            try:
                headers = self.get_headers()
                response = self.session.get(url, headers=headers, timeout=15)

                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    # 被限制，等待更長時間
                    logger.warning(f"被限制訪問，等待 {30} 秒")
                    time.sleep(30)
                else:
                    logger.warning(f"請求失敗，狀態碼：{response.status_code}")

            except Exception as e:
                logger.error(f"請求失敗 (嘗試 {attempt + 1}/{max_retries}): {e}")

            if attempt < max_retries - 1:
                self.delay_random(5, 10)

        return None

    def crawl_104_jobs(self, keyword, location="", salary_min="", salary_max="", limit=10):
        """爬取 104 人力銀行職缺 - 使用最新的 API"""
        jobs = []

        try:
            # 104 的新 API 端點
            params = {
                'ro': '0',
                'keyword': keyword,
                'area': location,
                'order': '15',  # 最新刊登
                'asc': '0',
                'page': '1',
                'mode': 's',
                'jobsource': '2018indexpoc'
            }

            if salary_min:
                params['sal1'] = salary_min
            if salary_max:
                params['sal2'] = salary_max

            # 構建搜尋 URL
            base_url = "https://www.104.com.tw/jobs/search/"
            search_url = f"{base_url}?{urlencode(params)}"

            logger.info(f"🔍 正在搜尋 104 職缺：{keyword}")
            response = self.safe_request(search_url)

            if not response:
                logger.error("無法獲取 104 搜尋結果")
                return jobs

            soup = BeautifulSoup(response.text, 'html.parser')

            # 新的職缺選擇器（2024年更新）
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

                    self.delay_random(1, 3)

                except Exception as e:
                    logger.error(f"解析104職缺 {i + 1} 時發生錯誤：{e}")
                    continue

        except Exception as e:
            logger.error(f"爬取 104 職缺失敗：{e}")

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

            # 地點
            location = self._extract_location_from_card(card)

            # 薪資
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
                    "url": job_url,
                    "platform": "104人力銀行",
                    "logo_url": self.get_company_logo(company),
                    "description": f"{title} - {company}",
                    "requirements": ["請查看個別職缺詳情", "具相關工作經驗優先"],
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
            # CakeResume API
            params = {
                'q': keyword,
                'location': location,
                'page': 1,
                'per_page': limit
            }

            search_url = f"https://www.cakeresume.com/jobs?{urlencode(params)}"

            logger.info(f"🔍 正在搜尋 CakeResume 職缺：{keyword}")
            response = self.safe_request(search_url)

            if not response:
                return jobs

            soup = BeautifulSoup(response.text, 'html.parser')

            # CakeResume 職缺選擇器
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

                    self.delay_random(1, 3)

                except Exception as e:
                    logger.error(f"解析CakeResume職缺 {i + 1} 時發生錯誤：{e}")
                    continue

        except Exception as e:
            logger.error(f"爬取 CakeResume 職缺失敗：{e}")

        return jobs

    def _parse_cakeresume_job_card(self, card, index):
        """解析 CakeResume 職缺卡片"""
        try:
            # 職位名稱和連結
            title_elem = card.find('h3') or card.find('a', class_='job-title')
            title = ""
            job_url = ""

            if title_elem:
                title = title_elem.get_text(strip=True)
                link_elem = title_elem.find('a') or card.find('a')
                if link_elem:
                    job_url = link_elem.get('href', '')

            # 公司名稱
            company_elem = card.find('div', class_='company-name') or \
                           card.find('span', class_='company')
            company = company_elem.get_text(strip=True) if company_elem else ""

            # 地點
            location_elem = card.find('div', class_='location') or \
                            card.find('span', class_='location')
            location = location_elem.get_text(strip=True) if location_elem else "未提供"

            # 薪資
            salary_elem = card.find('div', class_='salary') or \
                          card.find('span', class_='salary')
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
                    "url": job_url,
                    "platform": "CakeResume",
                    "logo_url": self.get_company_logo(company),
                    "description": f"{title} - {company}",
                    "requirements": ["請查看個別職缺詳情"],
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
            # Yourator 搜尋
            params = {
                'q': keyword,
                'location[]': location if location else '',
                'page': 1
            }

            search_url = f"https://www.yourator.co/jobs?{urlencode(params)}"

            logger.info(f"🔍 正在搜尋 Yourator 職缺：{keyword}")
            response = self.safe_request(search_url)

            if not response:
                return jobs

            soup = BeautifulSoup(response.text, 'html.parser')

            # Yourator 職缺選擇器
            job_cards = soup.find_all('div', class_='job-card') or \
                        soup.find_all('a', class_='job-link')

            logger.info(f"找到 {len(job_cards)} 個 Yourator 職缺元素")

            for i, card in enumerate(job_cards[:limit]):
                try:
                    job_data = self._parse_yourator_job_card(card, i)
                    if job_data:
                        jobs.append(job_data)
                        logger.info(f"✅ Yourator職缺 {i + 1}: {job_data['title']} - {job_data['company']}")

                    self.delay_random(1, 3)

                except Exception as e:
                    logger.error(f"解析Yourator職缺 {i + 1} 時發生錯誤：{e}")
                    continue

        except Exception as e:
            logger.error(f"爬取 Yourator 職缺失敗：{e}")

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

            # 地點
            location_elem = card.find('div', class_='location')
            location = location_elem.get_text(strip=True) if location_elem else "未提供"

            # 薪資
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
                    "url": job_url,
                    "platform": "Yourator",
                    "logo_url": self.get_company_logo(company),
                    "description": f"{title} - {company}",
                    "requirements": ["請查看個別職缺詳情"],
                    "tags": ["yourator", "新創", "正職"],
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

        self.delay_random(3, 6)

        # 搜尋 CakeResume
        try:
            jobs_cake = self.crawl_cakeresume_jobs(keyword, location, limit_per_platform)
            all_jobs.extend(jobs_cake)
            logger.info(f"CakeResume 找到 {len(jobs_cake)} 個職缺")
        except Exception as e:
            logger.error(f"CakeResume搜尋失敗：{e}")

        self.delay_random(3, 6)

        # 搜尋 Yourator
        try:
            jobs_yourator = self.crawl_yourator_jobs(keyword, location, limit_per_platform)
            all_jobs.extend(jobs_yourator)
            logger.info(f"Yourator 找到 {len(jobs_yourator)} 個職缺")
        except Exception as e:
            logger.error(f"Yourator搜尋失敗：{e}")

        logger.info(f"🎉 全平台搜尋完成！總共找到 {len(all_jobs)} 個職缺")

        # 去重和排序
        all_jobs = self.deduplicate_jobs(all_jobs)

        return all_jobs

    def deduplicate_jobs(self, jobs):
        """去除重複職缺"""
        seen = set()
        unique_jobs = []

        for job in jobs:
            # 使用公司名+職位名作為去重標準
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
                    return text[:20]  # 限制長度

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
                if any(keyword in text for keyword in ['萬', '千', '$', 'k', 'K']) or any(c.isdigit() for c in text):
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
            return "https://via.placeholder.com/80x80/4285F4/FFFFFF?text=LOGO"

        company_initial = company_name[0].upper() if company_name else 'C'
        colors = ['4285F4', 'EA4335', 'FBBC04', '34A853', 'FF6D01', '9C27B0']
        color = colors[hash(company_name) % len(colors)]

        return f"https://via.placeholder.com/80x80/{color}/FFFFFF?text={company_initial}"


# 測試函數
def test_enhanced_crawler():
    """測試增強版爬蟲"""
    crawler = EnhancedJobCrawler()

    # 測試搜尋
    jobs = crawler.search_all_platforms("Python工程師", "台北", limit_per_platform=3)

    print(f"\n📋 搜尋結果：找到 {len(jobs)} 個職缺")
    for job in jobs[:3]:
        print(f"• {job['title']} - {job['company']} ({job['platform']})")
        print(f"  薪資：{job['salary']} | 地點：{job['location']}")
        print(f"  連結：{job['url'][:50]}...")
        print()


if __name__ == "__main__":
    test_enhanced_crawler()