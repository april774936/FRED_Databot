import os, requests, yfinance as yf
from datetime import datetime
from fredapi import Fred

def send_msg(msg):
    url = f"https://api.telegram.org/bot{os.environ.get('TELEGRAM_TOKEN')}/sendMessage"
    requests.post(url, json={"chat_id": os.environ.get('CHAT_ID'), "text": msg, "parse_mode": "HTML"})

def get_data(ticker_symbol, name, is_open):
    try:
        # 2년물은 수익률 지수(^2Y) 사용
        t_code = "^2Y" if "2년물" in name else ticker_symbol
        
        ticker = yf.Ticker(t_code)
        df = ticker.history(period="7d").dropna()
        
        if df.empty and "2년물" in name:
            df = yf.Ticker("^IRX").history(period="7d").dropna()

        if df.empty:
            return f"• <b>{name}</b>\n데이터 로드 실패 ⚠️\n\n"

        curr, prev = df.iloc[-1], df.iloc[-2]
        w_df = df.iloc[0] 
        
        price = curr['Open'] if is_open else curr['Close']
        diff = price - prev['Close']
        date = curr.name.strftime('%m/%d')
        
        # 상승/하락 이모티콘 설정 (📈/📉 로 통일)
        chart_emoji = "📈" if diff >= 0 else "📉"
        
        if "국채 금리" in name:
            # 국채 금리는 달러(💵) 이모티콘 사용
            res = f"💵 <b>{name}</b> - {date}\n"
            res += f"  {chart_emoji} <b>{price:.2f}%</b> (전일 {diff:+.2f}p)\n"
            res += f"  └ 주간: {w_df['Close']:.2f}% ({price-w_df['Close']:+.2f}p)\n\n"
        else:
            # 주식/선물/코인 출력
            pct = (diff / prev['Close']) * 100
            res = f"{chart_emoji} <b>{name}</b> - {date}\n"
            res += f"  • 현재가: <b>{price:,.2f}</b> ({pct:+.2f}%, {diff:+.2f}p)\n"
            res += f"  • 주간: {w_df['Close']:,.2f} ({((price-w_df['Close'])/w_df['Close']*100):+.2f}%, {price-w_df['Close']:+.2f}p)\n\n"
        return res
    except Exception as e:
        return f"• <b>{name}</b>\n로드 에러: {str(e)[:15]}\n\n"

def main():
    now = datetime.now()
    is_open = True if 16 <= now.hour or now.hour <= 4 else False
    
    fred = Fred(api_key=os.environ.get('FRED_API_KEY'))
    hy_series = fred.get_series('BAMLH0A0HYM2').dropna()
    hy_curr, hy_prev = hy_series.iloc[-1], hy_series.iloc[-2]
    
    report = f"✨ <b>{'🚀 장 시작 전' if is_open else '🏁 장 마감'} 리포트</b>\n"
    report += f"({now.strftime('%Y/%m/%d %H:%M')})\n"
    report += "━━━━━━━━━━━━━━━━━━\n\n"
    
    report += "📊 <b>핵심 시장 지표</b>\n\n"
    for t, n in [("NQ=F", "나스닥100 선물"), ("ES=F", "S&P500 선물"), ("DX-Y.NYB", "달러 인덱스"), ("GC=F", "금 선물"), ("BTC-USD", "비트코인")]:
        report += get_data(t, n, is_open)
        
    report += "📉 <b>국채 수익률 (Yield)</b>\n\n"
    report += get_data("^2Y", "미 2년물 국채 금리", is_open)
    report += get_data("^TNX", "미 10년물 국채 금리", is_open)
    
    report += "━━━━━━━━━━━━━━━━━━\n\n"
    report += f"💩 <b>정크본드 스프레드</b>\n"
    # 스프레드 변동에 따른 이모티콘 적용
    hy_diff = hy_curr - hy_prev
    hy_emoji = "📈" if hy_diff >= 0 else "📉"
    report += f"  └ 수치: <b>{hy_curr:.2f}%</b> ({hy_emoji} {hy_diff:+.2f}p)\n\n"
    report += "━━━━━━━━━━━━━━━━━━"
    
    send_msg(report)

if __name__ == "__main__":
    main()
