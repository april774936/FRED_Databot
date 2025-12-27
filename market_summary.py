import os, requests, yfinance as yf
from datetime import datetime

def send_telegram_msg(msg):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('CHAT_ID')
    if not token or not chat_id:
        print("토큰이나 채팅 ID가 설정되지 않았습니다.")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}
    try:
        response = requests.post(url, json=payload)
        print(f"전송 결과: {response.status_code}")
    except Exception as e:
        print(f"전송 중 오류 발생: {e}")

def get_data(ticker_symbol, name, is_bond=False):
    try:
        df = yf.Ticker(ticker_symbol).history(period="3mo").dropna()
        if df.empty: return f"• {name}: 데이터 없음\n\n"
        
        # 실제 데이터가 존재하는 마지막 날(curr)과 그 전날(prev)
        curr, prev = df.iloc[-1], df.iloc[-2]
        w_df, m_df = df.iloc[max(0, len(df)-6)], df.iloc[max(0, len(df)-21)]
        
        days = ['월', '화', '수', '목', '금', '토', '일']
        date_label = f"{curr.name.strftime('%m/%d')}({days[curr.name.weekday()]})"
        c_val = curr['Close']
        
        if is_bond:
            res = f"• {name} - {date_label}\n"
            res += f"• {c_val:.2f} (전일대비 {c_val - prev['Close']:+.2f}p)\n"
            res += f"• {w_df['Close']:.2f} (주간 {c_val - w_df['Close']:+.2f}p)\n"
            res += f"• {m_df['Close']:.2f} (월간 {c_val - m_df['Close']:+.2f}p)\n\n"
        else:
            diff = c_val - prev['Close']
            pct = (diff / prev['Close']) * 100
            vol_pct = ((curr['Volume'] - prev['Volume']) / prev['Volume'] * 100) if prev['Volume'] > 0 else 0
            emoji = "🔴" if pct < 0 else "🔵"
            
            res = f"{emoji} {name} - {date_str}\n"
            res = f"{emoji} {name} - {date_label}\n"
            res += f"• {c_val:,.2f} (전일대비 {pct:+.2f}%, {diff:+.0f}p)\n"
            res += f"• 주간({w_df.name.strftime('%m/%d')}): {((c_val-w_df['Close'])/w_df['Close']*100):+.2f}%, {c_val-w_df['Close']:+.0f}p\n"
            res += f"• 월간({m_df.name.strftime('%m/%d')}): {((c_val-m_df['Close'])/m_df['Close']*100):+.2f}%, {c_val-m_df['Close']:+.0f}p\n"
            res += f"• 거래량: {curr['Volume']:,.0f} (전일대비 {vol_pct:+.2f}%)\n\n"
        return res
    except:
        return f"• {name}: 로드 실패\n\n"

def main():
    # 주말 실행 방지 로직 (필요 시 주석 처리 가능)
    # if datetime.now().weekday() in [0, 6]: return 

    now_str = datetime.now().strftime('%m/%d %H:%M')
    report = f"🏁 <b>시장 마감 리포트 ({now_str})</b>\n\n[주요 종목 상세 분석]\n"
    
    # 분석 종목
    for t, n in [("NQ=F", "나스닥100 선물"), ("ES=F", "S&P500 선물"), ("YM=F", "다우 선물"), ("GC=F", "금 선물"), ("BTC-USD", "비트코인 현물")]:
        report += get_data(t, n)
        
    report += "📉 <b>채권 금리 (Point)</b>\n"
    # 2년물 대용으로 안정적인 ^IRX(단기지수)와 ^TNX 사용
    report += get_data("^IRX", "미 단기 국채 금리", is_bond=True)
    report += get_data("^TNX", "미 10년물 국채 금리", is_bond=True)
    
    send_telegram_msg(report)

if __name__ == "__main__":
    main()
