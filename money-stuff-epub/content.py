# -*- coding: utf-8 -*-
"""
Money Stuff 最近 10 期的「中文导读/概要」数据。

说明：summary_html 为编者根据每期公开的标题与主题清单撰写的中文导读，
并非 Bloomberg 原文的翻译。日期标注「约」者表示推断，请以原文为准。
"""

META = {
    "title": "Money Stuff 中文导读合集（最近 10 期）",
    "author": "Matt Levine（Bloomberg Opinion）· 中文导读：编者",
    "language": "zh-CN",
    "description": "Matt Levine «Money Stuff» 专栏最近 10 期的中文导读/概要合集。",
}

# 按时间倒序
EDITIONS = [
    {
        "title_zh": "Robinhood 上线 AI 代理",
        "title_en": "Robinhood Adds Some Agents",
        "date": "2026-05-27",
        "url": "https://www.bloomberg.com/opinion/authors/ARbTQlRLRjE/matthew-s-levine",
        "topics": [
            "Robinhood 推出 AI 代理 / 自动化交易功能",
            "动视暴雪（Activision）相关讨论",
            "指数「快速纳入」机制（index fast-tracking）",
            "First Brands 与关税",
            "Kalshi 上的专业玩家（sharps）",
        ],
        "summary_html": """
<p>本期开篇关注 Robinhood 在平台上引入 AI「代理」——当券商把下单、决策的环节交给
能自动执行的智能体时，谁在为投资负责、监管该如何界定责任，成为有趣的问题。Levine
一贯的角度是：金融产品的「便利」与「风险」往往是同一件事的两面。</p>
<p>随后涉及动视暴雪相关话题、指数「快速纳入」机制，以及 First Brands 在关税环境下的
处境。结尾照例谈预测市场，这次聚焦 Kalshi 上的「sharps」（消息灵通、下注犀利的专业
玩家）如何影响赔率与市场效率。</p>
""",
    },
    {
        "title_zh": "指数基金对 SpaceX 说不了「不」",
        "title_en": "Index Funds Can't Say No to SpaceX",
        "date": "2026-05-26",
        "url": "https://www.bloomberg.com/opinion/authors/ARbTQlRLRjE/matthew-s-levine",
        "topics": [
            "指数基金被动纳入 SpaceX 的逻辑与困境",
            "假碳信用（fake carbon credits）",
            "对真人秀《幸存者》(Survivor) 的押注",
            "Fernando Tatis Jr. 合同进展",
            "「抹除名单」的技术",
            "书单推荐",
        ],
        "summary_html": """
<p>核心论点：指数投资的前提是「你不比市场聪明，所以市场说哪只股票好你就买哪只」。可一旦
SpaceX 这类巨无霸进入相关指数，指数基金就「不得不」买——无论你对它估值或治理有何看法。
Levine 借此探讨被动投资规模膨胀后，「不做判断」本身如何变成一种判断。</p>
<p>本期还覆盖假碳信用的套利、围绕真人秀《幸存者》结果的下注、棒球明星 Fernando Tatis Jr.
的合同更新，以及一段关于「抹除名单 / 删除记录」技术的讨论，末尾附上书单推荐。</p>
""",
    },
    {
        "title_zh": "SpaceX 的投资者无从抱怨",
        "title_en": "SpaceX Investors Can't Complain",
        "date": "2026-05-21",
        "url": "https://www.bloomberg.com/opinion/authors/ARbTQlRLRjE/matthew-s-levine",
        "topics": [
            "SpaceX 投资者权利与治理结构",
            "私募股权 / 高估值私有公司的股东处境",
        ],
        "summary_html": """
<p>承接「SpaceX 与指数」的主题，本期把镜头转向 SpaceX 的投资者：在一家长期保持私有、
话语权高度集中的明星公司里，外部股东即便对条款或治理不满，实际能做的也很有限。Levine
的典型问题是——当一家公司「好到」人人都想进，投资者的议价能力反而被削弱了。</p>
""",
    },
    {
        "title_zh": "「预测」成了新的公开市场",
        "title_en": "Predicting Is the New Public Market",
        "date": "2026-05（约）",
        "url": "https://www.bloomberg.com/opinion/authors/ARbTQlRLRjE/matthew-s-levine",
        "topics": [
            "预测市场（prediction markets）的角色演变",
            "预测市场 vs 传统公开股票市场",
        ],
        "summary_html": """
<p>Levine 持续追踪的主线之一：预测市场（如 Kalshi、Polymarket）正越来越像「公开市场」——
人们在上面对各种事件结果定价、对冲、投机。本期讨论当「下注未来」逐渐承担起价格发现的功能时，
它与传统证券市场在监管、操纵风险和信息效率上的异同。</p>
""",
    },
    {
        "title_zh": "有时候 Andrew Left 是对的",
        "title_en": "Sometimes Andrew Left Was Right",
        "date": "2026-05（约）",
        "url": "https://www.bloomberg.com/opinion/authors/ARbTQlRLRjE/matthew-s-levine",
        "topics": [
            "做空机构香橼（Citron）创始人 Andrew Left",
            "做空者的市场角色与法律风险",
        ],
        "summary_html": """
<p>围绕知名做空者、香橼研究创始人 Andrew Left 展开。Levine 探讨一个微妙之处：即便做空者
因发布报告、操纵指控等面临法律麻烦，他们对某些公司的负面判断在事后可能被证明是对的。
做空者究竟是揭露问题的「市场清道夫」，还是借机牟利的操纵者——本期讨论这条模糊的界线。</p>
""",
    },
    {
        "title_zh": "GameStop 的股票不够用了",
        "title_en": "GameStop Doesn't Have Enough Stock",
        "date": "2026-05-04",
        "url": "https://www.bloomberg.com/opinion/authors/ARbTQlRLRjE/matthew-s-levine",
        "topics": [
            "GameStop 授权股份不足（authorized shares）",
            "高管薪酬方案调整",
            "预测市场做市（prediction market making）",
            "「玩钱」赌场（play-money casinos）",
        ],
        "summary_html": """
<p>本期从 GameStop「授权股份不够发」的技术性问题切入——一家被散户热情推高的公司，想增发
却受限于章程授权上限，这本身就折射出 meme 股的特殊处境。随后谈薪酬方案的调整。</p>
<p>后半部分回到预测市场，讨论「做市」一端的经济学，以及「玩钱」（非真钱）赌场的模式：当
筹码不是真钱时，它到底算游戏还是变相的金融产品？</p>
""",
    },
    {
        "title_zh": "把没人用的电卖掉",
        "title_en": "Sell the Electricity No One Is Using",
        "date": "2026-04-30",
        "url": "https://www.bloomberg.com/opinion/authors/ARbTQlRLRjE/matthew-s-levine",
        "topics": [
            "American Efficient（能效 / 电力套利）",
            "Pershing Square USA（Bill Ackman 的封闭式基金）",
            "BJ's",
        ],
        "summary_html": """
<p>标题指向一种「把闲置 / 未被使用的电力变现」的商业与监管套路，本期以 American Efficient
为例剖析其中的激励与漏洞。随后谈 Bill Ackman 的 Pershing Square USA 封闭式基金近况，以及
零售商 BJ's 的相关话题。Levine 关注的依旧是：制度设计如何被聪明人钻空子。</p>
""",
    },
    {
        "title_zh": "短线交易引发的逼空",
        "title_en": "Short-Swing Short Squeeze",
        "date": "2026-04-29",
        "url": "https://www.bloomberg.com/opinion/authors/ARbTQlRLRjE/matthew-s-levine",
        "topics": [
            "Avis（逼空 / short squeeze）",
            "PSUS 的「双重 IPO」",
            "有限合伙人咨询委员会（LP advisory committees）",
        ],
        "summary_html": """
<p>本期标题玩了个梗：把「short-swing（六个月内短线交易须吐出利润的 16(b) 规则）」和
「short squeeze（逼空）」并置。以 Avis 为例讨论逼空动态；再谈 Pershing Square USA 所谓
「双重 IPO」的结构，以及私募基金里有限合伙人（LP）咨询委员会的治理作用。</p>
""",
    },
    {
        "title_zh": "机器人来做预测",
        "title_en": "The Robots Make the Predictions",
        "date": "2026-04-28",
        "url": "https://www.bloomberg.com/opinion/authors/ARbTQlRLRjE/matthew-s-levine",
        "topics": [
            "Polymarket 上的机器人（bots）",
            "OBDC II 要约收购（tender）",
            "Rivian CEO 薪酬",
        ],
        "summary_html": """
<p>预测市场再度登场：当 Polymarket 上越来越多由机器人 / 算法自动下注，市场赔率到底反映的是
人群智慧还是程序博弈？本期借此讨论自动化对预测市场效率与操纵的影响。此外涉及 OBDC II 的
要约收购，以及 Rivian CEO 的薪酬方案。</p>
""",
    },
    {
        "title_zh": "一切皆是大宗商品欺诈",
        "title_en": "Everything Is Commodities Fraud",
        "date": "2026-04-27",
        "url": "https://www.bloomberg.com/opinion/authors/ARbTQlRLRjE/matthew-s-levine",
        "topics": [
            "「同一突袭」组合注（same-raid parlays）",
            "具备自主行动能力的 AI 对冲基金（agentic AI hedge funds）",
        ],
        "summary_html": """
<p>「Everything Is X」是 Levine 的经典句式（最有名的是「一切皆是证券欺诈」）。本期把它套到
大宗商品上：很多看似不同的行为，最终都能被归入「大宗商品欺诈」的框架。文中讨论一种
「same-raid parlays」的下注玩法，以及「能自主行动的 AI 对冲基金」——当交易决策交给具备
代理能力的 AI 时，责任与监管该如何落地。</p>
""",
    },
]
