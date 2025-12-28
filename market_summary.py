import os, requests, yfinance as yf
from datetime import datetime
from fredapi import Fred

def send_msg(msg):
    url = f"https://api.telegram.org/bot{os.environ.get('TELEGRAM_TOKEN')}/sendMessage"
    requests.post(url, json={"chat_id": os.environ.get('CHAT_ID'), "text": msg, "parse_mode": "HTML"})

def get_data(ticker_symbol, name, is_open_report, is_bond=False):
    try:
        t_code = "^2Y" if "2년물" in name else ticker_symbol
        df = yf.Ticker(t_code).history(period="3mo").dropna()
        curr, prev, w_df, m_df = df.iloc[-1], df.iloc[-2], df.iloc[-6], df.iloc[-21]
        price = curr['Open'] if is_open_report else curr['Close']
        diff = price - prev['Close']
        
        date_label = f"{curr.name.strftime('%m/%d')}({['월','화','수','목','금','토','일'][curr.name.weekday()]})"
        if is_bond:
            emoji = "📈" if diff >= 0 else "📉"
            res = f"• <b>{name}</b> - {date_label}\n  {emoji} <b>{price:.2f}%</b> (전일 {diff:+.2f}p)\n"
            res += f"  └ 주간: {w_df['Close']:.2f}% ({price-w_df['Close']:+.2f}p)\n  └ 월간: {m_df['Close']:.2f}% ({price-m_df['Close']:+.2f}p)\n\n"
        else:
            pct = (diff / prev['Close']) * 100
            emoji = "🟢" if pct >= 0 else "🔴"
            res = f"{emoji} <b>{name}</b> - {date_label}\n  • 현재가: <b>{price:,.2f}</b> ({pct:+.2f}%, {diff:+.2f}p)\n"
            res += f"  • 주간: {w_df['Close']:,.2f} ({((price-w_df['Close'])/w_df['Close']*100):+.2f}%, {price-w_df['Close']:+.2f}p)\n"
            res += f"  • 월간: {m_df['Close']:,.2f} ({((price-m_df['Close'])/m_df['Close']*100):+.2f}%, {price-m_df['Close']:+.2f}p)\n\n"
        return res
    except: return f"• {name}: 로드 실패\n\n"

def main():
    now = datetime.now()
    is_open = True if 16 <= now.hour or now.hour <= 4 else False
    fred = Fred(api_key=os.environ.get('FRED_API_KEY'))
    hy = fred.get_series('BAMLH0A0HYM2')
    
    report = f"✨ <b>{'🚀 장 시작 전' if is_open else '🏁 장 마감'} 리포트</b>\n({now.strftime('%Y/%m/%d %H:%M')})\n━━━━━━━━━━━━━━━━━━\n\n📊 <b>핵심 시장 지표</b>\n\n"
    for t, n in [("NQ=F", "나스닥100 선물"), ("ES=F", "S&P500 선물"), ("DX-Y.NYB", "달러 인덱스"), ("GC=F", "금 선물"), ("BTC-USD", "비트코인")]:
        report += get_data(t, n, is_open)
    report += "📉 <b>국채 수익률 (Yield)</b>\n\n"
    report += get_data("^2Y", "미 2년물 국채 금리", is_open, True)
    report += get_data("^TNX", "미 10년물 국채 금리", is_open, True)
    report += f"💩 <b>정크본드 스프레드</b>\n  └ 수치: <b>{hy.iloc[-1]:.2f}%</b> ({hy.iloc[-1]-hy.iloc[-2]:+.2f}p)\n━━━━━━━━━━━━━━━━━━"
    send_msg(report)

if __name__ == "__main__":
    main()
