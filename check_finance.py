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
    'EFFR': {'name': 'EFFR (실효연방금리)', 'unit': '%'},
    'SOFR': {'name': 'SOFR (담보금리)', 'unit': '%'},
    'IORB': {'name': 'IORB (준비금이자)', 'unit': '%'},
    'DFEDTARL': {'name': 'Fed Funds Target (기준금리 하단)', 'unit': '%'}
}

def get_fred_data(fred, ticker, is_liquidity=False):
    try:
        config = INDICATORS.get(ticker)
        series = fred.get_series(ticker).dropna().sort_index()
        if len(series) < 2: return "\n데이터 업데이트 대기 중..."

        curr, prev = series.iloc[-1], series.iloc[-2]
        d_curr, d_prev = series.index[-1].strftime('%m/%d'), series.index[-2].strftime('%m/%d')
        diff = curr - prev
        unit = config['unit']
        
        if is_liquidity:
            div = config['scale_div']
            c_val, p_val, d_val = curr/div, prev/div, diff/div
            sign = "+" if d_val >= 0 else ""
            pct = (diff / prev * 100) if prev != 0 else 0
            # ★ 핵심: 여기서 시작할 때 \n을 두 번 넣어 확실하게 줄을 바꿉니다.
            return f"\n{p_val:,.2f}{unit}({d_prev}) → {c_val:,.2f}{unit}({d_curr}) <b>[{sign}{d_val:,.2f}{unit}] ({pct:+.2f}%)</b>"
        else:
            return f"\n{prev:.2f}%({d_prev}) → {curr:.2f}%({d_curr})"
    except: return "\n데이터 로드 실패"

def get_fomc_info():
    delta = datetime(2026, 1, 28) - datetime.now()
    return f"📅 다음 FOMC: 2026-01-28 ({max(delta.days, 0)}일 남음)"

def send_msg(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True})

def main():
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('CHAT_ID')
    api_key = os.environ.get('FRED_API_KEY')
    
    if not all([token, chat_id, api_key]): sys.exit(1)
    fred = Fred(api_key=api_key)
    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    # 리포트 1: 유동성 리포트 구성
    m1 = f"💰 <b>Liquidity & Banking (유동성 및 은행)</b>\nUpdate: {now}\n"
    for t in ['WALCL', 'M2SL', 'WTREGEN', 'RRPONTSYD', 'DPSACBW027SBOG', 'TOTLL']:
        # 각 지표 항목 앞에 \n을 추가하여 지표끼리도 줄을 바꿉니다.
        m1 += f"\n• {INDICATORS[t]['name']}: {get_fred_data(fred, t, True)}\n"
    send_msg(token, chat_id, m1)

    # 리포트 2: 금리 리포트 구성
    m2 = f"📈 <b>Rates & Risk (금리 및 리스크)</b>\n{get_fomc_info()}\n"
    for t in ['DFEDTARU', 'EFFR', 'SOFR', 'IORB', 'DFEDTARL']:
        m2 += f"\n• {INDICATORS[t]['name']}: {get_fred_data(fred, t, False)}\n"
    send_msg(token, chat_id, m2)

if __name__ == "__main__":
    main()
