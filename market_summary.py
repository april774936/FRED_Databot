import os, requests, yfinance as yf
from datetime import datetime

def get_detailed_info(ticker_symbol, name):
    try:
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period="3mo").dropna()
        if len(df) < 21: return f"• {name}: 데이터 부족\n\n"

        # 실제 거래 데이터가 있는 마지막 두 날 추출
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 날짜 포맷 (예: 12/26(금))
        days = ['월', '화', '수', '목', '금', '토', '일']
        date_str = f"{curr.name.strftime('%m/%d')}({days[curr.name.weekday()]})"
        
        price = curr['Close']
        diff_p = price - prev['Close']
        daily_pct = (diff_p / prev['Close']) * 100
        
        # 주간/월간 비교
        w_df = df.iloc[-6]
        m_df = df.iloc[-21]
        w_diff, m_diff = price - w_df['Close'], price - m_df['Close']
        w_pct, m_pct = (w_diff/w_df['Close']*100), (m_diff/m_df['Close']*100)
        
        # 거래량 필터링 (선물 특성상 0이 많음)
        vol = curr['Volume']
        # 전일 거래량이 0이면 그 이전 거래일 탐색
        idx = -2
        while prev['Volume'] == 0 and abs(idx) < len(df):
            prev = df.iloc[idx]
            idx -= 1
        
        vol_pct = ((vol - prev['Volume']) / prev['Volume'] * 100) if prev['Volume'] > 0 else 0
        
        emoji = "🔴" if daily_pct < 0 else "🔵"
        
        res = f"{emoji} {name} - {date_str}\n"
        res += f"• {price:,.2f} (전일대비 {daily_pct:+.2f}%, {diff_p:+.0f}p)\n"
        res += f"• 주간({w_df.name.strftime('%m/%d')}): {w_pct:+.2f}%, {w_diff:+.0f}p\n"
        res += f"• 월간({m_df.name.strftime('%m/%d')}): {m_pct:+.2f}%, {m_diff:+.0f}p\n"
        res += f"• 거래량: {vol:,.0f} (전일대비 {vol_pct:+.2f}%)\n\n"
        return res
    except:
        return f"• {name}: 정보 로드 실패\n\n"

def get_bond_info(ticker_symbol, name):
    try:
        # 국채 금리는 데이터가 비는 경우가 많아 더 길게 가져옴
        df = yf.Ticker(ticker_symbol).history(period="3mo").dropna()
        curr, prev = df.iloc[-1], df.iloc[-2]
        w_df, m_df = df.iloc[-6], df.iloc[-21]
        
        days = ['월', '화', '수', '목', '금', '토', '일']
        date_str = f"{curr.name.strftime('%m/%d')}({days[curr.name.weekday()]})"
        
        c_val = curr['Close']
        res = f"• {name} - {date_str}\n"
        res += f"• {c_val:.2f} (전일대비 {c_val - prev['Close']:+.2f}p)\n"
        res += f"• {w_df['Close']:.2f} (주간 {c_val - w_df['Close']:+.2f}p)\n"
        res += f"• {m_df['Close']:.2f} (월간 {c_val - m_df['Close']:+.2f}p)\n\n"
        return res
    except:
        return f"• {name}: 정보 로드 실패\n\n"

def main():
    if datetime.now().weekday() in [0, 6]: return # 일, 월 아침 중단
    
    token, chat_id = os.environ.get('TELEGRAM_TOKEN'), os.environ.get('CHAT_ID')
    now_str = datetime.now().strftime('%m/%d %H:%M')
    
    msg = f"🏁 <b>시장 마감 리포트 ({now_str})</b>\n\n"
    msg += "[주요 종목 상세 분석]\n"
    
    # 지수 및 자산 리스트
    for t, n in [("NQ=F", "나스닥100 선물"), ("ES=F", "S&P500 선물"), ("YM=F", "다우 선물"), 
                 ("GC=F", "금 선물"), ("BTC-USD", "비트코인 현물")]:
        msg += get_detailed_info(t, n)
        
    msg += "📉 <b>채권 금리 (Point)</b>\n"
    # 2년물 금리 티커를 더 안정적인 ^ZT=F 또는 ZN=F와 병행 테스트 가능 (여기선 표준 선물)
    msg += get_bond_info("ZT=F", "미 2년물 국채 금리") 
    msg += get_bond_info("^TNX", "미 10년물 국채 금리")
    
    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                  json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})

if __name__ == "__main__":
    main()

