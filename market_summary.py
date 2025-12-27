import os, requests, yfinance as yf
from datetime import datetime

def get_detailed_info(ticker_symbol, name):
    try:
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period="3mo")
        if len(df) < 21: return f"• {name}: 데이터 부족\n\n"

        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 날짜 및 요일 (예: 12/26(일))
        days = ['월', '화', '수', '목', '금', '토', '일']
        date_str = f"{curr.name.strftime('%m/%d')}({days[curr.name.weekday()]})"
        
        price = curr['Close']
        diff_p = price - prev['Close']
        daily_pct = (diff_p / prev['Close']) * 100
        
        # 주간(5거래일 전), 월간(20거래일 전) 비교
        w_df = df.iloc[-6]
        w_date = w_df.name.strftime('%m/%d')
        w_diff = price - w_df['Close']
        w_pct = (w_diff / w_df['Close']) * 100
        
        m_df = df.iloc[-21]
        m_date = m_df.name.strftime('%m/%d')
        m_diff = price - m_df['Close']
        m_pct = (m_diff / m_df['Close']) * 100
        
        # 거래량 변동 (0일 경우 처리)
        vol = curr['Volume']
        prev_vol = prev['Volume']
        vol_pct = ((vol - prev_vol) / prev_vol * 100) if prev_vol > 0 else 0
        
        emoji = "🔴" if daily_pct < 0 else "🔵"
        
        res = f"{emoji} {name} - {date_str}\n"
        res += f"• {price:,.2f} (전일대비 {daily_pct:+.2f}%, {diff_p:+.0f}p)\n"
        res += f"• 주간({w_date}): {w_pct:+.2f}%, {w_diff:+.0f}p\n"
        res += f"• 월간({m_date}): {m_pct:+.2f}%, {m_diff:+.0f}p\n"
        res += f"• 거래량: {vol:,.0f} (전일대비 {vol_pct:+.2f}%)\n\n"
        return res
    except:
        return f"• {name}: 정보 로드 실패\n\n"

def get_bond_info(ticker_symbol, name):
    try:
        df = yf.Ticker(ticker_symbol).history(period="3mo")
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        w_df = df.iloc[-6]
        m_df = df.iloc[-21]
        
        days = ['월', '화', '수', '목', '금', '토', '일']
        date_str = f"{curr.name.strftime('%m/%d')}({days[curr.name.weekday()]})"
        
        c_val = curr['Close']
        d_diff = c_val - prev['Close']
        w_diff = c_val - w_df['Close']
        m_diff = c_val - m_df['Close']
        
        res = f"• {name} - {date_str}\n"
        res += f"• {c_val:.2f} (전일대비 {d_diff:+.2f}p)\n"
        res += f"• {w_df['Close']:.2f} (주간 {w_diff:+.2f}p)\n"
        res += f"• {m_df['Close']:.2f} (월간 {m_diff:+.2f}p)\n\n"
        return res
    except:
        return f"• {name}: 정보 로드 실패\n\n"

def main():
    if datetime.now().weekday() in [0, 6]: return # 일, 월요일 아침 제외
    
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('CHAT_ID')
    now_str = datetime.now().strftime('%m/%d %H:%M')
    
    msg = f"🏁 <b>시장 마감 리포트 ({now_str})</b>\n\n"
    msg += "[주요 종목 상세 분석]\n"
    
    for t, n in [("NQ=F", "나스닥100 선물"), ("ES=F", "S&P500 선물"), ("YM=F", "다우 선물"), 
                 ("GC=F", "금 선물"), ("BTC-USD", "비트코인 현물")]:
        msg += get_detailed_info(t, n)
        
    msg += "📉 <b>채권 금리 (Point)</b>\n"
    msg += get_bond_info("^ZT=F", "미 2년물 국채 금리")
    msg += get_bond_info("^TNX", "미 10년물 국채 금리")
    
    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                  json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})

if __name__ == "__main__":
    main()
