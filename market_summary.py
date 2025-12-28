import os, requests, yfinance as yf
from datetime import datetime
from fredapi import Fred

def send_msg(msg):
    url = f"https://api.telegram.org/bot{os.environ.get('TELEGRAM_TOKEN')}/sendMessage"
    requests.post(url, json={"chat_id": os.environ.get('CHAT_ID'), "text": msg, "parse_mode": "HTML"})

def get_data(ticker_symbol, name, is_open):
    try:
        # 1. 티커 보정: 2년물 국채 수익률은 ^ZT=F(선물)보다 ^2Y(현물) 또는 ZT=F가 안정적입니다.
        t_code = "ZT=F" if "2년물" in name else ticker_symbol
        
        # 2. 데이터 로드: 충분한 기간(5일치)을 가져와 최신 유효값을 찾습니다.
        ticker = yf.Ticker(t_code)
        df = ticker.history(period="5d")
        
        # 3. 결측치(NaN)가 있는 행을 제거하여 실제 데이터가 있는 날만 남깁니다.
        df = df.dropna()
        
        if df.empty:
            return f"• <b>{name}</b> - 데이터 없음 ⚠️\n\n"

        curr, prev = df.iloc[-1], df.iloc[-2]
        w_df = df.iloc[0] # 5일전 데이터
        
        price = curr['Open'] if is_open else curr['Close']
        diff = price - prev['Close']
        date = curr.name.strftime('%m/%d')
        
        if "국채 금리" in name:
            emoji = "📈" if diff >= 0 else "📉"
            res = f"• <b>{name}</b> - {date}\n"
            res += f"  {emoji} <b>{price:.2f}%</b> (전일 {diff:+.2f}p)\n"
            res += f"  └ 주간: {w_df['Close']:.2f}% ({price-w_df['Close']:+.2f}p)\n\n"
        else:
            pct = (diff / prev['Close']) * 100
            emoji = "🟢" if pct >= 0 else "🔴"
            res = f"{emoji} <b>{name}</b> - {date}\n"
            res += f"  • 현재가: <b>{price:,.2f}</b> ({pct:+.2f}%, {diff:+.2f}p)\n\n"
        return res
    except Exception as e:
        return f"• <b>{name}</b> 로드 실패 (에러: {str(e)[:10]})\n\n"

def main():
    now = datetime.now()
    is_open = True if 16 <= now.hour or now.hour <= 4 else False
    
    # FRED에서 정크본드 데이터 로드
    fred = Fred(api_key=os.environ.get('FRED_API_KEY'))
    hy_series = fred.get_series('BAMLH0A0HYM2').dropna()
    hy_curr, hy_prev = hy_series.iloc[-1], hy_series.iloc[-2]
    
    report = f"✨ <b>{'🚀 장 시작 전' if is_open else '🏁 장 마감'} 리포트</b>\n({now.strftime('%Y/%m/%d %H:%M')})\n━━━━━━━━━━━━━━━━━━\n\n"
    
    report += "📊 <b>핵심 시장 지표</b>\n\n"
    for t, n in [("NQ=F", "나스닥100 선물"), ("ES=F", "S&P500 선물"), ("DX-Y.NYB", "달러 인덱스"), ("GC=F", "금 선물"), ("BTC-USD", "비트코인")]:
        report += get_data(t, n, is_open)
        
    report += "📉 <b>국채 수익률 (Yield)</b>\n\n"
    # 2년물 금리를 확실히 가져오기 위해 전용 티커 적용
    report += get_data("ZT=F", "미 2년물 국채 금리", is_open) 
    report += get_data("^TNX", "미 10년물 국채 금리", is_open)
    
    report += f"💩 <b>정크본드 스프레드</b>\n  └ 수치: <b>{hy_curr:.2f}%</b> ({hy_curr-hy_prev:+.2f}p)\n━━━━━━━━━━━━━━━━━━"
    
    send_msg(report)

if __name__ == "__main__":
    main()
