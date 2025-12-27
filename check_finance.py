import os
import requests
from fredapi import Fred
from datetime import datetime
import sys

# 지표 설정 (국채 금리 및 기준금리 추가)
INDICATORS = {
    'WALCL': {'name': 'Fed Total Assets (연준총자산)', 'unit': 'T', 'scale_div': 1000000},
    'M2SL': {'name': 'M2 Money Stock (M2 통화량)', 'unit': 'T', 'scale_div': 1000},
    'WTREGEN': {'name': 'TGA Balance (TGA 잔고)', 'unit': 'B', 'scale_div': 1000},
    'RRPONTSYD': {'name': 'Reverse Repo (역레포 잔고)', 'unit': 'B', 'scale_div': 1},
    'DPSACBW027SBOG': {'name': 'Bank Deposits (은행 총예금)', 'unit': 'B', 'scale_div': 1},
    'TOTLL': {'name': 'Bank Loans (은행 총대출)', 'unit': 'B', 'scale_div': 1},
    'DFEDTARU': {'name': 'Fed Funds Rate (미 기준금리 상단)', 'unit': '%'},
    'DGS10': {'name': '10Y Treasury (미 국채 10년)', 'unit': '%'},
    'DGS2': {'name': '2Y Treasury (미 국채 2년)', 'unit': '%'},
    'IORB': {'name': 'IORB (준비금이자)', 'unit': '%'},
    'EFFR': {'name': 'EFFR (실효연방금리)', 'unit': '%'},
    'SOFR': {'name': 'SOFR (담보금리)', 'unit': '%'},
    'BAMLH0A0HYM2': {'name': 'HY Spread (하이일드)', 'unit': '%'}
}

def get_fred_data(fred, ticker):
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
            curr, prev, diff = curr/div, prev/div, diff/div
            sign = "+" if diff >= 0 else ""
            return f"\n{prev:,.2f}{unit}({d_prev}) → {curr:,.2f}{unit}({d_curr}) <b>[{sign}{diff:,.2f}{unit}]</b>"
        else:
            sign = "+" if diff >= 0 else ""
            return f"\n{prev:.2f}%({d_prev}) → {curr:.2f}%({d_curr}) <b>[{sign}{diff:.2f}%]</b>"
    except Exception as e:
        return f"\nError({ticker}): {str(e)}"

def send_msg(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    res = requests.post(url, json=payload)
    if not res.ok: print(f"❌ 전송 실패: {res.text}")

def main():
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('CHAT_ID')
    api_key = os.environ.get('FRED_API_KEY')
    if not all([token, chat_id, api_key]): sys.exit(1)

    try:
        fred = Fred(api_key=api_key)
        now = datetime.now().strftime('%Y-%m-%d %H:%M')

        # Report 1: Liquidity & Banking
        m1 = f"💰 <b>Liquidity & Banking (유동성 및 은행)</b>\n<code>Update: {now}</code>\n\n"
        m1 += f"• {INDICATORS['WALCL']['name']}: {get_fred_data(fred, 'WALCL')}\n\n"
        m1 += f"• {INDICATORS['M2SL']['name']}: {get_fred_data(fred, 'M2SL')}\n\n"
        m1 += f"• {INDICATORS['WTREGEN']['name']}: {get_fred_data(fred, 'WTREGEN')}\n\n"
        m1 += f"• {INDICATORS['RRPONTSYD']['name']}: {get_fred_data(fred, 'RRPONTSYD')}\n\n"
        m1 += f"• {INDICATORS['DPSACBW027SBOG']['name']}: {get_fred_data(fred, 'DPSACBW027SBOG')}\n\n"
        m1 += f"• {INDICATORS['TOTLL']['name']}: {get_fred_data(fred, 'TOTLL')}"
        send_msg(token, chat_id, m1)

        # Report 2: Rates & Risk (추가 지표 반영)
        m2 = f"📈 <b>Rates & Risk (금리 및 리스크)</b>\n<code>Update: {now}</code>\n\n"
        m2 += f"• {INDICATORS['DFEDTARU']['name']}: {get_fred_data(fred, 'DFEDTARU')}\n\n"
        m2 += f"• {INDICATORS['DGS10']['name']}: {get_fred_data(fred, 'DGS10')}\n\n"
        m2 += f"• {INDICATORS['DGS2']['name']}: {get_fred_data(fred, 'DGS2')}\n\n"
        m2 += f"• {INDICATORS['IORB']['name']}: {get_fred_data(fred, 'IORB')}\n\n"
        m2 += f"• {INDICATORS['EFFR']['name']}: {get_fred_data(fred, 'EFFR')}\n\n"
        m2 += f"• {INDICATORS['SOFR']['name']}: {get_fred_data(fred, 'SOFR')}\n\n"
        m2 += f"• {INDICATORS['BAMLH0A0HYM2']['name']}: {get_fred_data(fred, 'BAMLH0A0HYM2')}"
        send_msg(token, chat_id, m2)

    except Exception as e:
        print(f"❌ 오류: {e}")

if __name__ == "__main__":
    main()
