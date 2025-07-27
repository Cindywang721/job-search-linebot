import json
import time
import random
from datetime import datetime
import urllib.parse


class ZeroDependencyCrawler:
    """完全零依賴的職缺生成系統"""

    def __init__(self):
        # 完整的職缺資料庫
        self.job_database = {
            # 產品管理類
            '產品經理': {
                'titles': [
                    '產品經理', '資深產品經理', '產品總監', '產品企劃專員',
                    '產品營運經理', '數位產品經理', '產品策略經理', '產品開發經理'
                ],
                'companies': [
                    '科技新創公司', 'AI科技公司', '電商平台', '金融科技公司',
                    '軟體開發公司', '數位行銷公司', '遊戲開發公司', '雲端服務商'
                ],
                'salaries': [
                    '60,000-90,000', '80,000-120,000', '100,000-150,000',
                    '120,000-180,000', '面議', '年薪 150-250萬', '年薪 200-350萬'
                ],
                'locations': ['台北市', '新北市', '桃園市', '新竹市', '台中市', '遠端工作'],
                'descriptions': [
                    '負責產品策略規劃與執行，與工程團隊協作開發創新產品',
                    '分析市場趨勢，制定產品發展方向，提升用戶體驗與滿意度',
                    '跨部門溝通協調，推動產品從概念到上市的完整開發流程',
                    '數據驅動產品決策，持續優化產品功能與商業模式',
                    '管理產品生命週期，確保產品目標與公司策略一致'
                ]
            },

            # 軟體工程師類
            '軟體工程師': {
                'titles': [
                    '軟體工程師', '前端工程師', '後端工程師', '全端工程師',
                    '資深軟體工程師', 'Python工程師', 'Java工程師', 'JavaScript工程師'
                ],
                'companies': [
                    '軟體開發公司', '科技新創', '系統整合商', '遊戲公司',
                    '雲端服務商', 'AI科技公司', '金融科技', '電商平台'
                ],
                'salaries': [
                    '50,000-80,000', '70,000-110,000', '90,000-140,000',
                    '110,000-160,000', '面議', '年薪 120-280萬', '年薪 150-350萬'
                ],
                'locations': ['台北市', '新北市', '桃園市', '新竹市', '台中市', '遠端工作'],
                'descriptions': [
                    '參與系統架構設計，開發高效能、可擴展的應用程式',
                    '使用現代技術棧進行開發，重視程式碼品質與系統效能',
                    '與產品團隊密切合作，實現創新功能與優質用戶體驗',
                    '負責系統維護與優化，確保服務穩定性與可靠性',
                    '參與技術選型與架構決策，推動技術創新與團隊成長'
                ]
            },

            # UI/UX設計師類
            '設計師': {
                'titles': [
                    'UI設計師', 'UX設計師', '視覺設計師', '產品設計師',
                    '網頁設計師', '平面設計師', '品牌設計師', '互動設計師'
                ],
                'companies': [
                    '設計公司', '廣告代理商', '品牌顧問公司', '電商平台',
                    '媒體公司', '科技公司', '遊戲公司', '新創企業'
                ],
                'salaries': [
                    '45,000-70,000', '60,000-95,000', '75,000-120,000',
                    '90,000-140,000', '面議', '年薪 80-200萬', '年薪 120-250萬'
                ],
                'locations': ['台北市', '新北市', '桃園市', '新竹市', '台中市', '遠端工作'],
                'descriptions': [
                    '設計直觀易用的使用者介面，提升產品的視覺效果與互動體驗',
                    '進行使用者研究與測試，設計符合用戶需求的產品介面',
                    '與產品經理和工程師協作，確保設計理念完美實現',
                    '建立設計系統與規範，維持品牌視覺的一致性',
                    '關注設計趨勢與技術發展，持續提升設計專業能力'
                ]
            },

            # 數據分析師類
            '數據分析師': {
                'titles': [
                    '數據分析師', '商業分析師', '資料科學家', '市場分析師',
                    '營運分析師', '財務分析師', '數據科學家', 'BI分析師'
                ],
                'companies': [
                    '顧問公司', '金融機構', '電商平台', '科技公司',
                    '市場研究公司', '新創企業', '製造業', '零售業'
                ],
                'salaries': [
                    '55,000-85,000', '70,000-110,000', '90,000-140,000',
                    '110,000-160,000', '面議', '年薪 120-250萬', '年薪 150-300萬'
                ],
                'locations': ['台北市', '新北市', '桃園市', '新竹市', '台中市', '遠端工作'],
                'descriptions': [
                    '分析業務數據，提供深入洞察和決策建議',
                    '建立數據模型和儀表板，預測市場趨勢和用戶行為',
                    '製作數據報告，協助管理層制定策略方向',
                    '設計實驗與A/B測試，評估產品功能效果',
                    '跨部門合作，推動數據驅動的商業決策'
                ]
            },

            # 業務銷售類
            '業務': {
                'titles': [
                    '業務代表', '業務經理', '銷售專員', '客戶經理',
                    '商務開發', '大客戶經理', '通路業務', '海外業務'
                ],
                'companies': [
                    '科技公司', '製造業', '服務業', '貿易公司',
                    '金融機構', '保險公司', '房地產', '軟體公司'
                ],
                'salaries': [
                    '35,000-60,000', '50,000-80,000', '70,000-120,000',
                    '底薪+獎金', '無上限', '年薪 80-300萬', '年薪 120-500萬'
                ],
                'locations': ['台北市', '新北市', '桃園市', '新竹市', '台中市', '高雄市'],
                'descriptions': [
                    '開發新客戶，維護既有客戶關係，達成銷售目標',
                    '了解客戶需求，提供專業的產品解決方案',
                    '建立長期合作關係，創造雙贏的商業價值',
                    '參與商務談判，協助合約簽署與執行',
                    '分析市場競爭情況，制定有效的銷售策略'
                ]
            },

            # 會計財務類
            '會計': {
                'titles': [
                    '會計師', '財務專員', '稽核員', '成本會計',
                    '財務分析師', '會計主管', '財務經理', '稅務專員'
                ],
                'companies': [
                    '會計事務所', '金融機構', '製造業', '上市公司',
                    '貿易公司', '服務業', '建設公司', '投資公司'
                ],
                'salaries': [
                    '38,000-58,000', '50,000-75,000', '65,000-100,000',
                    '80,000-120,000', '面議', '年薪 60-150萬', '年薪 100-200萬'
                ],
                'locations': ['台北市', '新北市', '桃園市', '新竹市', '台中市', '高雄市'],
                'descriptions': [
                    '處理日常會計作業，編製財務報表和稅務申報',
                    '進行財務分析，協助管理層制定財務決策',
                    '確保財務作業符合法規，維護公司財務健全',
                    '成本控制與預算編製，提升營運效率',
                    '參與投資評估與財務規劃，支援業務發展'
                ]
            },

            # 人力資源類
            '人資': {
                'titles': [
                    '人資專員', '招募專員', '薪酬福利專員', '教育訓練專員',
                    '人資經理', '組織發展專員', '績效管理專員', '勞資關係專員'
                ],
                'companies': [
                    '各行各業', '人力資源公司', '獵頭公司', '大型企業',
                    '跨國公司', '製造業', '服務業', '科技公司'
                ],
                'salaries': [
                    '40,000-65,000', '55,000-80,000', '70,000-105,000',
                    '85,000-130,000', '面議', '年薪 70-180萬', '年薪 100-250萬'
                ],
                'locations': ['台北市', '新北市', '桃園市', '新竹市', '台中市', '高雄市'],
                'descriptions': [
                    '負責人才招募，建立有效的人力資源管理制度',
                    '規劃員工訓練發展，提升組織整體競爭力',
                    '處理勞資關係，確保企業人力資源政策執行',
                    '設計薪酬福利制度，提升員工滿意度與留任率',
                    '推動組織變革與文化建設，打造優質工作環境'
                ]
            },

            # 行銷企劃類
            '行銷': {
                'titles': [
                    '行銷專員', '數位行銷', '品牌行銷', '內容行銷',
                    '成長行銷', '行銷經理', '社群經營', '廣告投放專員'
                ],
                'companies': [
                    '行銷公司', '品牌企業', '媒體公司', '廣告代理商',
                    '電商平台', '新創企業', '零售業', '服務業'
                ],
                'salaries': [
                    '42,000-68,000', '58,000-90,000', '75,000-120,000',
                    '90,000-140,000', '面議', '年薪 80-200萬', '年薪 120-250萬'
                ],
                'locations': ['台北市', '新北市', '桃園市', '新竹市', '台中市', '遠端工作'],
                'descriptions': [
                    '規劃執行行銷活動，提升品牌知名度和市場佔有率',
                    '管理社群媒體和數位廣告，優化行銷投資報酬率',
                    '分析市場數據和消費者行為，制定精準的行銷策略',
                    '創作優質內容，建立品牌形象與用戶連結',
                    '跨部門合作，推動整合行銷傳播策略'
                ]
            },

            # 營運管理類
            '營運': {
                'titles': [
                    '營運專員', '營運經理', '業務營運', '平台營運',
                    '電商營運', '供應鏈管理', '物流營運', '客戶成功經理'
                ],
                'companies': [
                    '電商平台', '零售連鎖', '物流公司', '服務業',
                    '新創企業', '製造業', '餐飲業', '金融業'
                ],
                'salaries': [
                    '40,000-65,000', '55,000-85,000', '70,000-110,000',
                    '85,000-130,000', '面議', '年薪 70-180萬', '年薪 100-220萬'
                ],
                'locations': ['台北市', '新北市', '桃園市', '新竹市', '台中市', '高雄市'],
                'descriptions': [
                    '優化營運流程，提升營運效率和客戶滿意度',
                    '監控關鍵指標，制定改善策略和執行計畫',
                    '跨部門協調，確保業務目標順利達成',
                    '管理供應商關係，確保服務品質與成本控制',
                    '推動數位轉型，提升營運自動化程度'
                ]
            }
        }

    def search_all_platforms(self, keyword, location="", salary_min="", salary_max="", limit_per_platform=5):
        """搜尋所有平台的職缺"""
        print(f"🚀 開始搜尋：{keyword}")

        # 生成職缺
        jobs = self.generate_jobs_by_keyword(keyword, location, limit_per_platform * 3)

        print(f"✅ 生成 {len(jobs)} 個職缺")
        return jobs

    def generate_jobs_by_keyword(self, keyword, location="", limit=15):
        """根據關鍵字生成職缺"""

        # 智能匹配職位類別
        matched_category = None
        keyword_lower = keyword.lower()

        # 完全匹配
        for category, data in self.job_database.items():
            if keyword_lower == category:
                matched_category = data
                break

        # 部分匹配
        if not matched_category:
            for category, data in self.job_database.items():
                if (category in keyword_lower or
                        keyword_lower in category or
                        any(keyword_lower in title.lower() for title in data['titles']) or
                        any(title.lower() in keyword_lower for title in data['titles'])):
                    matched_category = data
                    break

        # 如果沒有匹配到，使用通用模板
        if not matched_category:
            matched_category = {
                'titles': [f'{keyword}專員', f'{keyword}經理', f'資深{keyword}', f'{keyword}主管', f'{keyword}顧問'],
                'companies': ['成長企業', '專業機構', '領導品牌', '創新公司', '優質團隊'],
                'salaries': ['35,000-60,000', '50,000-80,000', '65,000-100,000', '面議', '具競爭力薪資'],
                'locations': ['台北市', '新北市', '新竹市', '台中市', '高雄市'],
                'descriptions': [f'負責{keyword}相關業務，歡迎有經驗或有興趣學習的人才加入']
            }

        # 生成職缺
        jobs = []
        platforms = ['104人力銀行', 'CakeResume', 'Yourator']

        for i in range(limit):
            # 隨機選擇職位資訊
            title = random.choice(matched_category['titles'])
            company = random.choice(matched_category['companies'])
            salary = random.choice(matched_category['salaries'])
            description = random.choice(matched_category['descriptions'])
            platform = platforms[i % 3]

            # 地點處理
            if location:
                job_location = location
            else:
                job_location = random.choice(matched_category['locations'])

            # 生成真實搜尋連結
            encoded_keyword = urllib.parse.quote(keyword)
            if platform == '104人力銀行':
                job_url = f"https://www.104.com.tw/jobs/search/?keyword={encoded_keyword}"
            elif platform == 'CakeResume':
                job_url = f"https://www.cakeresume.com/jobs?q={encoded_keyword}"
            else:
                job_url = f"https://www.yourator.co/jobs?q={encoded_keyword}"

            # 公司Logo
            company_initial = company[0] if company else 'C'
            colors = ['4285F4', 'EA4335', 'FBBC04', '34A853', 'FF6D01', '9C27B0', '795548', '607D8B']
            color = colors[hash(company + str(i)) % len(colors)]
            logo_url = f"https://via.placeholder.com/80x80/{color}/FFFFFF?text={company_initial}"

            job_data = {
                "id": f"zero_dep_{int(time.time())}_{i}",
                "title": title,
                "company": company,
                "salary": salary,
                "location": job_location,
                "url": job_url,
                "platform": platform,
                "logo_url": logo_url,
                "description": description,
                "requirements": ["相關工作經驗", "良好溝通能力", "團隊合作精神", "學習能力強"],
                "tags": [keyword.lower(), "零依賴生成"],
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            jobs.append(job_data)

        return jobs