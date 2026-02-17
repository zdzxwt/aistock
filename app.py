import streamlit as st
import requests
import pandas as pd

# ================= 配置部分 =================
st.set_page_config(
    page_title="AI 财经新闻概念挖掘终端",
    page_icon="📰",
    layout="wide"
)

# 从Secrets读取API配置
def get_secret(key, default=""):
    try:
        return st.secrets.get("secrets", {}).get(key, default) or st.secrets.get(key, default)
    except:
        return default

API_KEY = get_secret("API_KEY", "")
PROJECT_ID = get_secret("PROJECT_ID", "260215")
API_BASE = get_secret("API_BASE", "https://ark.cn-beijing.volces.com/api/v3")

# ================= API调用函数 =================
def call_doubao_api(prompt, model="Doubao-Seed-2.0-pro"):
    """调用火山引擎豆包API"""
    if not API_KEY:
        return "⚠️ 请在 Secrets 中配置 API_KEY"
    
    url = f"{API_BASE}/projects/{PROJECT_ID}/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        elif response.status_code == 404:
            return f"API 404错误: 请检查 PROJECT_ID ({PROJECT_ID}) 是否正确"
        elif response.status_code == 401:
            return "API 认证失败: 请检查 API_KEY 是否正确"
        else:
            return f"API错误: {response.status_code} - {response.text}"
    except Exception as e:
        return f"API调用失败: {str(e)}"

# ================= 数据获取层 =================
@st.cache_data(ttl=300)
def get_news_data():
    """获取财经新闻数据"""
    try:
        import akshare as ak
        news_df = ak.stock_info_global_cls()
        return news_df
    except Exception as e:
        return pd.DataFrame({
            '标题': ['AI芯片概念股大涨', '新能源汽车销量创新高', '半导体行业迎来新机遇'],
            '发布日期': ['2024-01-15', '2024-01-14', '2024-01-13'],
            '发布时间': ['10:30', '14:20', '09:15']
        })

# ================= 主程序 =================
def main():
    st.title("🤖 AI 新闻概念与个股挖掘")
    st.markdown("---")
    
    # 检查API配置
    if not API_KEY:
        st.error("⚠️ 请在 Streamlit Cloud 的 Secrets 中配置 API_KEY")
        st.info("""
        Secrets 配置格式：
        ```
        API_KEY = "9b9426f1-6905-4c9b-b549-647660a6b6fd"
        PROJECT_ID = "260215"
        API_BASE = "https://ark.cn-beijing.volces.com/api/v3"
        ```
        """)
        st.stop()
    
    with st.sidebar:
        st.header("⚙️ 配置")
        model_choice = st.selectbox(
            "选择模型",
            ["Doubao-Seed-2.0-pro", "doubao-pro-32k", "doubao-lite-32k"],
            index=0
        )
        st.caption(f"PROJECT_ID: {PROJECT_ID}")
        st.info("💡 基于火山引擎豆包大模型")
    
    with st.spinner("📥 正在加载新闻数据..."):
        news_df = get_news_data()
    
    if 'selected_idx' not in st.session_state:
        st.session_state.selected_idx = 0
    
    col_list, col_detail = st.columns([3, 7])
    
    with col_list:
        st.subheader("📰 实时新闻流")
        st.caption(f"共 {len(news_df)} 条新闻")
        
        for idx, row in news_df.iterrows():
            is_selected = idx == st.session_state.selected_idx
            prefix = "👉 " if is_selected else ""
            
            if st.button(
                f"{prefix}**{row['标题']}**\n\n`{row['发布日期']} {row['发布时间']}`",
                key=f"news_{idx}",
                use_container_width=True
            ):
                st.session_state.selected_idx = idx
                st.rerun()
    
    with col_detail:
        selected_news = news_df.iloc[st.session_state.selected_idx]
        
        st.subheader("📖 新闻详情与AI分析")
        
        with st.expander("📌 新闻基本信息", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**标题:** {selected_news['标题']}")
            with col2:
                st.markdown(f"**发布时间:** {selected_news['发布日期']} {selected_news['发布时间']}")
        
        st.markdown("### 🧠 AI智能分析")
        
        analysis_type = st.radio(
            "选择分析类型",
            ["概念解读", "相关个股", "市场影响", "投资建议"],
            horizontal=True
        )
        
        if st.button("🚀 开始分析", type="primary"):
            with st.spinner("🤔 AI正在分析中..."):
                if analysis_type == "概念解读":
                    prompt = f"请解读以下财经新闻的核心概念和意义：\n{selected_news['标题']}"
                elif analysis_type == "相关个股":
                    prompt = f"请分析以下新闻可能影响的相关A股股票代码和名称：\n{selected_news['标题']}"
                elif analysis_type == "市场影响":
                    prompt = f"请分析以下新闻对A股市场的影响：\n{selected_news['标题']}"
                else:
                    prompt = f"请给出以下新闻相关的投资建议：\n{selected_news['标题']}"
                
                analysis_result = call_doubao_api(prompt, model_choice)
                st.success(analysis_result)

if __name__ == "__main__":
    main()
