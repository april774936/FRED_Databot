import os, requests, yfinance as yf
from datetime import datetime

def send_telegram_msg(msg):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('CHAT_ID')
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})

def get_data(ticker_symbol, name, is_bond=False):
    backups = {"NQ=F": "QQQ", "ES=F": "SPY", "YM=F": "DIA", "GC=F": "GLD"}
    try:
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period="3mo").dropna()
        
        if df.empty and ticker_symbol in backups:
            ticker = yf.Ticker(backups[ticker_symbol])
            df = ticker.history(period="3mo").dropna()
        
        if df.empty: return f"• <b>{name}</b>: 데이터 로드 실패 ⚠️\n\n"
        
        curr, prev = df.iloc[-1], df.iloc[-2]
        w_df, m_df = df.iloc[max(0, len(df)-6)], df.iloc[max(0, len(df)-21)]
        
        days = ['월', '화', '수', '목', '금', '토', '일']
        date_label = f"{curr.name.strftime('%m/%d')}({days[curr.name.weekday()]})"
        c_val = curr['Close']
        
        if is_bond:
            diff = c_val - prev['Close']
            emoji = "📈" if diff >= 0 else "📉"
            res = f"• <b>{name}</b> - {date_label}\n"
            res += f"  {emoji} {c_val:.2f} (전일대비 {diff:+.2f}p)\n"
            res += f"  └ 주간: {w_df['Close']:.2f} (변동 {c_val - w_df['Close']:+.2f}p)\n"
            res += f"  └ 월간: {m_df['Close']:.2f} (변동 {c_val - m_df['Close']:+.2f}p)\n\n"
        else:
            diff = c_val - prev['Close']
            pct = (diff / prev['Close']) * 100
            vol_pct = ((curr['Volume'] - prev['Volume']) / prev['Volume'] * 100) if prev['Volume'] > 0 else 0
            
            # 미국식 색상 (상승: 🟢, 하락: 🔴)
            emoji = "🟢" if pct >= 0 else "🔴"
            
            res = f"{emoji} <b>{name}</b> - {date_label}\n"
            res += f"  • 현재가: <b>{c_val:,.2f}</b> ({pct:+.2f}%, {diff:+.0f}p)\n"
            res += f"  • 주간({w_df.name.strftime('%m/%d')}): {((c_val-w_df['Close'])/w_df['Close']*100):+.2f}%\n"
            res += f"  • 월간({m_df.name.strftime('%m/%d')}): {((c_val-m_df['Close'])/m_df['Close']*100):+.2f}%\n"
            res += f"  • 거래량: {curr['Volume']:,.0f} ({vol_pct:+.2f}%)\n\n"
        return res
    except:
        return f"• <b>{name}</b>: 분석 중 오류 발생 ❌\n\n"

def main():
    now_str = datetime.now().strftime('%Y/%m/%d %H:%M')
    report = f"✨ <b>시장 마감 리포트</b> ({now_str})\n"
    report += "━━━━━━━━━━━━━━━━━━\n\n"
    
    report += "📊 <b>주요 종목 상세 분석</b>\n\n"
    targets = [("NQ=F", "나스닥100 선물"), ("ES=F", "S&P500 선물"), 
               ("YM=F", "다우 선물"), ("GC=F", "금 선물"), ("BTC-USD", "비트코인 현물")]
    
    for t, n in targets:
        report += get_data(t, n)
        
    report += "━━━━━━━━━━━━━━━━━━\n\n"
    report += "📉 <b>국채 금리 현황 (Point)</b>\n\n"
    report += get_data("^IRX", "미 단기 국채 금리", is_bond=True)
    report += get_data("^TNX", "미 10년물 국채 금리", is_bond=True)
    
    report += "━━━━━━━━━━━━━━━━━━"
    
    send_telegram_msg(report)

if __name__ == "__main__":
    main()
