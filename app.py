import streamlit as st
import requests
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
    
try:
    PROJECT_ID = st.secrets["PROJECT_ID"]
except:
    PROJECT_ID = "260215"

# ================= API调用函数 =================
def call_doubao_api(prompt, model_prefix="doubao-seed-2-0-pro"):
    if not API_KEY:
        return "⚠️ 未配置API_KEY"
    
    url = "https://ark.cn-beijing.volces.com/api/v3/responses"
    model = f"{model_prefix}-{PROJECT_ID}"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "input": [{"role": "user", "content": [{"type": "input_text", "text": prompt}]}]
    }
    
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        if resp.status_code == 200:
            result = resp.json()
            if 'output' in result and result['output']:
                return result['output'][0]['content'][0]['text']
            return str(result)
        return f"错误{resp.status_code}: {resp.text}"
    except Exception as e:
        return f"失败: {str(e)}"

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
    
    # 调试信息
    st.sidebar.write("配置状态:")
    st.sidebar.write(f"API_KEY: {'✅已配置' if API_KEY else '❌未配置'}")
    st.sidebar.write(f"PROJECT_ID: {PROJECT_ID}")
    
    if not API_KEY:
        st.error("请在Secrets中配置API_KEY")
        st.code("API_KEY = 9b9426f1-6905-4c9b-b549-647660a6b6fd\nPROJECT_ID = 260215")
        st.stop()
    
    with st.sidebar:
        model = st.selectbox("模型", ["doubao-seed-2-0-pro", "doubao-pro-32k"], index=0)
        if st.button("测试API"):
            st.write(call_doubao_api("你好", model))
    
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
