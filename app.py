import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import akshare as ak

# ================= 1. 页面配置与美化 =================
st.set_page_config(
    page_title="AI 财经挖掘终端",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 强制手机端适配 CSS
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stButton>button {width: 100%; border-radius: 8px; height: 3em; background-color: #2563eb; color: white;}
    .stInfo {background-color: #f0f4ff; border-left: 5px solid #2563eb;}
    </style>
    """, unsafe_allow_html=True)

# ================= 2. 数据获取 (带缓存防止卡顿) =================
@st.cache_data(ttl=600)
def get_news_data():
    try:
        # 获取财联社电报数据
        df = ak.stock_info_global_cls()
        return df
    except Exception as e:
        return None

# ================= 3. 核心应用 =================
def app():
    st.title("🤖 AI 财经助手")
    
    # 安全获取 API Key
    # 优先从 Streamlit 后台 Secrets 读取，如果没有则报错提醒
    api_key = st.secrets.get("ZHIPU_API_KEY", "")
    
    if not api_key or api_key == "":
        st.error("❌ 未检测到 API Key。请在 Streamlit Advanced Settings 中配置 ZHIPU_API_KEY")
        st.stop()

    news_df = get_news_data()
    
    if news_df is None or news_df.empty:
        st.info("🔄 正在尝试获取最新财经数据，请刷新页面...")
        st.stop()

    # Session State 记录选中的新闻索引
    if 'selected_idx' not in st.session_state:
        st.session_state.selected_idx = 0

    # 手机端布局：先显示简讯列表
    st.subheader("📰 实时简讯 (点击下方新闻进行分析)")
    
    # 仅展示前 10 条，方便手机滑动
    options = news_df.head(10)['标题'].tolist()
    selected_title = st.selectbox("切换新闻内容：", options, index=st.session_state.selected_idx)
    
    # 更新索引
    current_idx = options.index(selected_title)
    st.session_state.selected_idx = current_idx
    current_news = news_df.iloc[current_idx]

    # 展示详情内容
    st.markdown("---")
    with st.container():
        st.markdown(f"### {current_news['标题']}")
        st.caption(f"🕒 {current_news['发布日期']} {current_news['发布时间']}")
        st.info(current_news['内容'])

    # AI 分析按钮
    if st.button("✨ 深度挖掘概念个股"):
        with st.spinner("AI 分析中..."):
            try:
                # 初始化智谱 GLM-4
                llm = ChatOpenAI(
                    api_key=api_key,
                    base_url="https://open.bigmodel.cn/api/paas/v4/",
                    model="glm-4-flash",
                    temperature=0.1
                )
                
                prompt = ChatPromptTemplate.from_messages([
                    ("system", "你是一位专业的证券分析师。请根据新闻，1.识别核心概念 2.挖掘3只A股相关龙头股并说明逻辑。输出格式要求：使用Markdown表格展示个股。"),
                    ("user", "新闻标题: {title}\n内容: {content}")
                ])
                
                chain = prompt | llm | StrOutputParser()
                result = chain.invoke({
                    "title": current_news['标题'],
                    "content": current_news['content'] if 'content' in current_news else current_news['内容']
                })
                
                st.success("✅ 分析完成")
                st.markdown(result)
                
            except Exception as e:
                st.error(f"分析失败: {str(e)}")

if __name__ == "__main__":
    app()
