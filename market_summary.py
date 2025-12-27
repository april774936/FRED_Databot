import os, requests, yfinance as yf
from datetime import datetime

def get_detailed_info(ticker_symbol, name):
    try:
        ticker = yf.Ticker(ticker_symbol)
        # 충분한 데이터 확보를 위해 3개월치 로드
        df = ticker.history(period="3mo")
        if len(df) < 21: return f"• {name}: 데이터 부족\n\n"

        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 1. 날짜 및 현재가 정보
        curr_date = curr.name.strftime('%m월 %d일')
        price = curr['Close']
        daily_pct = ((price - prev['Close']) / prev['Close']) * 100
        
        # 2. 거래량 전일 대비 변동률
        vol_change = ((curr['Volume'] - prev['Volume']) / prev['Volume']) * 100 if prev['Volume'] > 0 else 0
        
        # 3. 주간/월간 날짜 및 가격 대비 변동
        # 주간 (5거래일 전)
        w_df = df.iloc[-6]
        w_date = w_df.name.strftime('%m월 %d일')
        w_price = w_df['Close']
        w_pct = ((price - w_price) / w_price) * 100
        
        # 월간 (20거래일 전)
        m_df = df.iloc[-21]
        m_date = m_df.name.strftime('%m월 %d일')
        m_price = m_df['Close']
        m_pct = ((price - m_price) / m_price) * 100
        
        emoji = "🔴" if daily_pct < 0 else "🔵"
        
        res = f"{emoji} <b>{name}</b>\n"
        res += f"• 현재가({curr_date}): {price:,.2f} (전일대비 {daily_pct:+.2f}%)\n"
        res += f"• 주간({w_date} {w_price:,.2f} 대비): {w_pct:+.2f}%\n"
        res += f"• 월간({m_date} {m_price:,.2f} 대비): {m_pct:+.2f}%\n"
        res += f"• 거래량: {curr['Volume']:,.0f} (전일대비 {vol_change:+.2f}%)\n\n"
        return res
    except Exception as e:
        return f"• {name}: 로드 실패\n\n"

def get_bond_info(ticker_symbol, name):
    try:
        data = yf.Ticker(ticker_symbol).history(period="2d")
        curr, prev = data['Close'].iloc[-1], data['Close'].iloc[-2]
        diff = curr - prev
        emoji = "🔺" if diff > 0 else "🔻"
        return f"{emoji} {name}: {curr:.3f}% (변동: {diff:+.3f})\n"
    except:
        return f"• {name}: 로드 실패\n"

def main():
    # 주말(일, 월 아침) 실행 방지
    if datetime.now().weekday() in [0, 6]: return
    
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('CHAT_ID')
    
    msg = f"🏁 <b>시장 마감 리포트 ({datetime.now().strftime('%m/%d')})</b>\n\n"
    
    # 1. 상세 종목 리스트 (선물 및 비트코인)
    detailed_tickers = [
        ("NQ=F", "나스닥100 선물"),
        ("ES=F", "S&P500 선물"),
        ("YM=F", "다우 선물"),
        ("GC=F", "금 선물"),
        ("BTC-USD", "비트코인 현물")
    ]
    
    msg += "[주요 종목 상세 분석]\n"
    for t, n in detailed_tickers:
        msg += get_detailed_info(t, n)
        
    # 2. 채권 금리 (증감값 위주)
    msg += "📉 <b>채권 금리 (Point)</b>\n"
    msg += get_bond_info("^ZT=F", "미 2년물 금리 선물")
    msg += get_bond_info("^TNX", "미 10년물 금리")
    
    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                  json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})

if __name__ == "__main__":
    main()
