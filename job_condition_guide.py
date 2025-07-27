import re
import jieba
from datetime import datetime
import json


class JobConditionGuide:
    """智能職缺條件引導系統"""

    def __init__(self):
        # 薪資關鍵字模式
        self.salary_patterns = {
            'monthly': [r'(\d+)k', r'(\d+)千', r'月薪(\d+)', r'(\d+)萬/月', r'(\d+)萬'],
            'yearly': [r'年薪(\d+)', r'(\d+)萬/年', r'年收(\d+)'],
            'hourly': [r'時薪(\d+)', r'(\d+)/小時']
        }

        # 地點關鍵字
        self.location_keywords = {
            '台北': ['台北', '信義', '大安', '中山', '松山', '內湖', '南港', '士林', '北投'],
            '新北': ['新北', '板橋', '新莊', '中和', '永和', '土城', '三重', '蘆洲', '汐止'],
            '桃園': ['桃園', '中壢', '平鎮', '八德', '楊梅', '龜山'],
            '新竹': ['新竹', '竹北', '湖口', '關埔', '科學園區'],
            '台中': ['台中', '西屯', '南屯', '北屯', '大里', '太平', '烏日'],
            '台南': ['台南', '永康', '仁德', '歸仁', '關廟'],
            '高雄': ['高雄', '鳳山', '三民', '左營', '楠梓', '岡山'],
            '遠端': ['遠端', 'remote', '在家', '居家', 'wfh', '彈性']
        }

        # 產業關鍵字
        self.industry_keywords = {
            '科技業': ['軟體', '科技', 'IT', '資訊', '網路', '電商', '遊戲', 'AI', '人工智慧'],
            '金融業': ['銀行', '金融', '保險', '證券', '投資', '理財', 'fintech'],
            '製造業': ['製造', '工廠', '生產', '品管', '工程', '機械'],
            '服務業': ['服務', '餐飲', '零售', '旅遊', '物流', '客服'],
            '醫療業': ['醫療', '醫院', '診所', '護理', '藥局', '生技'],
            '教育業': ['教育', '學校', '補習', '培訓', '講師'],
            '媒體業': ['媒體', '廣告', '行銷', '公關', '新聞', '出版'],
            '新創': ['新創', 'startup', '創業', '團隊']
        }

        # 工作年限關鍵字
        self.experience_keywords = {
            '新鮮人': ['新鮮人', '應屆', '無經驗', '0年', '實習'],
            '1-3年': ['1年', '2年', '3年', '初級', 'junior'],
            '3-5年': ['3年', '4年', '5年', '中級', 'mid'],
            '5年以上': ['5年以上', '資深', 'senior', '主管', '經理']
        }

    def parse_natural_language_conditions(self, user_input):
        """解析用戶的自然語言輸入，提取職缺條件"""

        # 初始化條件
        conditions = {
            'job_title': '',
            'salary': {
                'min': None,
                'max': None,
                'type': 'monthly'  # monthly, yearly, hourly
            },
            'location': [],
            'industry': [],
            'experience': '',
            'work_type': '',  # 遠端、現場、混合
            'company_type': [],  # 外商、新創、上市
            'original_text': user_input,
            'missing_info': []  # 缺少的資訊
        }

        # 使用jieba分詞
        words = jieba.lcut(user_input.lower())
        text_lower = user_input.lower()

        # 1. 提取職位名稱（移除條件詞後的主要關鍵字）
        job_title = self._extract_job_title(user_input, words)
        conditions['job_title'] = job_title

        # 2. 提取薪資條件
        salary_info = self._extract_salary(user_input)
        conditions['salary'].update(salary_info)

        # 3. 提取地點
        locations = self._extract_locations(text_lower)
        conditions['location'] = locations

        # 4. 提取產業
        industries = self._extract_industries(text_lower)
        conditions['industry'] = industries

        # 5. 提取工作經驗
        experience = self._extract_experience(text_lower)
        conditions['experience'] = experience

        # 6. 提取工作型態
        work_type = self._extract_work_type(text_lower)
        conditions['work_type'] = work_type

        # 7. 提取公司類型
        company_types = self._extract_company_type(text_lower)
        conditions['company_type'] = company_types

        # 8. 檢查缺少的重要資訊
        missing_info = self._check_missing_info(conditions)
        conditions['missing_info'] = missing_info

        return conditions

    def _extract_job_title(self, text, words):
        """提取職位名稱 - 完全重寫，確保準確性"""

        # 直接職位映射（最高優先級）
        direct_job_mapping = {
            # 商務管理類
            '產品經理': '產品經理',
            '專案經理': '專案經理',
            '產品manager': '產品經理',
            'pm': '產品經理',
            'product manager': '產品經理',
            'project manager': '專案經理',

            # 設計類
            'ui設計師': 'UI設計師',
            'ux設計師': 'UX設計師',
            'ui/ux': 'UI/UX設計師',
            '視覺設計師': '視覺設計師',
            '平面設計師': '平面設計師',
            '網頁設計師': '網頁設計師',

            # 工程師類
            '軟體工程師': '軟體工程師',
            '前端工程師': '前端工程師',
            '後端工程師': '後端工程師',
            '全端工程師': '全端工程師',
            'python工程師': 'Python工程師',
            'java工程師': 'Java工程師',
            'javascript工程師': 'JavaScript工程師',

            # 數據類
            '數據分析師': '數據分析師',
            '資料分析師': '數據分析師',
            '資料科學家': '資料科學家',
            'data analyst': '數據分析師',
            'data scientist': '資料科學家',

            # 營運類
            '營運專員': '營運專員',
            '行銷專員': '行銷專員',
            '業務代表': '業務代表',
            '客服專員': '客服專員',

            # 財務會計類
            '會計師': '會計師',
            '財務專員': '財務專員',
            '稽核': '稽核',

            # 人力資源類
            '人資專員': '人資專員',
            '人力資源': '人資專員',
            'hr': '人資專員',

            # 其他專業類
            '法務': '法務專員',
            '律師': '律師',
            '護理師': '護理師',
            '醫師': '醫師',
            '老師': '老師',
            '講師': '講師',
            '翻譯': '翻譯',
            '編輯': '編輯',
            '記者': '記者',

            # 技術支援類
            '系統管理員': '系統管理員',
            'devops': 'DevOps工程師',
            '測試工程師': '測試工程師',
            '品質保證': 'QA工程師',
            '資安工程師': '資安工程師',

            # 銷售類
            '銷售': '業務代表',
            '業務': '業務代表',
            'sales': '業務代表',

            # 實習/新鮮人
            '實習生': '實習生',
            '新鮮人': '新鮮人職缺',
            '應屆畢業生': '新鮮人職缺'
        }

        # 將輸入文字轉為小寫進行比對
        text_lower = text.lower().strip()

        # 1. 直接完全匹配
        for key, value in direct_job_mapping.items():
            if key in text_lower:
                return value

        # 2. 從原始文字中提取關鍵詞
        # 移除條件詞和常見修飾詞
        condition_words = [
            '薪資', '薪水', '月薪', '年薪', '地點', '台北', '新竹', '台中', '台南', '高雄', '桃園', '新北',
            '遠端', '年經驗', '經驗', '新鮮人', '萬', '以上', '以下', '左右', '大約', '希望', '想要',
            '找', '工作', '職缺', '的', '我', '想', '要', '有', '年', '以上', '外商', '新創'
        ]

        # 使用 jieba 分詞
        words = jieba.lcut(text)

        # 過濾出可能的職位詞彙
        job_candidates = []
        for word in words:
            word_clean = word.strip()
            if (len(word_clean) > 1 and
                    word_clean not in condition_words and
                    not word_clean.isdigit() and
                    not any(char in word_clean for char in ['k', 'K', '萬', '千'])):
                job_candidates.append(word_clean)

        # 3. 組合職位名稱
        if job_candidates:
            # 優先找包含職位關鍵字的組合
            position_keywords = ['經理', '工程師', '設計師', '分析師', '專員', '主管', '總監', '助理', '實習']

            for keyword in position_keywords:
                for candidate in job_candidates:
                    if keyword in candidate:
                        return candidate

            # 如果沒有找到職位關鍵字，返回第一個有意義的詞
            for candidate in job_candidates:
                if len(candidate) >= 2:
                    return candidate

        # 4. 最後備用方案：從原始文字中提取
        # 移除所有條件詞後，取剩餘的第一個詞
        remaining_text = text_lower
        for condition in condition_words:
            remaining_text = remaining_text.replace(condition, ' ')

        remaining_words = remaining_text.split()
        remaining_words = [w for w in remaining_words if len(w) > 1 and not w.isdigit()]

        if remaining_words:
            return remaining_words[0]

        # 如果都沒找到，返回空字串
        return ""

    def _extract_salary(self, text):
        """提取薪資資訊"""
        salary_info = {'min': None, 'max': None, 'type': 'monthly'}

        # 薪資範圍模式 (例如: 50k-80k, 40萬-60萬)
        range_patterns = [
            r'(\d+)([k千萬]?)\s*[-~到]\s*(\d+)([k千萬]?)',
            r'薪資?\s*(\d+)([k千萬]?)\s*[-~到]\s*(\d+)([k千萬]?)',
        ]

        for pattern in range_patterns:
            match = re.search(pattern, text)
            if match:
                min_val, min_unit, max_val, max_unit = match.groups()

                salary_info['min'] = self._normalize_salary(min_val, min_unit or '')
                salary_info['max'] = self._normalize_salary(max_val, max_unit or '')

                # 判斷薪資類型
                if '年薪' in text or '年收' in text:
                    salary_info['type'] = 'yearly'
                elif '時薪' in text:
                    salary_info['type'] = 'hourly'

                break

        # 單一薪資模式 (例如: 50k以上, 至少40萬)
        single_patterns = [
            r'(\d+)([k千萬]?)\s*以上',
            r'至少\s*(\d+)([k千萬]?)',
            r'薪資?\s*(\d+)([k千萬]?)\s*起'
        ]

        if not salary_info['min']:
            for pattern in single_patterns:
                match = re.search(pattern, text)
                if match:
                    val, unit = match.groups()
                    salary_info['min'] = self._normalize_salary(val, unit or '')
                    break

        return salary_info

    def _normalize_salary(self, value, unit):
        """標準化薪資數值"""
        try:
            val = int(value)

            if unit in ['k', 'K']:
                return val * 1000
            elif unit in ['千']:
                return val * 1000
            elif unit in ['萬']:
                return val * 10000
            else:
                # 根據數值大小判斷單位
                if val < 100:  # 可能是萬
                    return val * 10000
                elif val < 1000:  # 可能是千
                    return val * 1000
                else:
                    return val

        except ValueError:
            return None

    def _extract_locations(self, text):
        """提取地點資訊"""
        found_locations = []

        for main_location, sub_locations in self.location_keywords.items():
            for location in sub_locations:
                if location in text:
                    if main_location not in found_locations:
                        found_locations.append(main_location)
                    break

        return found_locations

    def _extract_industries(self, text):
        """提取產業資訊"""
        found_industries = []

        for industry, keywords in self.industry_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    if industry not in found_industries:
                        found_industries.append(industry)
                    break

        return found_industries

    def _extract_experience(self, text):
        """提取工作經驗要求"""
        for exp_level, keywords in self.experience_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return exp_level

        return ''

    def _extract_work_type(self, text):
        """提取工作型態"""
        if any(word in text for word in ['遠端', 'remote', '在家', '居家', 'wfh']):
            return '遠端'
        elif any(word in text for word in ['現場', '辦公室', 'office']):
            return '現場'
        elif any(word in text for word in ['混合', 'hybrid', '彈性']):
            return '混合'

        return ''

    def _extract_company_type(self, text):
        """提取公司類型"""
        company_types = []

        type_keywords = {
            '外商': ['外商', '外資', 'foreign', 'international'],
            '新創': ['新創', 'startup', '創業'],
            '上市': ['上市', '上櫃', '大公司', '知名企業'],
            '傳統產業': ['傳統', '老牌', '歷史悠久']
        }

        for comp_type, keywords in type_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    if comp_type not in company_types:
                        company_types.append(comp_type)
                    break

        return company_types

    def _check_missing_info(self, conditions):
        """檢查缺少的重要資訊"""
        missing = []

        if not conditions['job_title']:
            missing.append('職位名稱')

        if not conditions['salary']['min'] and not conditions['salary']['max']:
            missing.append('期望薪資')

        if not conditions['location']:
            missing.append('工作地點')

        if not conditions['experience']:
            missing.append('工作年限')

        return missing

    def generate_clarification_message(self, conditions):
        """生成澄清問題的訊息"""
        missing = conditions['missing_info']

        if not missing:
            return self._generate_confirmation_message(conditions)

        # 生成詢問缺少資訊的訊息
        clarification_text = "我來幫你搜尋職缺！為了找到更符合你需求的工作，請提供以下資訊：\n\n"

        questions = []

        if '職位名稱' in missing:
            questions.append("🎯 你想找什麼職位？（例如：軟體工程師、產品經理、UI設計師）")

        if '期望薪資' in missing:
            questions.append("💰 期望薪資範圍？（例如：月薪50k-80k、年薪100萬以上）")

        if '工作地點' in missing:
            questions.append("📍 希望在哪個地區工作？（例如：台北、新竹、遠端工作）")

        if '工作年限' in missing:
            questions.append("📊 你的工作經驗？（例如：新鮮人、3年經驗、資深）")

        clarification_text += "\n".join(questions)

        clarification_text += "\n\n💡 你可以一次回答多個問題，例如：\n"
        clarification_text += "「我想找台北的Python工程師，月薪60k以上，有2年經驗」"

        return clarification_text

    def _generate_confirmation_message(self, conditions):
        """生成確認訊息"""
        confirmation_text = "✅ 我了解你的需求了！\n\n"
        confirmation_text += "🔍 搜尋條件：\n"

        if conditions['job_title']:
            confirmation_text += f"• 職位：{conditions['job_title']}\n"

        if conditions['salary']['min'] or conditions['salary']['max']:
            salary_text = ""
            if conditions['salary']['min'] and conditions['salary']['max']:
                salary_text = f"{conditions['salary']['min']:,} - {conditions['salary']['max']:,}"
            elif conditions['salary']['min']:
                salary_text = f"{conditions['salary']['min']:,} 以上"
            elif conditions['salary']['max']:
                salary_text = f"{conditions['salary']['max']:,} 以下"

            salary_type = {'monthly': '月薪', 'yearly': '年薪', 'hourly': '時薪'}[conditions['salary']['type']]
            confirmation_text += f"• 薪資：{salary_type} {salary_text}\n"

        if conditions['location']:
            confirmation_text += f"• 地點：{', '.join(conditions['location'])}\n"

        if conditions['industry']:
            confirmation_text += f"• 產業：{', '.join(conditions['industry'])}\n"

        if conditions['experience']:
            confirmation_text += f"• 經驗：{conditions['experience']}\n"

        if conditions['work_type']:
            confirmation_text += f"• 工作型態：{conditions['work_type']}\n"

        confirmation_text += "\n🚀 正在為你搜尋相關職缺..."

        return confirmation_text

    def create_condition_quick_replies(self, missing_info):
        """建立條件設定的快速回覆按鈕"""
        from linebot.models import QuickReply, QuickReplyButton, MessageAction

        if '職位名稱' in missing_info:
            return QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="軟體工程師", text="軟體工程師")),
                QuickReplyButton(action=MessageAction(label="產品經理", text="產品經理")),
                QuickReplyButton(action=MessageAction(label="UI設計師", text="UI設計師")),
                QuickReplyButton(action=MessageAction(label="數據分析師", text="數據分析師")),
                QuickReplyButton(action=MessageAction(label="前端工程師", text="前端工程師")),
                QuickReplyButton(action=MessageAction(label="後端工程師", text="後端工程師"))
            ])

        elif '工作地點' in missing_info:
            return QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="台北", text="台北")),
                QuickReplyButton(action=MessageAction(label="新竹", text="新竹")),
                QuickReplyButton(action=MessageAction(label="台中", text="台中")),
                QuickReplyButton(action=MessageAction(label="高雄", text="高雄")),
                QuickReplyButton(action=MessageAction(label="遠端工作", text="遠端工作")),
                QuickReplyButton(action=MessageAction(label="不限地點", text="不限地點"))
            ])

        elif '期望薪資' in missing_info:
            return QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="40k-60k", text="月薪40k-60k")),
                QuickReplyButton(action=MessageAction(label="60k-80k", text="月薪60k-80k")),
                QuickReplyButton(action=MessageAction(label="80k-100k", text="月薪80k-100k")),
                QuickReplyButton(action=MessageAction(label="100k以上", text="月薪100k以上")),
                QuickReplyButton(action=MessageAction(label="面議", text="薪資面議"))
            ])

        elif '工作年限' in missing_info:
            return QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="新鮮人", text="新鮮人")),
                QuickReplyButton(action=MessageAction(label="1-3年", text="1-3年經驗")),
                QuickReplyButton(action=MessageAction(label="3-5年", text="3-5年經驗")),
                QuickReplyButton(action=MessageAction(label="5年以上", text="5年以上經驗"))
            ])

        return None

    def is_complete_conditions(self, conditions):
        """檢查條件是否完整"""
        return len(conditions['missing_info']) == 0

    def format_search_conditions(self, conditions):
        """格式化搜尋條件供爬蟲使用"""
        formatted = {
            'keyword': conditions['job_title'],
            'location': conditions['location'][0] if conditions['location'] else '',
            'salary_min': conditions['salary']['min'],
            'salary_max': conditions['salary']['max'],
            'experience': conditions['experience'],
            'industry': conditions['industry'],
            'work_type': conditions['work_type'],
            'company_type': conditions['company_type']
        }

        return formatted


