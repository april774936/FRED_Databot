import os, requests, yfinance as yf
from datetime import datetime
from fredapi import Fred

def send_msg(msg):
    url = f"https://api.telegram.org/bot{os.environ.get('TELEGRAM_TOKEN')}/sendMessage"
    requests.post(url, json={"chat_id": os.environ.get('CHAT_ID'), "text": msg, "parse_mode": "HTML"})

def get_data(ticker_symbol, name, use_current_price):
    try:
        t_code = "^2Y" if "2년물" in name else ticker_symbol
        df = yf.Ticker(t_code).history(period="7d").dropna()
        
        if df.empty and "2년물" in name:
            df = yf.Ticker("^IRX").history(period="7d").dropna()

        if df.empty: return f"• <b>{name}</b>\n데이터 로드 실패 ⚠️\n\n"

        curr, prev = df.iloc[-1], df.iloc[-2]
        w_df = df.iloc[0] 
        
        # 핵심 로직: 23시(True)면 현재가(Open/Last), 17시 30분(False)이면 전일 종가(Close)
        # yfinance의 최신행(iloc[-1]) Close는 장중에는 현재가 역할을 합니다.
        price = curr['Close'] if use_current_price else prev['Close']
        
        # 전일 종가 기준일 때는 그 전날(prev)과 그 전전날(df.iloc[-3])을 비교하게 세팅
        if not use_current_price:
            base_price = df.iloc[-3]['Close']
            diff = price - base_price
            date = prev.name.strftime('%m/%d') # 전일 날짜 표시
        else:
            base_price = prev['Close']
            diff = price - base_price
            date = curr.name.strftime('%m/%d') # 오늘 날짜 표시
            
        w_diff = price - w_df['Close']
        emoji = "📈" if diff >= 0 else "📉"
        
        if "국채 금리" in name:
            res = f"{emoji} <b>{name}</b> - {date}\n"
            res += f"  현재: <b>{price:.2f}%</b> ({diff:+.2f}p)\n"
            res += f"  주간: {w_df['Close']:.2f}% ({w_diff:+.2f}p)\n\n"
        else:
            pct = (diff / base_price * 100) if base_price != 0 else 0
            res = f"{emoji} <b>{name}</b> - {date}\n"
            res += f"  • 가격: <b>{price:,.2f}</b> ({pct:+.2f}%, {diff:+.2f}p)\n"
            res += f"  • 주간: {w_df['Close']:,.2f} ({((price-w_df['Close'])/w_df['Close']*100):+.2f}%, {price-w_df['Close']:+.2f}p)\n\n"
        return res
    except: return f"• <b>{name}</b>\n로드 에러\n\n"

def main():
    now = datetime.now()
    # 한국 시간 기준 20시 이후(오후 11시 포함)면 현재가 모드(True), 그 전이면 종가 모드(False)
    # 서버 시간(UTC) 기준으로는 11시 이후면 현재가 모드입니다.
    # 안전하게 실행 시점의 '시' 정보를 기준으로 판단합니다.
    current_hour = now.hour 
    use_current = True if current_hour >= 11 or current_hour <= 4 else False

    fred = Fred(api_key=os.environ.get('FRED_API_KEY'))
    hy = fred.get_series('BAMLH0A0HYM2').dropna()
    hy_curr, hy_prev, hy_week = hy.iloc[-1], hy.iloc[-2], hy.iloc[-6]
    
    # 종가 모드일 때는 한 칸씩 뒤로 밀어서 계산
    target_hy = hy_curr if use_current else hy_prev
    prev_hy = hy_prev if use_current else hy.iloc[-3]
    
    hy_diff = target_hy - prev_hy
    hy_emoji = "📈" if hy_diff >= 0 else "📉"
    
    status_text = "🚀 실시간 현재가" if use_current else "🏁 전일 종가 기준"
    report = f"✨ <b>{status
