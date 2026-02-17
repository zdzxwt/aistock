import streamlit as st
from openai import OpenAI
import pandas as pd

# ================= 配置部分 =================
st.set_page_config(
    page_title="AI 财经新闻概念挖掘终端",
    page_icon="📰",
    layout="wide"
)

# 直接读取Secrets
try:
    API_KEY = st.secrets["API_KEY"]
except:
    API_KEY = ""

# 初始化客户端
@st.cache_resource
def get_client():
    if not API_KEY:
        return None
    return OpenAI(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key=API_KEY,
    )

# ================= API调用函数 =================
def call_doubao_api(prompt, model="doubao-seed-2-0-pro-260215"):
    if not API_KEY:
        return "⚠️ 未配置API_KEY"
    
    client = get_client()
    if not client:
        return "⚠️ 客户端未初始化"
    
    try:
        response = client.responses.create(
            model=model,
            input=[{"role": "user", "content": [{"type": "input_text", "text": prompt}]}]
        )
        
        # 调试：打印完整响应
        print("Response:", response)
        
        # 检查响应结构
        if response.output is None or len(response.output) == 0:
            return f"响应为空: {response}"
        
        if hasattr(response.output[0], 'content') and response.output[0].content:
            return response.output[0].content[0].text
        
        return str(response)
        
    except Exception as e:
        import traceback
        return f"错误: {str(e)}\n{traceback.format_exc()}"

# ================= 数据获取 =================
@st.cache_data(ttl=300)
def get_news_data():
    try:
        import akshare as ak
        return ak.stock_info_global_cls()
    except:
        return pd.DataFrame({
            '标题': ['AI芯片概念股大涨', '新能源汽车销量创新高', '半导体行业迎来新机遇'],
            '发布日期': ['2024-01-15', '2024-01-14', '2024-01-13'],
            '发布时间': ['10:30', '14:20', '09:15']
        })

# ================= 主程序 =================
def main():
    st.title("🤖 AI 新闻概念与个股挖掘")
    
    st.sidebar.write("配置状态:")
    st.sidebar.write(f"API_KEY: {'✅' if API_KEY else '❌'}")
    
    if not API_KEY:
        st.error("请在Secrets配置API_KEY")
        st.code("API_KEY = 9b9426f1-6905-4c9b-b549-647660a6b6fd")
        st.stop()
    
    with st.sidebar:
        model = st.selectbox("模型", ["doubao-seed-2-0-pro-260215"], index=0)
        if st.button("测试API"):
            with st.spinner("测试中..."):
                result = call_doubao_api("你好", model)
                st.text_area("结果", result, height=200)
    
    news_df = get_news_data()
    
    if 'idx' not in st.session_state:
        st.session_state.idx = 0
    
    c1, c2 = st.columns([3, 7])
    with c1:
        st.subheader("📰 新闻")
        for i, row in news_df.iterrows():
            if st.button(f"{'👉 ' if i==st.session_state.idx else ''}{row['标题']}", key=f"b{i}", use_container_width=True):
                st.session_state.idx = i
                st.rerun()
    
    with c2:
        sel = news_df.iloc[st.session_state.idx]
        st.subheader("📖 详情")
        st.write(f"**{sel['标题']}**")
        st.caption(f"{sel['发布日期']} {sel['发布时间']}")
        
        typ = st.radio("分析类型", ["概念解读", "相关个股", "市场影响", "投资建议"], horizontal=True)
        
        if st.button("🚀 开始分析", type="primary"):
            prompts = {
                "概念解读": f"解读: {sel['标题']}",
                "相关个股": f"分析相关股票: {sel['标题']}",
                "市场影响": f"分析市场: {sel['标题']}",
                "投资建议": f"投资建议: {sel['标题']}"
            }
            with st.spinner("..."):
                st.success(call_doubao_api(prompts[typ], model))

if __name__ == "__main__":
    main()