class ConversationManager:
    """對話管理器 - 管理多輪對話"""

    def __init__(self):
        self.user_conversations = {}  # 儲存用戶對話狀態
        self.condition_guide = JobConditionGuide()

    def process_user_message(self, user_id, message):
        """處理用戶訊息"""

        # 取得或建立用戶對話狀態
        if user_id not in self.user_conversations:
            self.user_conversations[user_id] = {
                'stage': 'initial',  # initial, collecting_conditions, ready_to_search
                'conditions': {},
                'attempts': 0
            }

        conversation = self.user_conversations[user_id]
        stage = conversation['stage']

        if stage == 'initial':
            # 第一次輸入，解析條件
            conditions = self.condition_guide.parse_natural_language_conditions(message)
            conversation['conditions'] = conditions

            if self.condition_guide.is_complete_conditions(conditions):
                # 條件完整，可以開始搜尋
                conversation['stage'] = 'ready_to_search'
                response_text = self.condition_guide._generate_confirmation_message(conditions)
                return {
                    'text': response_text,
                    'action': 'search',
                    'conditions': self.condition_guide.format_search_conditions(conditions),
                    'quick_reply': None
                }
            else:
                # 條件不完整，需要收集更多資訊
                conversation['stage'] = 'collecting_conditions'
                response_text = self.condition_guide.generate_clarification_message(conditions)
                quick_reply = self.condition_guide.create_condition_quick_replies(conditions['missing_info'])

                return {
                    'text': response_text,
                    'action': 'collect_info',
                    'conditions': conditions,
                    'quick_reply': quick_reply
                }

        elif stage == 'collecting_conditions':
            # 補充條件資訊
            existing_conditions = conversation['conditions']

            # 將新輸入與現有條件合併
            combined_input = existing_conditions['original_text'] + " " + message
            updated_conditions = self.condition_guide.parse_natural_language_conditions(combined_input)

            conversation['conditions'] = updated_conditions
            conversation['attempts'] += 1

            if self.condition_guide.is_complete_conditions(updated_conditions):
                # 條件完整了
                conversation['stage'] = 'ready_to_search'
                response_text = self.condition_guide._generate_confirmation_message(updated_conditions)

                return {
                    'text': response_text,
                    'action': 'search',
                    'conditions': self.condition_guide.format_search_conditions(updated_conditions),
                    'quick_reply': None
                }
            else:
                # 還是不完整，繼續收集
                if conversation['attempts'] >= 3:
                    # 嘗試太多次，使用現有條件搜尋
                    conversation['stage'] = 'ready_to_search'
                    response_text = "好的，我先用目前的條件為你搜尋，你可以稍後再調整：\n\n"
                    response_text += self.condition_guide._generate_confirmation_message(updated_conditions)

                    return {
                        'text': response_text,
                        'action': 'search',
                        'conditions': self.condition_guide.format_search_conditions(updated_conditions),
                        'quick_reply': None
                    }
                else:
                    response_text = self.condition_guide.generate_clarification_message(updated_conditions)
                    quick_reply = self.condition_guide.create_condition_quick_replies(
                        updated_conditions['missing_info'])

                    return {
                        'text': response_text,
                        'action': 'collect_info',
                        'conditions': updated_conditions,
                        'quick_reply': quick_reply
                    }

        else:  # ready_to_search 或其他狀態
            # 重新開始新的搜尋
            self.user_conversations[user_id] = {
                'stage': 'initial',
                'conditions': {},
                'attempts': 0
            }

            return self.process_user_message(user_id, message)

    def reset_conversation(self, user_id):
        """重設用戶對話狀態"""
        if user_id in self.user_conversations:
            del self.user_conversations[user_id]


# 測試函數
def test_condition_guide():
    """測試條件引導系統"""
    guide = JobConditionGuide()
    conversation_manager = ConversationManager()

    test_inputs = [
        "我想找台北的Python工程師，月薪60k以上",
        "軟體工程師",
        "新竹的前端工程師，有3年經驗",
        "產品經理，遠端工作，薪資80k-120k"
    ]

    print("=== 測試條件解析 ===")
    for i, text in enumerate(test_inputs):
        print(f"\n測試 {i + 1}: {text}")

        # 使用對話管理器處理
        result = conversation_manager.process_user_message(f"test_user_{i}", text)

        print(f"回應: {result['text'][:100]}...")
        print(f"動作: {result['action']}")
        if result['conditions']:
            formatted = result['conditions'] if result['action'] == 'search' else result['conditions']
            print(f"條件: {json.dumps(formatted, ensure_ascii=False, indent=2)}")


if __name__ == "__main__":
    test_condition_guide()