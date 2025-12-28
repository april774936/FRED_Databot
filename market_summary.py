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
        if not fred_key: return "• FRED API 설정 필요\n\n"
        fred = Fred(api_key=fred_key)
        data = fred.get_series('BAMLH0A0HYM2')
        curr, prev = data.iloc[-1], data.iloc[-2]
        diff = curr - prev
        status = "🟢 안정" if diff < 0 else "🔴 주의"
        return f"🛡️ <b>정크본드 스프레드</b>\n  └ 수치: <b>{curr:.2f}%</b> ({diff:+.2f}p) [{status}]\n\n"
    except:
        return "• FRED 데이터 로드 일시 실패\n\n"

def get_data(ticker_symbol, name, is_open_report, is_bond=False):
    try:
        # 2년물의 경우 선물 가격(104.xx)이 아닌 수익률(4.xx)을 가져오기 위한 티커 우선순위 설정
        if "2년물" in name:
            ticker_list = ["^2Y", "^IRX"] # ^2Y가 실패하면 단기물로 대체
        else:
            ticker_list = [ticker_symbol]

        df = None
        for t in ticker_list:
            df = yf.Ticker(t).history(period="1mo").dropna()
            if not df.empty: break
            
        if df is None or df.empty: return f"• <b>{name}</b>: 로드 실패\n\n"
        
        curr, prev = df.iloc[-1], df.iloc[-2]
        w_df = df.iloc[max(0, len(df)-6)]
        date_label = f"{curr.name.strftime('%m/%d')}({['월','화','수','목','금','토','일'][curr.name.weekday()]})"
        
        price = curr['Open'] if is_open_report else curr['Close']
        diff = price - prev['Close']
        
        if is_bond:
            # 2년물 가격이 100 이상으로 들어오는 경우를 대비한 방어 로직 (금리 지표만 해당)
            if price > 50: # 수익률이 50%일 리는 없으므로 이는 가격 데이터임
                return f"• <b>{name}</b>: 데이터 보정 중... ⏳\n\n"
                
            emoji = "📈" if diff >= 0 else "📉"
            return f"• <b>{name}</b> - {date_label}\n  {emoji} {price:.2f}% (전일대비 {diff:+.2f}p)\n\n"
        else:
            pct = (diff / prev['Close']) * 100
            emoji = "🟢" if pct >= 0 else "🔴"
            return f"{emoji} <b>{name}</b> - {date_label}\n  • 가격: <b>{price:,.2f}</b> ({pct:+.2f}%, {diff:+.2f}p)\n  • 주간: {((price-w_df['Close'])/w_df['Close']*100):+.2f}%\n\n"
    except:
        return f"• <b>{name}</b>: 분석 오류\n\n"

def main():
    now = datetime.now()
    # 오후 4시 ~ 오전 4시 사이면 '장 시작 전'
    is_open_report = True if now.hour >= 16 or now.hour <= 4 else False
    title = "🚀 장 시작 전 리포트" if is_open_report else "🏁 장 마감 리포트"
    
    report = f"✨ <b>{title}</b>\n({now.strftime('%Y/%m/%d %H:%M')})\n"
    report += "━━━━━━━━━━━━━━━━━━\n\n"
    
    report += "📊 <b>핵심 시장 지표</b>\n\n"
    for t, n in [("NQ=F", "나스닥100 선물"), ("ES=F", "S&P500 선물"), ("DX-Y.NYB", "달러 인덱스"), ("GC=F", "금 선물"), ("BTC-USD", "비트코인")]:
        report += get_data(t, n, is_open_report)
        
    report += "📉 <b>국채 수익률 (Yield)</b>\n\n"
    # ^2Y가 가장 정확한 2년물 금리 지수입니다.
    report += get_data("^2Y", "미 2년물 국채 금리", is_open_report, is_bond=True)
    report += get_data("^TNX", "미 10년물 국채 금리", is_open_report, is_bond=True)
    
    report += "━━━━━━━━━━━━━━━━━━\n\n"
    report += get_fred_data()
    report += "━━━━━━━━━━━━━━━━━━"
    
    send_telegram_msg(report)

if __name__ == "__main__":
    main()
