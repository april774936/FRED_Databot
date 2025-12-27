import os
import requests
from fredapi import Fred
from datetime import datetime
import sys

# 지표 설정
INDICATORS = {
    'WALCL': {'name': 'Fed Total Assets (연준총자산)', 'unit': 'T', 'scale_div': 1000000},
    'M2SL': {'name': 'M2 Money Stock (M2 통화량)', 'unit': 'T', 'scale_div': 1000},
    'WMAPNS': {'name': 'MMF Total (MMF 총잔액)', 'unit': 'T', 'scale_div': 1000},
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
        # MMF 등 주간 데이터 대응을 위해 dropna() 후 최신 2개 추출
        series = fred.get_series(ticker).dropna().sort_index()
        
        if len(series) < 2:
            return "\n데이터 업데이트 대기 중..."

        curr, prev = series.iloc[-1], series.iloc[-2]
        d_curr, d_prev = series.index[-1].strftime('%m/%d'), series.index[-2].strftime('%m/%d')
        diff = curr - prev
        unit = config['unit']
        
        if is_liquidity:
            # [유동성 파트] 날짜 + 변화량 + 퍼센트 표시
            div = config['scale_div']
            c_val, p_val, d_val = curr/div, prev/div, diff/div
            sign = "+" if d_val >= 0 else ""
            pct = (diff / prev * 100) if prev != 0 else 0
            return f"\n{p_val:,.2f}{unit}({d_prev}) → {c_val:,.2f}{unit}({d_curr}) <b>[{sign}{d_val:,.2f}{unit}] ({pct:+.2f}%)</b>"
        else:
            # [금리 파트] 변화량 없이 날짜만 표시 (요청하신 형식)
            return f"\n{prev:.2f}%({d_prev}) → {curr:.2f}%({d_curr})"
            
    except Exception as e:
        return f"\nError({ticker}): 데이터 불러오기 실패"

def get_fomc_info():
    next_fomc = datetime(2026, 1, 28)
    today = datetime.now()
    delta = next_fomc - today
    days_left = delta.days if delta.days >= 0 else 0
    return f"📅 다음 FOMC: 2026-01-28 ({days_left}일 남음)"

def send_msg(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    res = requests.post(url, json=payload)
    if not res.ok: print(f"❌ 전송 실패: {res.text}")

def main():
    token, chat_id, api_key = os.environ.get('TELEGRAM_TOKEN'), os.environ.get('CHAT_ID'), os.environ.get('FRED_API_KEY')
    if not all([token, chat_id, api_key]): sys.exit(1)

    try:
        fred = Fred(api_key=api_key)
        now = datetime.now().strftime('%Y-%m-%d %H:%M')

        # Report 1: 유동성 및 은행 (기존 유지)
        m1 = f"💰 <b>Liquidity & Banking (유동성 및 은행)</b>\n"
        m1 += f"<code>Update: {now}</code>\n\n"
        m1 += f"• {INDICATORS['WALCL']['name']}: {get_fred_data(fred, 'WALCL', True)}\n\n"
        m1 += f"• {INDICATORS['M2SL']['name']}: {get_fred_data(fred, 'M2SL', True)}\n\n"
        m1 += f"• {INDICATORS['WMAPNS']['name']}: {get_fred_data(fred, 'WMAPNS', True)}\n\n"
