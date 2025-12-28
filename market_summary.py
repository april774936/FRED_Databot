import os, requests, yfinance as yf
from datetime import datetime
from fredapi import Fred

def send_msg(msg):
    url = f"https://api.telegram.org/bot{os.environ.get('TELEGRAM_TOKEN')}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})

def get_data(ticker_symbol, name, is_open):
    try:
        t_code = "^2Y" if "2년물" in name else ticker_symbol
        df = yf.Ticker(t_code).history(period="7d").dropna()
        
        if df.empty and "2년물" in name:
            df = yf.Ticker("^IRX").history(period="7d").dropna()

        if df.empty: return f"• <b>{name}</b>\n데이터 로드 실패 ⚠️\n\n"

        curr, prev = df.iloc[-1], df.iloc[-2]
        w_df = df.iloc[0] 
        
        price = curr['Open'] if is_open else curr['Close']
        diff = price - prev['Close']
        w_diff = price - w_df['Close']
        date = curr.name.strftime('%m/%d')
        
        emoji = "📈" if diff >= 0 else "📉"
        
        if "국채 금리" in name:
            # 요청하신 양식: (이모티콘) 지표명
            res = f"{emoji} <b>{name}</b> - {date}\n"
            res += f"  현재: <b>{price:.2f}%</b> ({diff:+.2f}p)\n"
            res += f"  주간: {w_df['Close']:.2f}% ({w_diff:+.2f}p)\n\n"
        else:
            pct = (diff / prev['Close']) * 100
            res = f"{emoji} <b>{name}</b> - {date}\n"
            res += f"  • 현재가: <b>{price:,.2f}</b> ({pct:+.2f}%, {diff:+.2f}p)\n"
            res += f"  • 주간: {w_df['Close']:,.2f} ({((price-w_df['Close'])/w_df['Close']*100):+.2f}%, {price-w_df['Close']:+.2f}p)\n\n"
        return res
    except: return f"• <b>{name}</b>\n로드 에러\n\n"

def main():
    token, chat_id = os.environ.get('TELEGRAM_TOKEN'), os.environ.get('CHAT_ID')
    now = datetime.now()
    is_open = True if 16 <= now.hour or now.hour <= 4 else False
    
    fred = Fred(api_key=os.environ.get('FRED_API_KEY'))
    hy = fred.get_series('BAMLH0A0HYM2').dropna()
    hy_curr, hy_prev, hy_week = hy.iloc[-1], hy.iloc[-2], hy.iloc[-6]
    hy_diff, hy_w_diff = hy_curr - hy_prev, hy_curr - hy_week
    hy_emoji = "📈" if hy_diff >= 0 else "📉"
    
    report = f"✨ <b>{'🚀 장 시작 전' if is_open else '🏁 장 마감'} 리포트</b>\n"
    report += f"({now.strftime('%Y/%m/%d %H:%M')})\n"
    report += "━━━━━━━━━━━━━━━━━━\n\n"
    
    report += "📊 <b>핵심 시장 지표</b>\n\n"
    for t, n in [("NQ=F", "나스닥100 선물"), ("ES=F", "S&P500 선물"), ("DX-Y.NYB", "달러 인덱스"), ("GC=F", "금 선물"), ("BTC-USD", "비트코인")]:
        report += get_data(t, n, is_open)
        
    report += "💰 <b>국채 수익률 (Yield)</b>\n\n"
    report += get_data("^2Y", "미 2년물 국채 금리", is_open)
    report += get_data("^TNX", "미 10년물 국채 금리", is_open)
    
    # 정크본드도 동일한 양식으로 통합
    report += f"{hy_emoji} <b>정크본드 스프레드</b>\n"
    report += f"  현재: <b>{hy_curr:.2f}%</b> ({hy_diff:+.2f}p)\n"
    report += f"  주간: {hy_week:.2f}% ({hy_w_diff:+.2f}p)\n\n"
    report += "━━━━━━━━━━━━━━━━━━"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": report, "parse_mode": "HTML"})

if __name__ == "__main__":
    main()
