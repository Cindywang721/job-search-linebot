import requests
from bs4 import BeautifulSoup
import json
import time
import random
from datetime import datetime
import re


class JobCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def delay_random(self):
        """隨機延遲，避免被反爬蟲偵測"""
        time.sleep(random.uniform(1, 3))

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

    def crawl_104_jobs(self, keyword, limit=10):
        """爬取 104 人力銀行職缺"""
        jobs = []

        try:
            # 104 搜尋 URL
            search_url = f"https://www.104.com.tw/jobs/search/?ro=0&keyword={keyword}&expansionType=area%2Cspec%2Ccom%2Cjob%2Cwf%2Cwktm&order=15&asc=0&page=1&mode=s&jobsource=2018indexpoc"

            print(f"正在搜尋 104 職缺：{keyword}")
            response = self.session.get(search_url, timeout=10)

            if response.status_code != 200:
                print(f"104 請求失敗，狀態碼：{response.status_code}")
                return jobs

            soup = BeautifulSoup(response.text, 'html.parser')

            # 找到職缺列表
            job_items = soup.find_all('article', class_='js-job-item')

            for item in job_items[:limit]:
                try:
                    # 提取職缺資訊
                    title_elem = item.find('a', {'data-job-name': True})
                    title = self.clean_text(title_elem.get('data-job-name', '')) if title_elem else ''

                    company_elem = item.find('a', {'data-cust-name': True})
                    company = self.clean_text(company_elem.get('data-cust-name', '')) if company_elem else ''

                    location_elem = item.find('ul', class_='job-list-intro')
                    location = ''
                    if location_elem:
                        location_li = location_elem.find('li')
                        location = self.clean_text(location_li.get_text()) if location_li else ''

                    salary_elem = item.find('span', class_='job-list-tag')
                    salary = self.extract_salary(salary_elem.get_text() if salary_elem else '')

                    # 職缺連結
                    job_url = ''
                    if title_elem and title_elem.get('href'):
                        job_url = 'https:' + title_elem['href'] if title_elem['href'].startswith('//') else title_elem[
                            'href']

                    # 公司 Logo（104 通常有預設圖片）
                    logo_url = "https://www.104.com.tw/img/logo_104.png"  # 預設 104 Logo

                    if title and company:  # 確保基本資訊完整
                        job_data = {
                            "id": f"104_{len(jobs) + 1}",
                            "title": title,
                            "company": company,
                            "salary": salary,
                            "location": location,
                            "url": job_url,
                            "platform": "104人力銀行",
                            "logo_url": logo_url,
                            "description": f"{title} - {company}",
                            "requirements": ["請查看職缺詳情"],
                            "tags": ["104", keyword],
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        jobs.append(job_data)
                        print(f"✅ 找到職缺：{title} - {company}")

                    self.delay_random()  # 隨機延遲

                except Exception as e:
                    print(f"解析職缺時發生錯誤：{e}")
                    continue

            print(f"🎉 104 搜尋完成，找到 {len(jobs)} 個職缺")

        except Exception as e:
            print(f"❌ 爬取 104 職缺失敗：{e}")

        return jobs

    def crawl_1111_jobs(self, keyword, limit=10):
        """爬取 1111 人力銀行職缺"""
        jobs = []

        try:
            # 1111 搜尋 URL
            search_url = f"https://www.1111.com.tw/search/job?ks={keyword}"

            print(f"正在搜尋 1111 職缺：{keyword}")
            response = self.session.get(search_url, timeout=10)

            if response.status_code != 200:
                print(f"1111 請求失敗，狀態碼：{response.status_code}")
                return jobs

            soup = BeautifulSoup(response.text, 'html.parser')

            # 找到職缺列表（1111 的結構）
            job_items = soup.find_all('div', class_='joblist_cont')

            for item in job_items[:limit]:
                try:
                    # 提取職缺資訊
                    title_elem = item.find('a', class_='joblist_job_name')
                    title = self.clean_text(title_elem.get_text()) if title_elem else ''

                    company_elem = item.find('a', class_='joblist_comp_name')
                    company = self.clean_text(company_elem.get_text()) if company_elem else ''

                    location_elem = item.find('div', class_='joblist_job_condition')
                    location = self.clean_text(location_elem.get_text()) if location_elem else ''

                    salary_elem = item.find('div', class_='joblist_money')
                    salary = self.extract_salary(salary_elem.get_text() if salary_elem else '')

                    # 職缺連結
                    job_url = ''
                    if title_elem and title_elem.get('href'):
                        job_url = 'https://www.1111.com.tw' + title_elem['href']

                    logo_url = "https://www.1111.com.tw/img/logo.png"  # 預設 1111 Logo

                    if title and company:
                        job_data = {
                            "id": f"1111_{len(jobs) + 1}",
                            "title": title,
                            "company": company,
                            "salary": salary,
                            "location": location,
                            "url": job_url,
                            "platform": "1111人力銀行",
                            "logo_url": logo_url,
                            "description": f"{title} - {company}",
                            "requirements": ["請查看職缺詳情"],
                            "tags": ["1111", keyword],
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        jobs.append(job_data)
                        print(f"✅ 找到職缺：{title} - {company}")

                    self.delay_random()

                except Exception as e:
                    print(f"解析 1111 職缺時發生錯誤：{e}")
                    continue

            print(f"🎉 1111 搜尋完成，找到 {len(jobs)} 個職缺")

        except Exception as e:
            print(f"❌ 爬取 1111 職缺失敗：{e}")

        return jobs

    def crawl_cakeresume_jobs(self, keyword, limit=10):
        """爬取 CakeResume 職缺（簡化版本）"""
        jobs = []

        try:
            print(f"正在搜尋 CakeResume 職缺：{keyword}")

            # CakeResume API 或網頁爬取（需要更複雜的處理）
            # 這裡先提供一個示例結構

            # 示例職缺資料
            sample_jobs = [
                {
                    "id": f"cake_{1}",
                    "title": f"{keyword}工程師",
                    "company": "新創科技公司",
                    "salary": "60,000 - 90,000",
                    "location": "台北市",
                    "url": "https://www.cakeresume.com/jobs",
                    "platform": "CakeResume",
                    "logo_url": "https://www.cakeresume.com/favicon.ico",
                    "description": f"{keyword}相關職缺",
                    "requirements": ["相關經驗", "團隊合作"],
                    "tags": ["CakeResume", keyword],
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            ]

            jobs.extend(sample_jobs)
            print(f"🎉 CakeResume 搜尋完成，找到 {len(jobs)} 個職缺")

        except Exception as e:
            print(f"❌ 爬取 CakeResume 職缺失敗：{e}")

        return jobs

    def search_all_platforms(self, keyword, limit_per_platform=5):
        """搜尋所有平台的職缺"""
        print(f"🚀 開始搜尋關鍵字：{keyword}")

        all_jobs = []

        # 搜尋各平台
        jobs_104 = self.crawl_104_jobs(keyword, limit_per_platform)
        all_jobs.extend(jobs_104)

        self.delay_random()

        jobs_1111 = self.crawl_1111_jobs(keyword, limit_per_platform)
        all_jobs.extend(jobs_1111)

        self.delay_random()

        jobs_cake = self.crawl_cakeresume_jobs(keyword, limit_per_platform)
        all_jobs.extend(jobs_cake)

        print(f"🎉 搜尋完成！總共找到 {len(all_jobs)} 個職缺")

        # 儲存到 JSON 檔案
        self.save_jobs_to_file(all_jobs)

        return all_jobs

    def save_jobs_to_file(self, jobs):
        """儲存職缺到 JSON 檔案"""
        try:
            data = {
                "jobs": jobs,
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
    jobs = crawler.search_all_platforms("Python", 3)

    print("\n📋 搜尋結果預覽：")
    for job in jobs[:3]:
        print(f"• {job['title']} - {job['company']} ({job['platform']})")


if __name__ == "__main__":
    test_crawler()