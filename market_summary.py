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
        if not fred_key: return "• ⚠️ FRED API 설정 확인 필요\n\n"
        fred = Fred(api_key=fred_key)
        data = fred.get_series('BAMLH0A0HYM2')
        curr, prev = data.iloc[-1], data.iloc[-2]
        diff = curr - prev
        status = "🟢 안정" if diff < 0 else "🔴 주의"
        return f"💩 <b>정크본드 스프레드</b>\n  └ 수치: <b>{curr:.2f}%</b> ({diff:+.2f}p)\n  └ 현재 시장은 {status} 분위기\n\n"
    except:
        return "• 💩 정크본드 데이터 로드 실패\n\n"

def get_data(ticker_symbol, name, is_open_report, is_bond=False):
    try:
        # 채권 금리 전용 티커 처리
        ticker_to_use = "^2Y" if "2년물" in name else ticker_symbol
        ticker = yf.Ticker(ticker_to_use)
        df = ticker.history(period="3mo").dropna()
        
        if df.empty and "2년물" in name:
            df = yf.Ticker("^IRX").history(period="3mo").dropna()

        if df.empty: return f"• <b>{name}</b>: 데이터 로드 실패 ⚠️\n\n"
        
        curr, prev = df.iloc[-1], df.iloc[-2]
        w_df, m_df = df.iloc[max(0, len(df)-6)], df.iloc[max(0, len(df)-21)]
        
        date_label = f"{curr.name.strftime('%m/%d')}({['월','화','수','목','금','토','일'][curr.name.weekday()]})"
        price = curr['Open'] if is_open_report else curr['Close']
        
        diff = price - prev['Close']
        
        if is_bond:
            # 채권 금리용 출력 (퍼센트 변화량 삭제)
            if price > 50: return f"• <b>{name}</b>: 수치 보정 중... ⏳\n\n"
            emoji = "📈" if diff >= 0 else "📉"
            res = f"• <b>{name}</b> - {date_label}\n"
            res += f"  {emoji} <b>{price:.2f}%</b> (전일 {diff:+.2f}p)\n"
            res += f"  └ 주간: {w_df['Close']:.2f}% ({price-w_df['Close']:+.2f}p)\n"
            res += f"  └ 월간: {m_df['Close']:.2f}% ({price-m_df['Close']:+.2f}p)\n\n"
        else:
            # 주식/선물/코인용 출력
            pct = (diff / prev['Close']) * 100
            emoji = "🟢" if pct >= 0 else "🔴"
            res = f"{emoji} <b>{name}</b> - {date_label}\n"
            res += f"  • 현재가: <b>{price:,.2f}</b> ({pct:+.2f}%, {diff:+.2f}p)\n"
            res += f"  • 주간: {w_df['Close']:,.2f} ({((price-w_df['Close'])/w_df['Close']*100):+.2f}%, {price-w_df['Close']:+.2f}p)\n"
            res += f"  • 월간: {m_df['Close']:,.2f} ({((price-m_df['Close'])/m_df['Close']*100):+.2f}%, {price-m_df['Close']:+.2f}p)\n\n"
        return res
    except:
        return f"• <b>{name}</b>: 분석 오류 ❌\n\n"

def main():
    now = datetime.now()
    is_open_report = True if 16 <= now.hour or now.hour <= 4 else False
    title_label = "🚀 장 시작 전 리포트" if is_open_report else "🏁 장 마감 리포트"
    
    report = f"✨ <b>{title_label}</b>\n({now.strftime('%Y/%m/%d %H:%M')})\n"
    report += "━━━━━━━━━━━━━━━━━━\n\n"
    
    report += "📊 <b>핵심 시장 지표</b>\n\n"
    for t, n in [("NQ=F", "나스닥100 선물"), ("ES=F", "S&P500 선물"), ("DX-Y.NYB", "달러 인덱스"), ("GC=F", "금 선물"), ("BTC-USD", "비트코인")] :
        report += get_data(t, n, is_open_report)
        
    report += "📉 <b>국채 수익률 (Yield)</b>\n\n"
    report += get_data("^2Y", "미 2년물 국채 금리", is_open_report, is_bond=True)
    report += get_data("^TNX", "미 10년물 국채 금리", is_open_report, is_bond=True)
    
    report += "━━━━━━━━━━━━━━━━━━\n\n"
    report += get_fred_data()
    report += "━━━━━━━━━━━━━━━━━━"
    
    send_telegram_msg(report)

if __name__ == "__main__":
    main()
