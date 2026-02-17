import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime

# ================= 配置部分 =================
st.set_page_config(
    page_title="AI 财经新闻概念挖掘终端",
    page_icon="📰",
    layout="wide"
)

# 火山引擎API配置
API_KEY = "9b9426f1-6905-4c9b-b549-647660a6b6fd"
API_BASE = "https://ark.cn-beijing.volces.com/api/v3"
PROJECT_ID = "2120566042"

# ================= API调用函数 =================
def call_doubao_api(prompt, model="doubao-pro-32k"):
    """调用火山引擎豆包API"""
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
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
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
        st.error(f"获取数据失败: {str(e)}")
        # 返回示例数据
        return pd.DataFrame({
            '标题': ['AI芯片概念股大涨', '新能源汽车销量创新高', '半导体行业迎来新机遇'],
            '发布日期': ['2024-01-15', '2024-01-14', '2024-01-13'],
            '发布时间': ['10:30', '14:20', '09:15']
        })

# ================= 主程序 =================
def main():
    st.title("🤖 AI 新闻概念与个股挖掘")
    st.markdown("---")
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 配置")
        model_choice = st.selectbox(
            "选择模型",
            ["doubao-pro-32k", "doubao-pro-4k"],
            index=0
        )
        st.info("💡 基于火山引擎豆包大模型")
    
    # 加载数据
    with st.spinner("📥 正在加载新闻数据..."):
        news_df = get_news_data()
    
    # 初始化 Session State
    if 'selected_idx' not in st.session_state:
        st.session_state.selected_idx = 0
    
    # 布局：左侧新闻列表，右侧详情与分析
    col_list, col_detail = st.columns([3, 7])
    
    with col_list:
        st.subheader("📰 实时新闻流")
        st.caption(f"共 {len(news_df)} 条新闻")
        
        # 显示新闻列表
        for idx, row in news_df.iterrows():
            # 简单的卡片样式
            with st.container():
                # 高亮选中项
                border_color = "#2563eb" if idx == st.session_state.selected_idx else "#e2e8f0"
                
                # 点击事件
                if st.button(
                    f"**{row['标题']}**\n\n`{row['发布日期']} {row['发布时间']}`",
                    key=f"news_{idx}",
                    use_container_width=True,
                    help="点击查看分析"
                ):
                    st.session_state.selected_idx = idx
                    st.rerun()
                
                st.markdown(f"""
                <style>
                .stButton > button {{
                    border-left: 4px solid {border_color};
                }}
                </style>
                """, unsafe_allow_html=True)
    
    with col_detail:
        # 获取选中的新闻
        selected_news = news_df.iloc[st.session_state.selected_idx]
        
        st.subheader("📖 新闻详情与AI分析")
        
        # 显示新闻基本信息
        with st.expander("📌 新闻基本信息", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**标题:** {selected_news['标题']}")
            with col2:
                st.markdown(f"**发布时间:** {selected_news['发布日期']} {selected_news['发布时间']}")
        
        # AI分析区域
        st.markdown("### 🧠 AI智能分析")
        
        # 分析选项
        analysis_type = st.radio(
            "选择分析类型",
            ["概念解读", "相关个股", "市场影响", "投资建议"],
            horizontal=True
        )
        
        if st.button("🚀 开始分析", type="primary"):
            with st.spinner("🤔 AI正在分析中..."):
                # 构建分析提示词
                if analysis_type == "概念解读":
                    prompt = f"请解读以下财经新闻的核心概念和意义：\n{selected_news['标题']}"
                elif analysis_type == "相关个股":
                    prompt = f"请分析以下新闻可能影响的相关A股股票代码和名称：\n{selected_news['标题']}"
                elif analysis_type == "市场影响":
                    prompt = f"请分析以下新闻对A股市场的影响：\n{selected_news['标题']}"
                else:
                    prompt = f"请给出以下新闻相关的投资建议：\n{selected_news['标题']}"
                
                # 调用API
                analysis_result = call_doubao_api(prompt, model_choice)
                
                # 显示结果
                st.success(analysis_result)
        
        # 历史分析记录
        if 'analysis_history' not in st.session_state:
            st.session_state.analysis_history = []
        
        with st.expander("📜 分析历史"):
            if st.session_state.analysis_history:
                for i, item in enumerate(st.session_state.analysis_history):
                    st.markdown(f"**{i+1}. {item['type']}**: {item['result'][:100]}...")
            else:
                st.info("暂无分析历史")

if __name__ == "__main__":
    main()
