import requests
from bs4 import BeautifulSoup
import json
import time
import random
from datetime import datetime
import re
import urllib.parse


class JobCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

        # 公司Logo映射 - 常見公司的Logo
        self.company_logos = {
            'microsoft': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Microsoft_logo.svg/200px-Microsoft_logo.svg.png',
            'google': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Google_2015_logo.svg/200px-Google_2015_logo.svg.png',
            'apple': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/Apple_logo_black.svg/200px-Apple_logo_black.svg.png',
            'meta': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/Meta_Platforms_Inc._logo.svg/200px-Meta_Platforms_Inc._logo.svg.png',
            'amazon': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Amazon_logo.svg/200px-Amazon_logo.svg.png',
            'netflix': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/Netflix_2015_logo.svg/200px-Netflix_2015_logo.svg.png',
            'tesla': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/bb/Tesla_T_symbol.svg/200px-Tesla_T_symbol.svg.png',
            'spotify': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Spotify_logo_without_text.svg/200px-Spotify_logo_without_text.svg.png',
            'uber': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/58/Uber_logo_2018.svg/200px-Uber_logo_2018.svg.png',
            'airbnb': 'https://upload.wikimedia.org/wikipedia.org/wikipedia/commons/6/69/Airbnb_Logo_Bélo.svg',
            '台積電': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/TSMC.svg/200px-TSMC.svg.png',
            'tsmc': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/TSMC.svg/200px-TSMC.svg.png',
            '聯發科': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/ee/MediaTek_logo.svg/200px-MediaTek_logo.svg.png',
            'mediatek': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/ee/MediaTek_logo.svg/200px-MediaTek_logo.svg.png',
            '鴻海': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/Foxconn_logo.svg/200px-Foxconn_logo.svg.png',
            'foxconn': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/Foxconn_logo.svg/200px-Foxconn_logo.svg.png'
        }

    def delay_random(self):
        """隨機延遲，避免被反爬蟲偵測"""
        time.sleep(random.uniform(2, 5))

    def clean_text(self, text):
        """清理文字，移除多餘空白和換行"""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text.strip())

    def extract_salary(self, salary_text):
        """提取薪資資訊"""
        if not salary_text:
            return "面議"

        # 移除常見的無用字詞
        salary = re.sub(r'(月薪|年薪|時薪|待遇|薪資|NT\$|\$)', '', salary_text)
        salary = self.clean_text(salary)

        # 如果包含數字，保留；否則返回面議
        if re.search(r'\d', salary):
            return salary
        return "面議"

    def get_company_logo(self, company_name):
        """根據公司名稱獲取Logo"""
        if not company_name:
            return "https://via.placeholder.com/80x80/4285F4/FFFFFF?text=LOGO"

        company_lower = company_name.lower()

        # 檢查是否有預設的公司Logo
        for key, logo_url in self.company_logos.items():
            if key in company_lower or key in company_name:
                return logo_url

        # 根據公司名稱生成彩色Logo
        company_initial = company_name[0].upper() if company_name else 'C'
        colors = ['4285F4', 'EA4335', 'FBBC04', '34A853', 'FF6D01', '9C27B0']
        color = colors[hash(company_name) % len(colors)]

        logo_url = f"https://via.placeholder.com/80x80/{color}/FFFFFF?text={company_initial}"
        return logo_url

    def crawl_104_jobs(self, keyword, limit=10):
        """爬取 104 人力銀行職缺 - 真實搜尋"""
        jobs = []

        try:
            # 104 搜尋 URL
            encoded_keyword = urllib.parse.quote(keyword)
            search_url = f"https://www.104.com.tw/jobs/search/?ro=0&keyword={encoded_keyword}&expansionType=area%2Cspec%2Ccom%2Cjob%2Cwf%2Cwktm&order=15&asc=0&page=1&mode=s&jobsource=2018indexpoc"

            print(f"🔍 正在搜尋 104 職缺：{keyword}")
            response = self.session.get(search_url, timeout=15)

            if response.status_code != 200:
                print(f"❌ 104 請求失敗，狀態碼：{response.status_code}")
                return jobs

            soup = BeautifulSoup(response.text, 'html.parser')

            # 104 的職缺卡片選擇器
            job_cards = soup.find_all('article', {'data-job-name': True}) or soup.find_all('div', class_='js-job-item')

            print(f"🔍 找到 {len(job_cards)} 個職缺元素")

            for i, card in enumerate(job_cards[:limit]):
                try:
                    # 提取職位名稱
                    title = ""
                    title_elem = card.find('a', {'data-job-name': True})
                    if title_elem:
                        title = self.clean_text(title_elem.get('data-job-name', ''))
                    else:
                        # 備用方案
                        title_link = card.find('a', class_='js-job-link') or card.find('h2', class_='b-tit')
                        if title_link:
                            title = self.clean_text(title_link.get_text())

                    # 提取公司名稱
                    company = ""
                    company_elem = card.find('a', {'data-cust-name': True})
                    if company_elem:
                        company = self.clean_text(company_elem.get('data-cust-name', ''))
                    else:
                        # 備用方案
                        company_link = card.find('a', class_='js-company-link') or card.find('ul',
                                                                                             class_='b-list-inline')
                        if company_link:
                            company = self.clean_text(company_link.get_text())

                    # 提取地點
                    location = ""
                    location_elem = card.find('ul', class_='job-list-intro') or card.find('ul', class_='b-list-inline')
                    if location_elem:
                        location_items = location_elem.find_all('li')
                        for item in location_items:
                            text = self.clean_text(item.get_text())
                            if any(loc in text for loc in
                                   ['台北', '新北', '桃園', '新竹', '台中', '台南', '高雄', '遠端']):
                                location = text
                                break
                        if not location and location_items:
                            location = self.clean_text(location_items[0].get_text())

                    # 提取薪資
                    salary = "面議"
                    salary_elem = card.find('span', class_='b-tag') or card.find('span', class_='job-list-tag')
                    if salary_elem:
                        salary_text = salary_elem.get_text()
                        if '萬' in salary_text or '千' in salary_text or ' in salary_text or any(char.isdigit() for char in salary_text):
                            salary = self.extract_salary(salary_text)

                    # 提取職缺連結
                    job_url = ""
                    if title_elem and title_elem.get('href'):
                        href = title_elem['href']
                        if href.startswith('//'):
                            job_url = 'https:' + href
                        elif href.startswith('/'):
                            job_url = 'https://www.104.com.tw' + href
                        else:
                            job_url = href

                    # 提取工作描述
                    description = f"{title} - {company}"
                    desc_elem = card.find('p', class_='job-list-intro') or card.find('div', class_='job-desc')
                    if desc_elem:
                        desc_text = self.clean_text(desc_elem.get_text())
                        if desc_text:
                            description = desc_text[:100] + "..." if len(desc_text) > 100 else desc_text

                    # 獲取公司Logo
                    logo_url = self.get_company_logo(company)

                    if title and company:  # 確保基本資訊完整
                        job_data = {
                            "id": f"104_{int(time.time())}_{i}",
                            "title": title,
                            "company": company,
                            "salary": salary,
                            "location": location or "未提供",
                            "url": job_url or f"https://www.104.com.tw/jobs/search/?keyword={encoded_keyword}",
                            "platform": "104人力銀行",
                            "logo_url": logo_url,
                            "description": description,
                            "requirements": ["請查看個別職缺詳情", "具相關工作經驗優先"],
                            "tags": ["104", keyword.lower()],
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        jobs.append(job_data)
                        print(f"✅ 104職缺 {i + 1}: {title} - {company}")

                    self.delay_random()  # 隨機延遲

                except Exception as e:
                    print(f"❌ 解析104職缺 {i + 1} 時發生錯誤：{e}")
                    continue

            print(f"🎉 104 搜尋完成，找到 {len(jobs)} 個職缺")

        except Exception as e:
            print(f"❌ 爬取 104 職缺失敗：{e}")

        return jobs

    def crawl_1111_jobs(self, keyword, limit=10):
        """爬取 1111 人力銀行職缺 - 真實搜尋"""
        jobs = []

        try:
            # 1111 搜尋 URL
            encoded_keyword = urllib.parse.quote(keyword)
            search_url = f"https://www.1111.com.tw/search/job?ks={encoded_keyword}"

            print(f"🔍 正在搜尋 1111 職缺：{keyword}")
            response = self.session.get(search_url, timeout=15)

            if response.status_code != 200:
                print(f"❌ 1111 請求失敗，狀態碼：{response.status_code}")
                return jobs

            soup = BeautifulSoup(response.text, 'html.parser')

            # 1111 的職缺列表
            job_items = soup.find_all('div', class_='joblist_cont') or soup.find_all('article', class_='job-item')

            print(f"🔍 找到 {len(job_items)} 個職缺元素")

            for i, item in enumerate(job_items[:limit]):
                try:
                    # 提取職位名稱
                    title = ""
                    title_elem = item.find('a', class_='joblist_job_name') or item.find('h4', class_='job-title')
                    if title_elem:
                        title = self.clean_text(title_elem.get_text())

                    # 提取公司名稱
                    company = ""
                    company_elem = item.find('a', class_='joblist_comp_name') or item.find('h5', class_='company-name')
                    if company_elem:
                        company = self.clean_text(company_elem.get_text())

                    # 提取地點
                    location = ""
                    location_elem = item.find('div', class_='joblist_job_condition') or item.find('span',
                                                                                                  class_='job-location')
                    if location_elem:
                        location_text = self.clean_text(location_elem.get_text())
                        # 提取地點關鍵字
                        for loc in ['台北', '新北', '桃園', '新竹', '台中', '台南', '高雄', '遠端']:
                            if loc in location_text:
                                location = loc
                                break
                        if not location:
                            location = location_text[:10] if location_text else "未提供"

                    # 提取薪資
                    salary = "面議"
                    salary_elem = item.find('div', class_='joblist_money') or item.find('span', class_='job-salary')
                    if salary_elem:
                        salary = self.extract_salary(salary_elem.get_text())

                    # 提取職缺連結
                    job_url = ""
                    if title_elem and title_elem.get('href'):
                        href = title_elem['href']
                        if href.startswith('/'):
                            job_url = 'https://www.1111.com.tw' + href
                        else:
                            job_url = href

                    # 獲取公司Logo
                    logo_url = self.get_company_logo(company)

                    # 工作描述
                    description = f"{company} 的 {title} 職位"

                    if title and company:
                        job_data = {
                            "id": f"1111_{int(time.time())}_{i}",
                            "title": title,
                            "company": company,
                            "salary": salary,
                            "location": location or "未提供",
                            "url": job_url or f"https://www.1111.com.tw/search/job?ks={encoded_keyword}",
                            "platform": "1111人力銀行",
                            "logo_url": logo_url,
                            "description": description,
                            "requirements": ["請查看個別職缺詳情", "具相關工作經驗優先"],
                            "tags": ["1111", keyword.lower()],
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        jobs.append(job_data)
                        print(f"✅ 1111職缺 {i + 1}: {title} - {company}")

                    self.delay_random()

                except Exception as e:
                    print(f"❌ 解析1111職缺 {i + 1} 時發生錯誤：{e}")
                    continue

            print(f"🎉 1111 搜尋完成，找到 {len(jobs)} 個職缺")

        except Exception as e:
            print(f"❌ 爬取 1111 職缺失敗：{e}")

        return jobs

    def crawl_yourator_jobs(self, keyword, limit=10):
        """爬取 Yourator 職缺 - 真實搜尋"""
        jobs = []

        try:
            # Yourator 搜尋 URL
            encoded_keyword = urllib.parse.quote(keyword)
            search_url = f"https://www.yourator.co/jobs?q={encoded_keyword}"

            print(f"🔍 正在搜尋 Yourator 職缺：{keyword}")
            response = self.session.get(search_url, timeout=15)

            if response.status_code != 200:
                print(f"❌ Yourator 請求失敗，狀態碼：{response.status_code}")
                return jobs

            soup = BeautifulSoup(response.text, 'html.parser')

            # 根據實際的HTML結構調整選擇器
            job_cards = soup.find_all('div', class_='job-item') or soup.find_all('a', class_='job-link')

            for i, card in enumerate(job_cards[:limit]):
                try:
                    # 基於Yourator的實際結構提取資訊
                    title_elem = card.find('h3') or card.find('h4') or card.find('div', class_='job-title')
                    title = self.clean_text(title_elem.get_text()) if title_elem else ""

                    company_elem = card.find('div', class_='company-name') or card.find('span', class_='company')
                    company = self.clean_text(company_elem.get_text()) if company_elem else ""

                    # 獲取公司Logo
                    logo_url = self.get_company_logo(company)

                    if title and company:
                        job_data = {
                            "id": f"yourator_{int(time.time())}_{i}",
                            "title": title,
                            "company": company,
                            "salary": "面議",
                            "location": "台北市",
                            "url": f"https://www.yourator.co/jobs?q={encoded_keyword}",
                            "platform": "Yourator",
                            "logo_url": logo_url,
                            "description": f"{title} - {company}",
                            "requirements": ["請查看個別職缺詳情"],
                            "tags": ["yourator", keyword.lower()],
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        jobs.append(job_data)
                        print(f"✅ Yourator職缺 {i + 1}: {title} - {company}")

                    self.delay_random()

                except Exception as e:
                    print(f"❌ 解析Yourator職缺 {i + 1} 時發生錯誤：{e}")
                    continue

            print(f"🎉 Yourator 搜尋完成，找到 {len(jobs)} 個職缺")

        except Exception as e:
            print(f"❌ 爬取 Yourator 職缺失敗：{e}")

        return jobs

    def search_all_platforms(self, keyword, limit_per_platform=5):
        """搜尋所有平台的職缺"""
        print(f"🚀 開始搜尋關鍵字：{keyword}")

        all_jobs = []

        # 搜尋 104 人力銀行
        try:
            jobs_104 = self.crawl_104_jobs(keyword, limit_per_platform)
            all_jobs.extend(jobs_104)
        except Exception as e:
            print(f"❌ 104搜尋失敗：{e}")

        self.delay_random()

        # 搜尋 1111 人力銀行
        try:
            jobs_1111 = self.crawl_1111_jobs(keyword, limit_per_platform)
            all_jobs.extend(jobs_1111)
        except Exception as e:
            print(f"❌ 1111搜尋失敗：{e}")

        self.delay_random()

        # 搜尋 Yourator
        try:
            jobs_yourator = self.crawl_yourator_jobs(keyword, limit_per_platform)
            all_jobs.extend(jobs_yourator)
        except Exception as e:
            print(f"❌ Yourator搜尋失敗：{e}")

        print(f"🎉 搜尋完成！總共找到 {len(all_jobs)} 個職缺")

        # 儲存到 JSON 檔案
        self.save_jobs_to_file(all_jobs, keyword)

        return all_jobs

    def save_jobs_to_file(self, jobs, keyword=""):
        """儲存職缺到 JSON 檔案"""
        try:
            data = {
                "jobs": jobs,
                "keyword": keyword,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_count": len(jobs)
            }

            with open('jobs.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"📁 職缺資料已儲存到 jobs.json")

        except Exception as e:
            print(f"❌ 儲存職缺資料失敗：{e}")


# 測試函數
def test_crawler():
    """測試爬蟲功能"""
    crawler = JobCrawler()

    # 測試搜尋
    test_keywords = ["Python", "前端工程師", "數據分析"]

    for keyword in test_keywords:
        print(f"\n🧪 測試關鍵字: {keyword}")
        jobs = crawler.search_all_platforms(keyword, 2)

        print(f"\n📋 搜尋結果預覽：")
        for job in jobs[:3]:
            print(f"• {job['title']} - {job['company']} ({job['platform']})")
            print(f"  💰 {job['salary']} | 📍 {job['location']}")
            print(f"  🏢 Logo: {job['logo_url']}")
            print()


if __name__ == "__main__":
    test_crawler()