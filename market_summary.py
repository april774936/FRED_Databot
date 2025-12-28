import os, requests, yfinance as yf
from datetime import datetime, timedelta
from fredapi import Fred

def send_telegram_msg(msg):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('CHAT_ID')
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})

def get_fred_data():
    try:
        fred_key = os.environ.get('FRED_API_KEY')
        if not fred_key: return "• FRED 데이터: API 키 누락\n\n"
        fred = Fred(api_key=fred_key)
        # BofA 하이일드 지수 옵션 조정 스프레드 (정크본드 지표)
        data = fred.get_series('BAMLH0A0HYM2')
        curr = data.iloc[-1]
        prev = data.iloc[-2]
        diff = curr - prev
        emoji = "⚠️" if diff > 0 else "✅"
        return f"<b>{emoji} 정크본드 스프레드(HY)</b>\n  └ 현재: {curr:.2f}% (변동 {diff:+.2f}p)\n\n"
    except:
        return "• FRED 데이터: 로드 실패\n\n"

def get_data(ticker_symbol, name, is_open_report, is_bond=False):
    try:
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period="3mo").dropna()
        if df.empty: return f"• <b>{name}</b>: 데이터 로드 실패\n\n"
        
        curr, prev = df.iloc[-1], df.iloc[-2]
        w_df = df.iloc[max(0, len(df)-6)]
        
        days = ['월', '화', '수', '목', '금', '토', '일']
        date_label = f"{curr.name.strftime('%m/%d')}({days[curr.name.weekday()]})"
        
        price = curr['Open'] if is_open_report else curr['Close']
        prev_close = prev['Close']
        diff = price - prev_close
        pct = (diff / prev_close) * 100
        
        if is_bond:
            emoji = "📈" if diff >= 0 else "📉"
            res = f"• <b>{name}</b> - {date_label}\n"
            res += f"  {emoji} {price:.2f} (전일대비 {diff:+.2f}p)\n\n"
        else:
            emoji = "🟢" if pct >= 0 else "🔴"
            res = f"{emoji} <b>{name}</b> - {date_label}\n"
            res += f"  • 가격: <b>{price:,.2f}</b> ({pct:+.2f}%, {diff:+.2f}p)\n"
            res += f"  • 주간변동: {((price-w_df['Close'])/w_df['Close']*100):+.2f}%\n\n"
        return res
    except:
        return f"• <b>{name}</b>: 로드 실패\n\n"

def main():
    now = datetime.now()
    is_open_report = True if now.hour >= 13 or now.hour <= 3 else False
    title_type = "🚀 장 시작 전 리포트" if is_open_report else "🏁 장 마감 리포트"
    
    report = f"✨ <b>{title_type}</b> ({now.strftime('%m/%d %H:%M')})\n"
    report += "━━━━━━━━━━━━━━━━━━\n\n"
    
    # 1. 주요 지수 및 달러 인덱스
    report += "📊 <b>핵심 시장 지표</b>\n\n"
    targets = [
        ("NQ=F", "나스닥100 선물"), ("ES=F", "S&P500 선물"), 
        ("DX-Y.NYB", "달러 인덱스"), ("GC=F", "금 선물"), ("BTC-USD", "비트코인")
    ]
    for t, n in targets:
        report += get_data(t, n, is_open_report)
        
    # 2. 국채 금리 (2년물, 10년물)
    report += "📉 <b>국채 수익률 현황</b>\n\n"
    report += get_data("^ZT=F", "미 2년물 국채 금리", is_open_report, is_bond=True)
    report += get_data("^TNX", "미 10년물 국채 금리", is_open_report, is_bond=True)
    
    # 3. FRED 데이터 (정크본드)
    report += "🔥 <b>위험 자산(FRED)</b>\n\n"
    report += get_fred_data()
    
    report += "━━━━━━━━━━━━━━━━━━"
    send_telegram_msg(report)

if __name__ == "__main__":
    main()
