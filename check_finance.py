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

def get_fred_data(fred, ticker, show_pct=False):
    try:
        config = INDICATORS.get(ticker)
        series = fred.get_series(ticker).sort_index().dropna()
        if series.empty: return "No Data"
        curr, prev = series.iloc[-1], series.iloc[-2]
        d_curr, d_prev = series.index[-1].strftime('%m/%d'), series.index[-2].strftime('%m/%d')
        diff = curr - prev
        unit = config['unit']
        
        if unit != "%":
            div = config['scale_div']
            c_val, p_val, d_val = curr/div, prev/div, diff/div
            sign = "+" if d_val >= 0 else ""
            # 데이터 시작 전 줄바꿈 추가
            res = f"\n{p_val:,.2f}{unit}({d_prev}) → {c_val:,.2f}{unit}({d_curr}) <b>[{sign}{d_val:,.2f}{unit}]</b>"
            if show_pct and prev != 0:
                pct = (diff / prev) * 100
                res += f" <b>({pct:+.2f}%)</b>"
            return res
        else:
            # 데이터 시작 전 줄바꿈 추가
            return f"\n{prev:.2f}%({d_prev}) → {curr:.2f}%({d_curr}) <b>[{diff:+.2f}%]</b>"
    except Exception as e:
        return f"\nError({ticker}): {str(e)}"

def get_fomc_info():
    # 현재 날짜 기준 다음 FOMC 날짜 계산 (2026-01-28)
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

        # Report 1: 유동성 및 은행
        m1 = f"💰 <b>Liquidity & Banking (유동성 및 은행)</b>\n"
        m1 += f"<code>Update: {now}</code>\n\n"
        
        m1 += f"• {INDICATORS['WALCL']['name']}: {get_fred_data(fred, 'WALCL', True)}\n\n"
        m1 += f"• {INDICATORS['M2SL']['name']}: {get_fred_data(fred, 'M2SL', True)}\n\n"
        m1 += f"• {INDICATORS['WMAPNS']['name']}: {get_fred_data(fred, 'WMAPNS', True)}\n\n"
        m1 += f"• {INDICATORS['WTREGEN']['name']}: {get_fred_data(fred, 'WTREGEN', True)}\n\n"
        m1 += f"• {INDICATORS['RRPONTSYD']['name']}: {get_fred_data(fred, 'RRPONTSYD', True)}\n\n"
        m1 += f"• {INDICATORS['DPSACBW027SBOG']['name']}: {get_fred_data(fred, 'DPSACBW027SBOG', True)}\n\n"
        m1 += f"• {INDICATORS['TOTLL']['name']}: {get_fred_data(fred, 'TOTLL', True)}"
        send_msg(token, chat_id, m1)

        # Report 2: 금리 및 리스크
        m2 = f"📈 <b>Rates & Risk (금리 및 리스크)</b>\n"
        m2 += f"<code>{get_fomc_info()}</code>\n"
        m2 += f"<code>Update: {now}</code>\n\n"
        
        m2 += f"• {INDICATORS['DFEDTARU']['name']}: {get_fred_data(fred, 'DFEDTARU')}\n\n"
        m2 += f"• {INDICATORS['EFFR']['name']}: {get_fred_data(fred, 'EFFR')}\n\n"
        m2 += f"• {INDICATORS['SOFR']['name']}: {get_fred_data(fred, 'SOFR')}\n\n"
        m2 += f"• {INDICATORS['IORB']['name']}: {get_fred_data(fred, 'IORB')}\n\n"
        m2 += f"• {INDICATORS['DFEDTARL']['name']}: {get_fred_data(fred, 'DFEDTARL')}"
        send_msg(token, chat_id, m2)

    except Exception as e:
        print(f"❌ 오류: {e}")

if __name__ == "__main__":
    main()
