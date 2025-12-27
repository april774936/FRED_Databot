import os, requests, yfinance as yf
from datetime import datetime

def get_latest_valid_data(df, column='Close'):
    """값이 존재하고 0이 아닌 최신 인덱스들을 찾아 반환"""
    valid_df = df[df[column] > 0].dropna()
    if len(valid_df) < 21:
        return None, None, None, None
    return valid_df.iloc[-1], valid_df.iloc[-2], valid_df.iloc[-6], valid_df.iloc[-21]

def get_detailed_info(ticker_symbol, name):
    try:
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period="3mo")
        
        # 1. 실제 거래 데이터가 있는 날들 추출 (거래량/가격 0 방어)
        curr, prev, w_df, m_df = get_latest_valid_data(df, 'Volume' if 'F' in ticker_symbol else 'Close')
        
        if curr is None: return f"• {name}: 데이터 분석 불가\n\n"

        # 날짜 포맷
        days = ['월', '화', '수', '목', '금', '토', '일']
        date_str = f"{curr.name.strftime('%m/%d')}({days[curr.name.weekday()]})"
        
        price = curr['Close']
        diff_p = price - prev['Close']
        daily_pct = (diff_p / prev['Close']) * 100
        
        # 주간/월간 변동
        w_diff, m_diff = price - w_df['Close'], price - m_df['Close']
        w_pct, m_pct = (w_diff/w_df['Close']*100), (m_diff/m_df['Close']*100)
        
        # 거래량 변동 (실제 값이 있는 전거래일과 비교)
        vol = curr['Volume']
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
        # 국채 금리는 종가(Close) 기준으로 유효 데이터 추출
        df = yf.Ticker(ticker_symbol).history(period="3mo")
        curr, prev, w_df, m_df = get_latest_valid_data(df, 'Close')
        
        if curr is None: return f"• {name}: 정보 로드 실패\n\n"
        
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
    if datetime.now().weekday() in [0, 6]: return 
    
    token, chat_id = os.environ.get('TELEGRAM_TOKEN'), os.environ.get('CHAT_ID')
    now_str = datetime.now().strftime('%m/%d %H:%M')
    
    msg = f"🏁 <b>시장 마감 리포트 ({now_str})</b>\n\n"
    msg += "[주요 종목 상세 분석]\n"
    
    # 상세 지표 리스트
    for t, n in [("NQ=F", "나스닥100 선물"), ("ES=F", "S&P500 선물"), ("YM=F", "다우 선물"), 
                 ("GC=F", "금 선물"), ("BTC-USD", "비트코인 현물")]:
        msg += get_detailed_info(t, n)
        
    msg += "📉 <b>채권 금리 (Point)</b>\n"
    # ^IRX(13주), ^FVX(5년), ^TNX(10년), ^TYX(30년) 등 수익률 지수 활용
    # 2년물은 수익률 지표인 ^ZTY0 또는 관련 지수로 대체 (수익률 데이터 중심)
    msg += get_bond_info("^ZTY0", "미 2년물 국채 금리") 
    msg += get_bond_info("^TNX", "미 10년물 국채 금리")
    
    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                  json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})

if __name__ == "__main__":
    main()
