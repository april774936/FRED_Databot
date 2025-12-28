import os
import requests
from fredapi import Fred
from datetime import datetime
import sys

# 지표 설정
INDICATORS = {
    'WALCL': {'name': 'Fed Total Assets (연준총자산)', 'unit': 'T', 'scale_div': 1000000},
    'M2SL': {'name': 'M2 Money Stock (M2 통화량)', 'unit': 'T', 'scale_div': 1000},
    'WTREGEN': {'name': 'TGA Balance (TGA 잔고)', 'unit': 'B', 'scale_div': 1000},
    'RRPONTSYD': {'name': 'Reverse Repo (역레포 잔고)', 'unit': 'B', 'scale_div': 1},
    'DPSACBW027SBOG': {'name': 'Bank Deposits (은행 총예금)', 'unit': 'B', 'scale_div': 1},
    'TOTLL': {'name': 'Bank Loans (은행 총대출)', 'unit': 'B', 'scale_div': 1},
    'DFEDTARU': {'name': 'Fed Funds Target (기준금리 상단)', 'unit': '%'},
    'DFEDTARL': {'name': 'Fed Funds Target (기준금리 하단)', 'unit': '%'},
    'IORB': {'name': 'IORB (준비금이자)', 'unit': '%'},
    'EFFR': {'name': 'EFFR (실효연방금리)', 'unit': '%'},
    'SOFR': {'name': 'SOFR (담보금리)', 'unit': '%'}
}

def get_fred_data(fred, ticker, is_liquidity=False):
    try:
        config = INDICATORS.get(ticker)
        # FRED 데이터는 업데이트 주기가 다르므로 최근 5개 정도를 가져와서 처리
        series = fred.get_series(ticker).dropna().sort_index()
        
        if len(series) < 2:
            return "데이터 업데이트 대기 중..."

        curr, prev = series.iloc[-1], series.iloc[-2]
        d_curr, d_prev = series.index[-1].strftime('%m/%d'), series.index[-2].strftime('%m/%d')
        diff = curr - prev
        unit = config['unit']
        
        if is_liquidity:
            div = config['scale_div']
            c_val, p_val, d_val = curr/div, prev/div, diff/div
            sign = "+" if d_val >= 0 else ""
            pct = (diff / prev * 100) if prev != 0 else 0
            # 가독성을 위해 한 줄로 정리
            return f"\n{p_val:,.2f}{unit}({d_prev}) → {c_val:,.2f}{unit}({d_curr}) <b>[{sign}{d_val:,.2f}{unit}] ({pct:+.2f}%)</b>"
        else:
            return f"\n{prev:.2f}%({d_prev}) → {curr:.2f}%({d_curr})"
            
    except Exception as e:
        return f"\nError: 데이터 로드 실패"

def get_fomc_info():
    # 2026년 첫 FOMC 날짜 기준
    next_fomc = datetime(2026, 1, 28)
    today = datetime.now()
    delta = next_fomc - today
    days_left = max(delta.days, 0)
    return f"📅 다음 FOMC: 2026-01-28 ({days_left}일 남음)"

def send_msg(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": text, 
        "parse_mode": "HTML", 
        "disable_web_page_preview": True
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        if not res.ok: print(f"❌ 전송 실패: {res.text}")
    except Exception as e:
        print(f"❌ 전송 중 에러: {e}")

def main():
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('CHAT_ID')
    api_key = os.environ.get('FRED_API_KEY')
    
    if not all([token, chat_id, api_key]):
        print("환경 변수 설정이 누락되었습니다.")
        sys.exit(1)

    try:
        fred = Fred(api_key=api_key)
        now_dt = datetime.now().strftime('%Y-%m-%d %H:%M')

        # 리포트 1: 유동성 및 은행
        m1 = f"💰 <b>Liquidity & Banking (유동성 및 은행)</b>\n"
        m1 += f"<code>Update: {now_dt}</code>\n"
        m1 += "━━━━━━━━━━━━━━━━━━\n"
        liquidity_tickers = ['WALCL', 'M2SL', 'WTREGEN', 'RRPONTSYD', 'DPSACBW027SBOG', 'TOTLL']
        for t in liquidity_tickers:
            m1 += f"• {INDICATORS[t]['name']}: {get_fred_data(fred, t, True)}\n"
        send_msg(token, chat_id, m1)

        # 리포트 2: 금리 및 리스크
        m2 = f"📈 <b>Rates & Risk (금리 및 리스크)</b>\n"
        m2 += f"{get_fomc_info()}\n"
        m2 += "━━━━━━━━━━━━━━━━━━\n"
        rate_tickers = ['DFEDTARU', 'EFFR', 'SOFR', 'IORB', 'DFEDTARL']
        for t in rate_tickers:
            m2 += f"• {INDICATORS[t]['name']}: {get_fred_data(fred, t, False)}\n"
        send_msg(token, chat_id, m2)

    except Exception as e:
        print(f"❌ 실행 중 오류: {e}")

if __name__ == "__main__":
    main()
