import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import akshare as ak

# ================= 1. 页面配置与美化 =================
st.set_page_config(
    page_title="AI 财经挖掘终端",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 适配手机端的 CSS 样式
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    /* 按钮样式优化 */
    .stButton>button {
        width: 100%; 
        border-radius: 10px; 
        height: 3.5em; 
        background-color: #ff4b4b; 
        color: white;
        font-weight: bold;
    }
    /* 卡片式展示新闻 */
    .stInfo {background-color: #ffffff; border: 1px solid #e0e0e0; border-left: 5px solid #ff4b4b;}
    </style>
    """, unsafe_allow_html=True)

# ================= 2. 数据获取 (带缓存) =================
@st.cache_data(ttl=600)
def get_news_data():
    try:
        # 获取财联社全球电报
        df = ak.stock_info_global_cls()
        return df
    except Exception as e:
        return None

# ================= 3. 核心应用逻辑 =================
def app():
    st.title("💹 AI 财经助手 (Qwen)")
    
    # 核心：从 Secrets 读取通义千问 API Key
    # 变量名依然沿用之前的，方便你在 Secrets 替换内容
    api_key = st.secrets.get("ZHIPU_API_KEY", "")
    
    if not api_key:
        st.error("❌ 尚未在 Secrets 中配置 API Key")
        st.stop()

    news_df = get_news_data()
    
    if news_df is None or news_df.empty:
        st.warning("🔄 数据加载中，请稍后刷新...")
        st.stop()

    # 初始化新闻索引
    if 'selected_idx' not in st.session_state:
        st.session_state.selected_idx = 0

    # 手机端下拉选择新闻
    st.subheader("📰 实时简讯列表")
    news_titles = news_df.head(15)['标题'].tolist()
    selected_title = st.selectbox("点击切换新闻查看详情：", news_titles, index=st.session_state.selected_idx)
    
    # 获取选中新闻详情
    current_idx = news_titles.index(selected_title)
    st.session_state.selected_idx = current_idx
    current_news = news_df.iloc[current_idx]

    # 展示详情内容
    st.markdown("---")
    with st.container():
        st.markdown(f"### {current_news['标题']}")
        st.caption(f"📅 {current_news['发布日期']} {current_news['发布时间']}")
        st.info(current_news['内容'])

    # AI 分析按钮
    if st.button("🚀 通义千问深度挖掘"):
        with st.spinner("Qwen 正在解析逻辑链条..."):
            try:
                # 初始化通义千问 (兼容 OpenAI 格式)
                llm = ChatOpenAI(
                    api_key=api_key,
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                    model="qwen-plus",
                    temperature=0.2
                )
                
                # 设定分析师人格与任务
                prompt = ChatPromptTemplate.from_messages([
                    ("system", """你是一位资深的证券分析师。请针对用户提供的新闻内容进行如下分析：
                    1. 核心逻辑：用一句话提炼新闻对资本市场的影响。
                    2. 概念识别：识别最直接受益的产业链板块（如：低空经济、存储芯片等）。
                    3. 龙头挖掘：列出3只最相关的A股龙头公司，必须包含股票名称和代码，并简述理由。
                    请使用 Markdown 格式输出，个股部分请使用表格。"""),
                    ("user", "新闻标题: {title}\n新闻内容: {content}")
                ])
                
                chain = prompt | llm | StrOutputParser()
                result = chain.invoke({
                    "title": current_news['标题'],
                    "content": current_news['内容']
                })
                
                st.success("✅ 分析完成")
                st.markdown(result)
                
            except Exception as e:
                st.error(f"分析失败: {str(e)}")
                st.info("请检查 Secrets 中的 Key 是否为 sk- 开头的通义千问 Key。")

if __name__ == "__main__":
    app()
