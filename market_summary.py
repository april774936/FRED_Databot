import os, requests, yfinance as yf
from datetime import datetime

def send_telegram_msg(msg):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('CHAT_ID')
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})

def get_data(ticker_symbol, name, is_open_report, is_bond=False):
    backups = {"NQ=F": "QQQ", "ES=F": "SPY", "YM=F": "DIA", "GC=F": "GLD"}
    try:
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period="3mo").dropna()
        if df.empty and ticker_symbol in backups:
            df = yf.Ticker(backups[ticker_symbol]).history(period="3mo").dropna()
        
        if df.empty: return f"• <b>{name}</b>: 데이터 로드 실패 ⚠️\n\n"
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        w_df = df.iloc[max(0, len(df)-6)]
        
        days = ['월', '화', '수', '목', '금', '토', '일']
        date_label = f"{curr.name.strftime('%m/%d')}({days[curr.name.weekday()]})"
        
        # 장 시작 전 리포트면 '시가(Open)', 장 마감 리포트면 '종가(Close)' 사용
        price = curr['Open'] if is_open_report else curr['Close']
        prev_price = prev['Close']
        
        diff = price - prev_price
        pct = (diff / prev_price) * 100
        
        if is_bond:
            emoji = "📈" if diff >= 0 else "📉"
            res = f"• <b>{name}</b> - {date_label}\n"
            res += f"  {emoji} {price:.2f} (전일대비 {diff:+.2f}p)\n\n"
        else:
            emoji = "🟢" if pct >= 0 else "🔴"
            label = "현재가(시가)" if is_open_report else "마감가(종가)"
            res = f"{emoji} <b>{name}</b> - {date_label}\n"
            res += f"  • {label}: <b>{price:,.2f}</b> ({pct:+.2f}%, {diff:+.0f}p)\n"
            res += f"  • 주간변동: {((price-w_df['Close'])/w_df['Close']*100):+.2f}%\n"
            if not is_open_report: # 마감 리포트에만 거래량 포함
                res += f"  • 거래량: {curr['Volume']:,.0f}\n"
            res += "\n"
        return res
    except:
        return f"• <b>{name}</b>: 분석 오류 ❌\n\n"

def main():
    now = datetime.now()
    # 한국시간 기준 오후 4시 이후면 '장 시작 전' 리포트로 간주 (UTC 기준으로는 오전 시간)
    is_open_report = True if now.hour >= 13 or now.hour <= 3 else False
    
    title_type = "🚀 장 시작 전 리포트 (시가 기준)" if is_open_report else "🏁 장 마감 리포트 (종가 기준)"
    now_str = now.strftime('%Y/%m/%d %H:%M')
    
    report = f"✨ <b>{title_type}</b>\n({now_str})\n"
    report += "━━━━━━━━━━━━━━━━━━\n\n"
    
    targets = [("NQ=F", "나스닥100"), ("ES=F", "S&P500"), ("YM=F", "다우존스"), ("GC=F", "금 선물"), ("BTC-USD", "비트코인")]
    for t, n in targets:
        report += get_data(t, n, is_open_report)
        
    report += "📉 <b>주요 국채 금리</b>\n\n"
    report += get_data("^IRX", "미 단기 금리", is_open_report, is_bond=True)
    report += get_data("^TNX", "미 10년물 금리", is_open_report, is_bond=True)
    report += "━━━━━━━━━━━━━━━━━━"
    
    send_telegram_msg(report)

if __name__ == "__main__":
    main()
