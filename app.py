import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="AI Market Analyst", layout="wide", page_icon="💹")

# Custom CSS for a sleek "Terminal" look
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# 2. Indicators Logic
def calculate_indicators(df):
    # Calculate 20-period SMA
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    
    # Calculate RSI (Relative Strength Index)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def get_recommendation(rsi, price, sma):
    if rsi < 35:
        return "🟢 STRONG BUY", "Asset is Oversold. Potential rebound likely."
    elif rsi > 65:
        return "🔴 STRONG SELL", "Asset is Overbought. Risk of price correction."
    elif price > sma:
        return "🟡 HOLD / BULLISH", "Price is trending above average. Stable growth."
    else:
        return "⚪ WAIT", "Market is neutral or showing weak momentum."

# 3. Sidebar
st.sidebar.title("📈 Command Center")
ticker = st.sidebar.text_input("Enter Ticker (e.g. AAPL, BTC-USD, RELIANCE.NS)", value="BTC-USD").upper()
period = st.sidebar.selectbox("History", ("5d", "1mo", "6mo", "1y", "5y"), index=1)
interval = st.sidebar.selectbox("Interval", ("15m", "1h", "1d"), index=1)

# 4. Data Fetching
@st.cache_data(ttl=60)
def fetch_data(t, p, i):
    data = yf.download(t, period=p, interval=i, auto_adjust=True, threads=False)
    return data

st.title("💹 AI-Driven Market Analyst")
st.caption(f"Analyzing {ticker} using RSI and Moving Average models.")

if ticker:
    try:
        df = fetch_data(ticker, period, interval)
        
        # Flatten columns if MultiIndex (fix for new yfinance versions)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        if not df.empty and len(df) > 20:
            df = calculate_indicators(df)
            last_row = df.iloc[-1]
            
            # 5. Dashboard Metrics
            col1, col2, col3, col4 = st.columns(4)
            price_now = last_row['Close']
            price_start = df['Close'].iloc[0]
            change = ((price_now - price_start) / price_start) * 100
            
            col1.metric("Current Price", f"{price_now:,.2f}")
            col2.metric("Period Change", f"{change:+.2f}%")
            col3.metric("RSI (14)", f"{last_row['RSI']:.1f}")
            col4.metric("SMA (20)", f"{last_row['SMA20']:,.2f}")

            # 6. Buy/Sell Analysis Section
            st.markdown("---")
            rec_signal, rec_desc = get_recommendation(last_row['RSI'], price_now, last_row['SMA20'])
            
            # Using a container for the call-to-action
            with st.container():
                st.subheader("Technical Strategy")
                c1, c2 = st.columns([1, 2])
                with c1:
                    if "BUY" in rec_signal: st.success(f"### {rec_signal}")
                    elif "SELL" in rec_signal: st.error(f"### {rec_signal}")
                    else: st.warning(f"### {rec_signal}")
                with c2:
                    st.info(f"**Analysis:** {rec_desc}")

            # 7. Enhanced Chart
            fig = go.Figure()
            # Candlesticks
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], 
                                         low=df['Low'], close=df['Close'], name="Market"))
            # SMA Line
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], name="Trend (SMA20)", 
                                     line=dict(color='#ff9900', width=1.5)))
            
            fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=500)
            st.plotly_chart(fig, use_container_width=True)

            # Disclaimer for portfolio
            st.caption("**Disclaimer:** This is a student project for portfolio purposes. Not financial advice.")

        else:
            st.error("Insufficient data. Try a longer 'History' or shorter 'Interval'.")
            
    except Exception as e:
        st.error(f"Error: {e}")
