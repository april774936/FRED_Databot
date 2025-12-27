import os, requests, yfinance as yf, sys
from datetime import datetime

def get_detailed_info(ticker_symbol, name):
    try:
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period="2mo")
        if len(df) < 21: return f"• {name}: 데이터 부족\n\n"
        curr, prev = df.iloc[-1], df.iloc[-2]
        price = curr['Close']
        daily_pct = ((price - prev['Close']) / prev['Close']) * 100
        w_pct = ((price - df.iloc[-6]['Close']) / df.iloc[-6]['Close']) * 100
        m_pct = ((price - df.iloc[-21]['Close']) / df.iloc[-21]['Close']) * 100
        vol, avg_vol = curr['Volume'], df['Volume'].tail(5).mean()
        emoji = "🔴" if daily_pct < 0 else "🔵"
        return f"{emoji} <b>{name}</b>\n• 현재가: {price:,.2f} ({daily_pct:+.2f}%)\n• 주간/월간: {w_pct:+.2f}% / {m_pct:+.2f}%\n• 거래량: {vol:,.0f} (5일평균: {avg_vol:,.0f})\n\n"
    except: return f"• {name}: 로드 실패\n\n"

def get_simple_info(ticker_symbol, name, is_yield=False):
    try:
        data = yf.Ticker(ticker_symbol).history(period="2d")
        curr, prev = data['Close'].iloc[-1], data['Close'].iloc[-2]
        chg = ((curr - prev) / prev) * 100
        return f"{'🔺' if chg > 0 else '🔻'} {name}: {curr:.3f}{'%' if is_yield else ''} ({chg:+.2f}%)\n"
    except: return f"• {name}: 로드 실패\n"

def main():
    if datetime.now().weekday() in [0, 6]: return # 일, 월요일 아침은 미장 휴무 반영 종료
    token, chat_id = os.environ.get('TELEGRAM_TOKEN'), os.environ.get('CHAT_ID')
    msg = f"🏁 <b>시장 마감 리포트 ({datetime.now().strftime('%m/%d')})</b>\n\n"
    msg += "[지수 및 가상화폐 상세]\n"
    for t, n in [("NQ=F", "나스닥100 선물"), ("ES=F", "S&P500 선물"), ("BTC-USD", "비트코인")]:
        msg += get_detailed_info(t, n)
    msg += "💵 <b>금리 및 달러</b>\n"
    msg += get_simple_info("^ZT=F", "미 2년물 금리", True)
    msg += get_simple_info("^TNX", "미 10년물 금리", True)
    msg += get_simple_info("DX=F", "달러 인덱스")
    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})

if __name__ == "__main__": main()
