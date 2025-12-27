import os, requests, yfinance as yf
from datetime import datetime

def main():
    token, chat_id = os.environ.get('TELEGRAM_TOKEN'), os.environ.get('CHAT_ID')
    if not token or not chat_id: return
    
    msg = f"🏁 <b>시장 마감 리포트 ({datetime.now().strftime('%m/%d')})</b>\n\n"
    # 상세 지표 (나스닥, S&P500, 비트코인)
    for t, n in [("NQ=F", "나스닥100 선물"), ("ES=F", "S&P500 선물"), ("BTC-USD", "비트코인")]:
        try:
            df = yf.Ticker(t).history(period="2mo")
            curr, prev = df.iloc[-1], df.iloc[-2]
            p, d = curr['Close'], ((curr['Close']-prev['Close'])/prev['Close'])*100
            w = ((p-df.iloc[-6]['Close'])/df.iloc[-6]['Close'])*100
            m = ((p-df.iloc[-21]['Close'])/df.iloc[-21]['Close'])*100
            msg += f"{'🔴' if d<0 else '🔵'} <b>{n}</b>\n• 현재가: {p:,.2f} ({d:+.2f}%)\n• 주간/월간: {w:+.2f}% / {m:+.2f}%\n• 거래량: {curr['Volume']:,.0f}\n\n"
        except: msg += f"• {n}: 로드 실패\n\n"
        
    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})

if __name__ == "__main__": main()
