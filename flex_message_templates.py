from linebot.models import (
    FlexSendMessage, BubbleContainer, CarouselContainer,
    BoxComponent, TextComponent, ImageComponent, ButtonComponent,
    URIAction, PostbackAction, MessageAction,
    SeparatorComponent
    # 移除 SpacerComponent - 在舊版本中不存在
)


class JobCardBuilder:
    """職缺卡片建構器"""

    @staticmethod
    def create_job_bubble(job_data):
        """建立單一職缺的 Bubble 卡片"""

        # 薪資處理
        salary_text = job_data.get('salary', '面議')
        if salary_text == '面議' or not salary_text:
            salary_display = "💰 薪資面議"
        else:
            salary_display = f"💰 {salary_text}"

        # 地點處理
        location = job_data.get('location', '未提供')
        location_display = f"📍 {location}" if location != '未提供' else "📍 地點未提供"

        # 平台顏色配置
        platform_colors = {
            "104人力銀行": "#FF6B35",
            "1111人力銀行": "#4CAF50",
            "CakeResume": "#2196F3"
        }

        platform = job_data.get('platform', '求職平台')
        platform_color = platform_colors.get(platform, "#757575")

        bubble = BubbleContainer(
            size="kilo",
            header=BoxComponent(
                layout="vertical",
                contents=[
                    # 公司 Logo 區域
                    BoxComponent(
                        layout="horizontal",
                        contents=[
                            ImageComponent(
                                url=job_data.get('logo_url', 'https://via.placeholder.com/60x60?text=LOGO'),
                                flex=0,
                                size="60px",
                                aspect_ratio="1:1"
                            ),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    TextComponent(
                                        text=job_data.get('title', '職位名稱'),
                                        weight="bold",
                                        size="lg",
                                        color="#1DB446",
                                        wrap=True,
                                        max_lines=2
                                    ),
                                    TextComponent(
                                        text=job_data.get('company', '公司名稱'),
                                        size="md",
                                        color="#666666",
                                        wrap=True
                                    )
                                ],
                                margin="md"
                            )
                        ],
                        spacing="sm"
                    )
                ],
                padding_all="20px",
                background_color="#FFFFFF"
            ),
            body=BoxComponent(
                layout="vertical",
                contents=[
                    # 薪資資訊
                    BoxComponent(
                        layout="horizontal",
                        contents=[
                            TextComponent(
                                text="💰",
                                size="lg",
                                flex=0
                            ),
                            TextComponent(
                                text="薪資",
                                size="sm",
                                color="#555555",
                                flex=0
                            ),
                            TextComponent(
                                text=salary_text,
                                size="sm",
                                color="#1DB446",
                                weight="bold",
                                align="end"
                            )
                        ],
                        margin="lg"
                    ),

                    # 分隔線
                    SeparatorComponent(margin="lg"),

                    # 地點資訊
                    BoxComponent(
                        layout="horizontal",
                        contents=[
                            TextComponent(
                                text="📍",
                                size="lg",
                                flex=0
                            ),
                            TextComponent(
                                text="地點",
                                size="sm",
                                color="#555555",
                                flex=0
                            ),
                            TextComponent(
                                text=location,
                                size="sm",
                                color="#666666",
                                align="end",
                                wrap=True
                            )
                        ],
                        margin="lg"
                    ),

                    # 分隔線
                    SeparatorComponent(margin="lg"),

                    # 平台資訊
                    BoxComponent(
                        layout="horizontal",
                        contents=[
                            TextComponent(
                                text="🏢",
                                size="lg",
                                flex=0
                            ),
                            TextComponent(
                                text="平台",
                                size="sm",
                                color="#555555",
                                flex=0
                            ),
                            TextComponent(
                                text=platform,
                                size="sm",
                                color=platform_color,
                                weight="bold",
                                align="end"
                            )
                        ],
                        margin="lg"
                    ),

                    # 工作描述
                    SeparatorComponent(margin="lg"),
                    BoxComponent(
                        layout="vertical",
                        contents=[
                            TextComponent(
                                text="📋 工作內容",
                                size="sm",
                                color="#555555",
                                weight="bold"
                            ),
                            TextComponent(
                                text=job_data.get('description', '請查看個別職缺詳細內容'),
                                size="xs",
                                color="#666666",
                                wrap=True,
                                max_lines=3,
                                margin="sm"
                            )
                        ],
                        margin="lg"
                    ),

                    # 職位要求
                    BoxComponent(
                        layout="vertical",
                        contents=[
                            TextComponent(
                                text="✅ 職位要求",
                                size="sm",
                                color="#555555",
                                weight="bold"
                            ),
                            TextComponent(
                                text="• " + "\n• ".join(
                                    job_data.get('requirements', ['請查看個別職缺要求', '條件因公司而異'])),
                                size="xs",
                                color="#666666",
                                wrap=True,
                                max_lines=4,
                                margin="sm"
                            )
                        ],
                        margin="lg"
                    )
                ],
                spacing="sm",
                padding_all="20px"
            ),
            footer=BoxComponent(
                layout="vertical",
                contents=[
                    # 主要按鈕
                    ButtonComponent(
                        style="primary",
                        height="sm",
                        action=URIAction(
                            label=f"查看職缺 ({platform})",
                            uri=job_data.get('url', 'https://www.google.com')
                        ),
                        color="#1DB446"
                    ),

                    # 用空的 TextComponent 代替 SpacerComponent
                    TextComponent(text=" ", size="xs", color="#FFFFFF"),

                    # 次要按鈕區域
                    BoxComponent(
                        layout="horizontal",
                        contents=[
                            ButtonComponent(
                                flex=1,
                                height="sm",
                                action=PostbackAction(
                                    label="💖 收藏",
                                    data=f"favorite_{job_data.get('id', '')}"
                                ),
                                style="secondary"
                            ),
                            ButtonComponent(
                                flex=1,
                                height="sm",
                                action=MessageAction(
                                    label="👥 分享",
                                    text=f"分享職缺：{job_data.get('title', '')} - {job_data.get('company', '')}"
                                ),
                                style="secondary"
                            )
                        ],
                        spacing="sm"
                    )
                ],
                spacing="sm",
                padding_all="20px"
            )
        )

        return bubble

    @staticmethod
    def create_job_carousel(jobs_list, search_keyword=""):
        """建立職缺旋轉木馬卡片"""

        if not jobs_list:
            # 如果沒有職缺，返回空結果卡片
            empty_bubble = BubbleContainer(
                body=BoxComponent(
                    layout="vertical",
                    contents=[
                        TextComponent(
                            text="😅 沒有找到相關職缺",
                            weight="bold",
                            size="lg",
                            color="#666666"
                        ),
                        TextComponent(
                            text="請嘗試其他關鍵字，例如：\n• Python工程師\n• 前端開發\n• 數據分析",
                            size="sm",
                            color="#999999",
                            wrap=True,
                            margin="md"
                        )
                    ],
                    spacing="md",
                    padding_all="20px"
                )
            )

            return FlexSendMessage(
                alt_text="沒有找到相關職缺",
                contents=empty_bubble
            )

        # 限制最多顯示 10 個職缺卡片
        display_jobs = jobs_list[:10]

        # 建立 Bubble 列表
        bubbles = []
        for job in display_jobs:
            bubble = JobCardBuilder.create_job_bubble(job)
            bubbles.append(bubble)

        # 建立 Carousel
        carousel = CarouselContainer(contents=bubbles)

        # 搜尋結果摘要文字
        total_jobs = len(jobs_list)
        display_count = len(display_jobs)

        if search_keyword:
            alt_text = f"找到 {total_jobs} 個「{search_keyword}」相關職缺，顯示前 {display_count} 個結果"
        else:
            alt_text = f"找到 {total_jobs} 個職缺，顯示前 {display_count} 個結果"

        flex_message = FlexSendMessage(
            alt_text=alt_text,
            contents=carousel
        )

        return flex_message

    @staticmethod
    def create_search_summary_message(total_jobs, keyword):
        """建立搜尋結果摘要訊息"""

        summary_bubble = BubbleContainer(
            body=BoxComponent(
                layout="vertical",
                contents=[
                    BoxComponent(
                        layout="horizontal",
                        contents=[
                            TextComponent(
                                text="✅",
                                size="xl",
                                flex=0
                            ),
                            TextComponent(
                                text=f"找到 {total_jobs} 個職缺",
                                weight="bold",
                                size="lg",
                                color="#1DB446",
                                margin="sm"
                            )
                        ]
                    ),

                    SeparatorComponent(margin="lg"),

                    BoxComponent(
                        layout="vertical",
                        contents=[
                            TextComponent(
                                text="💡 提示：使用「職位｜薪資｜地點｜類型｜年限」可設定更詳細條件",
                                size="sm",
                                color="#666666",
                                wrap=True
                            )
                        ],
                        margin="lg"
                    )
                ],
                spacing="sm",
                padding_all="20px"
            )
        )

        return FlexSendMessage(
            alt_text=f"搜尋結果：找到 {total_jobs} 個職缺",
            contents=summary_bubble
        )