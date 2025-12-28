import os, requests, yfinance as yf
from datetime import datetime
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
        if not fred_key: return "• ⚠️ <b>FRED API 키를 등록해주세요</b>\n\n"
        fred = Fred(api_key=fred_key)
        # BofA 하이일드 지수 옵션 조정 스프레드
        data = fred.get_series('BAMLH0A0HYM2')
        curr, prev = data.iloc[-1], data.iloc[-2]
        diff = curr - prev
        status = "위험선호" if diff < 0 else "위험회피"
        return f"🔥 <b>정크본드 스프레드</b>: {curr:.2f}% ({diff:+.2f}p)\n  └ 현재 시장은 <b>{status}</b> 분위기입니다.\n\n"
    except:
        return "• FRED 데이터: 로드 일시 실패\n\n"

def get_data(ticker_symbol, name, is_open_report, is_bond=False):
    try:
        # 데이터 안정성을 위해 시계열을 넉넉히 가져옴
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period="1mo").dropna()
        if df.empty: return f"• {name}: 데이터 로드 실패\n\n"
        
        curr, prev = df.iloc[-1], df.iloc[-2]
        w_df = df.iloc[max(0, len(df)-6)]
        days = ['월', '화', '수', '목', '금', '토', '일']
        date_label = f"{curr.name.strftime('%m/%d')}({days[curr.name.weekday()]})"
        
        price = curr['Open'] if is_open_report else curr['Close']
        diff = price - prev['Close']
        pct = (diff / prev['Close']) * 100
        
        if is_bond:
            emoji = "📈" if diff >= 0 else "📉"
            return f"• <b>{name}</b> - {date_label}\n  {emoji} {price:.2f} (전일대비 {diff:+.2f}p)\n\n"
        else:
            emoji = "🟢" if pct >= 0 else "🔴"
            return f"{emoji} <b>{name}</b> - {date_label}\n  • 가격: <b>{price:,.2f}</b> ({pct:+.2f}%, {diff:+.2f}p)\n  • 주간: {((price-w_df['Close'])/w_df['Close']*100):+.2f}%\n\n"
    except:
        return f"• {name}: 분석 오류\n\n"

def main():
    now = datetime.now()
    # 오후 4시 ~ 오전 4시 사이 실행 시 '장 시작 전'으로 표시
    is_open_report = True if now.hour >= 16 or now.hour <= 4 else False
    title = "🚀 장 시작 전 리포트" if is_open_report else "🏁 장 마감 리포트"
    
    report = f"✨ <b>{title}</b> ({now.strftime('%m/%d %H:%M')})\n"
    report += "━━━━━━━━━━━━━━━━━━\n\n"
    
    report += "📊 <b>핵심 시장 지표</b>\n\n"
    # 달러 인덱스 티커 보정 (DX-Y.NYB)
    for t, n in [("NQ=F", "나스닥100 선물"), ("ES=F", "S&P500 선물"), ("DX-Y.NYB", "달러 인덱스"), ("GC=F", "금 선물"), ("BTC-USD", "비트코인")]:
        report += get_data(t, n, is_open_report)
        
    report += "📉 <b>국채 수익률 (Yield)</b>\n\n"
    # 2년물은 선물 티커(^ZT=F) 대신 지수 티커(^IRX:단기, ^FVX:5년물) 혹은 ^TNX를 기준으로 보정
    report += get_data("^IRX", "미 단기 국채 금리", is_open_report, is_bond=True)
    report += get_data("^TNX", "미 10년물 국채 금리", is_open_report, is_bond=True)
    
    report += "🛡️ <b>신용 위험 지표</b>\n\n"
    report += get_fred_data()
    
    report += "━━━━━━━━━━━━━━━━━━"
    send_telegram_msg(report)

if __name__ == "__main__":
    main()
