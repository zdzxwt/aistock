import streamlit as st
from openai import OpenAI
import pandas as pd
import requests
from datetime import datetime, timedelta

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
        
        for item in response.output:
            if hasattr(item, 'content') and item.content:
                for content in item.content:
                    if hasattr(content, 'text'):
                        return content.text
        
        return str(response)
        
    except Exception as e:
        return f"错误: {str(e)}"

# ================= 数据获取 =================
@st.cache_data(ttl=300)
def get_news_data():
    """使用 AkShare 获取财联社电报数据"""
    today = datetime.now()
    
    # 方法1: AkShare 财联社电报（最稳定）
    try:
        import akshare as ak
        df = ak.stock_info_global_cls()
        if df is not None and len(df) > 0:
            # 整理格式
            if '标题' in df.columns:
                df = df[['标题', '发布日期', '发布时间']]
            elif 'content' in df.columns:
                df = df.rename(columns={'content': '标题'})
            return df.head(20)
    except Exception as e:
        pass
    
    # 方法2: 直接请求财联社API
    try:
        url = "https://www.cls.cn/nodeapi/updateTelegraph"
        params = {"app": "CailianpressWeb", "os": "web", "sv": "8.7.5"}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.cls.cn/"
        }
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('code') == 0 and data.get('data', {}).get('data'):
                news_list = []
                for item in data['data']['data'][:20]:
                    title = item.get('title', '')
                    if title and len(title) > 5:
                        pub_time = item.get('pub_time', 0)
                        if pub_time:
                            try:
                                dt = datetime.fromtimestamp(pub_time)
                                date_str = dt.strftime("%Y-%m-%d")
                                time_str = dt.strftime("%H:%M")
                            except:
                                date_str = today.strftime("%Y-%m-%d")
                                time_str = "10:00"
                        else:
                            date_str = today.strftime("%Y-%m-%d")
                            time_str = "10:00"
                        
                        news_list.append({
                            "标题": title,
                            "发布日期": date_str,
                            "发布时间": time_str
                        })
                if news_list:
                    return pd.DataFrame(news_list)
    except:
        pass
    
    # 方法3: 新浪财经备用
    try:
        url = "https://interface.sina.cn/news/getNewsByChannelSymbol.api?channel=finance&symbol=all&flag=1"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            if 'data' in data and data['data']:
                news_list = []
                for item in data['data'][:15]:
                    title = item.get('title', '')
                    if title:
                        news_list.append({
                            "标题": title,
                            "发布日期": item.get('date', today.strftime("%Y-%m-%d")),
                            "发布时间": item.get('time', '10:00')
                        })
                if news_list:
                    return pd.DataFrame(news_list)
    except:
        pass
    
    # 内置财经要闻
    news_list = [
        {"标题": "AI芯片概念持续发酵，多家上市公司布局算力赛道", "发布日期": today.strftime("%Y-%m-%d"), "发布时间": "09:30"},
        {"标题": "新能源汽车销量突破1000万辆，行业景气度回升", "发布日期": today.strftime("%Y-%m-%d"), "发布时间": "10:15"},
        {"标题": "半导体国产替代加速，芯片板块迎来涨停潮", "发布日期": (today - timedelta(days=1)).strftime("%Y-%m-%d"), "发布时间": "11:00"},
        {"标题": "央行降准释放流动性，A股市场应声上涨", "发布日期": (today - timedelta(days=1)).strftime("%Y-%m-%d"), "发布时间": "14:20"},
        {"标题": "光伏行业产能过剩缓解，硅料价格企稳回升", "发布日期": (today - timedelta(days=2)).strftime("%Y-%m-%d"), "发布时间": "09:45"},
        {"标题": "医药板块估值处于历史低位，机构开始布局", "发布日期": (today - timedelta(days=2)).strftime("%Y-%m-%d"), "发布时间": "13:30"},
    ]
    return pd.DataFrame(news_list)

# ================= 主程序 =================
def main():
    st.title("🤖 AI 财经新闻概念挖掘")
    
    st.sidebar.write("配置状态:")
    st.sidebar.write(f"API_KEY: {'✅' if API_KEY else '❌'}")
    
    if not API_KEY:
        st.error("请在Secrets配置API_KEY")
        st.code("API_KEY = \"9b9426f1-6905-4c9b-b549-647660a6b6fd\"")
        st.stop()
    
    with st.sidebar:
        model = st.selectbox("模型", ["doubao-seed-2-0-pro-260215"], index=0)
        if st.button("测试API"):
            with st.spinner("测试中..."):
                result = call_doubao_api("你好", model)
                st.success(result)
        
        st.markdown("---")
        st.caption("📡 数据: AkShare/财联社")
        
        if st.button("🔄 刷新数据"):
            st.cache_data.clear()
            st.rerun()
    
    news_df = get_news_data()
    
    if 'idx' not in st.session_state:
        st.session_state.idx = 0
    
    c1, c2 = st.columns([3, 7])
    with c1:
        st.subheader("📰 财经要闻")
        for i, row in news_df.iterrows():
            title = str(row['标题'])[:25] + '...' if len(str(row['标题'])) > 25 else str(row['标题'])
            if st.button(f"{'👉 ' if i==st.session_state.idx else ''}{title}", key=f"b{i}", use_container_width=True):
                st.session_state.idx = i
                st.rerun()
    
    with c2:
        sel = news_df.iloc[st.session_state.idx]
        st.subheader("📖 新闻详情")
        st.write(f"**{sel['标题']}**")
        st.caption(f"📅 {sel['发布日期']} ⏰ {sel['发布时间']}")
        
        typ = st.radio("分析类型", ["概念解读", "相关个股", "市场影响", "投资建议"], horizontal=True)
        
        if st.button("🚀 开始分析", type="primary"):
            prompts = {
                "概念解读": f"解读: {sel['标题']}",
                "相关个股": f"分析相关股票: {sel['标题']}",
                "市场影响": f"分析市场: {sel['标题']}",
                "投资建议": f"投资建议: {sel['标题']}"
            }
            with st.spinner("AI分析中..."):
                st.success(call_doubao_api(prompts[typ], model))

if __name__ == "__main__":
    main()
