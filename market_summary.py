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
        # BofA 하이일드 옵션 조정 스프레드 (종목코드: BAMLH0A0HYM2)
        data = fred.get_series('BAMLH0A0HYM2')
        curr, prev = data.iloc[-1], data.iloc[-2]
        diff = curr - prev
        status = "🟢 안정(위험선호)" if diff < 0 else "🔴 주의(위험회피)"
        return f"🛡️ <b>정크본드 스프레드</b>\n  └ 수치: <b>{curr:.2f}%</b> ({diff:+.2f}p)\n  └ 현재 시장은 {status} 분위기\n\n"
    except:
        return "• FRED 데이터 로드 일시 실패 ❌\n\n"

def get_data(ticker_symbol, name, is_open_report, is_bond=False):
    try:
        # 2년물 금리 오류(100.xx 가격 출력) 방지를 위한 전용 티커 매핑
        ticker_to_use = ticker_symbol
        if "2년물" in name:
            ticker_to_use = "^2Y" # 수익률 지수 티커 우선 사용
            
        ticker = yf.Ticker(ticker_to_use)
        df = ticker.history(period="1mo").dropna()
        
        # 보조 티커: ^2Y 실패 시 단기국채(^IRX)로 우회
        if df.empty and "2년물" in name:
            df = yf.Ticker("^IRX").history(period="1mo").dropna()

        if df.empty: return f"• <b>{name}</b>: 데이터 로드 실패 ⚠️\n\n"
        
        curr, prev = df.iloc[-1], df.iloc[-2]
        w_df = df.iloc[max(0, len(df)-6)]
        
        days = ['월', '화', '수', '목', '금', '토', '일']
        date_label = f"{curr.name.strftime('%m/%d')}({days[curr.name.weekday()]})"
        
        price = curr['Open'] if is_open_report else curr['Close']
        diff = price - prev['Close']
        
        if is_bond:
            # 안전장치: 수익률이 50% 이상(가격 데이터)일 경우 예외 처리
            if price > 50:
                return f"• <b>{name}</b>: 수치 보정 중 (재실행 요망) ⏳\n\n"
                
            emoji = "📈" if diff >= 0 else "📉"
            return f"• <b>{name}</b> - {date_label}\n  {emoji} <b>{price:.2f}%</b> (전일대비 {diff:+.2f}p)\n\n"
        else:
            pct = (diff / prev['Close']) * 100
            # 미국식 색상: 상승(초록 🟢), 하락(빨강 🔴)
            emoji = "🟢" if pct >= 0 else "🔴"
            return f"{emoji} <b>{name}</b> - {date_label}\n  • 가격: <b>{price:,.2f}</b> ({pct:+.2f}%, {diff:+.2f}p)\n  • 주간: {((price-w_df['Close'])/w_df['Close']*100):+.2f}%\n\n"
    except:
        return f"• <b>{name}</b>: 분석 오류 ❌\n\n"

def main():
    now = datetime.now()
    # 실행 시간 기준 리포트 성격 정의 (KST 기준 16시~04시: 장 시작 전 / 04시~16시: 장 마감)
    is_open_report = True if 16 <= now.hour or now.hour <= 4 else False
    title_label = "🚀 장 시작 전 리포트" if is_open_report else "🏁 장 마감 리포트"
    
    report = f"✨ <b>{title_label}</b>\n({now.strftime('%Y/%m/%d %H:%M')})\n"
    report += "━━━━━━━━━━━━━━━━━━\n\n"
    
    # 1. 시장 지표
    report += "📊 <b>핵심 시장 지표</b>\n\n"
    market_targets = [
        ("NQ=F", "나스닥100 선물"), ("ES=F", "S&P500 선물"), 
        ("DX-Y.NYB", "달러 인덱스"), ("GC=F", "금 선물"), ("BTC-USD", "비트코인")
    ]
    for t, n in market_targets:
        report += get_data(t, n, is_open_report)
        
    # 2. 국채 금리
    report += "📉 <b>국채 수익률 (Yield)</b>\n\n"
    report += get_data("^2Y", "미 2년물 국채 금리", is_open_report, is_bond=True)
    report += get_data("^TNX", "미 10년물 국채 금리", is_open_report, is_bond=True)
    
    # 3. 위험 지표 (FRED)
    report += "━━━━━━━━━━━━━━━━━━\n\n"
    report += get_fred_data()
    report += "━━━━━━━━━━━━━━━━━━"
    
    send_telegram_msg(report)

if __name__ == "__main__":
    main()
