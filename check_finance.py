import os
import requests
from fredapi import Fred
from datetime import datetime

# 지표 설정
INDICATORS = {
    'WALCL': {'name': 'Fed Total Assets (연준총자산)', 'unit': 'T', 'scale_div': 1000000},
    'M2SL': {'name': 'M2 Money Stock (M2 통화량)', 'unit': 'T', 'scale_div': 1000},
    'WTREGEN': {'name': 'TGA Balance (TGA 잔고)', 'unit': 'B', 'scale_div': 1000},
    'RRPONTSYD': {'name': 'Reverse Repo (역레포 잔고)', 'unit': 'B', 'scale_div': 1},
    'DPSACBW027SBOG': {'name': 'Bank Deposits (은행 총예금)', 'unit': 'B', 'scale_div': 1},
    'TOTLL': {'name': 'Bank Loans (은행 총대출)', 'unit': 'B', 'scale_div': 1},
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
            return f"{prev:,.1f}{unit}({d_prev}) → {curr:,.1f}{unit}({d_curr}) <b>[{sign}{diff:,.1f}{unit}]</b>"
        else:
            sign = "+" if diff >= 0 else ""
            return f"{prev:.2f}%({d_prev}) → {curr:.2f}%({d_curr}) <b>[{sign}{diff:.2f}%]</b>"
    except Exception as e:
        return f"Error: {str(e)}"

def send_msg(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    requests.post(url, json=payload)

def main():
    try:
        fred = Fred(api_key=os.environ['FRED_API_KEY'])
        token = os.environ['TELEGRAM_TOKEN']
        chat_id = os.environ['CHAT_ID']
        now = datetime.now().strftime('%m/%d %H:%M')

        # Report 1
        m1 = f"💰 <b>Liquidity & Banking (유동성 및 은행)</b>\n<small>Date: {now}</small>\n\n"
        m1 += f"• {INDICATORS['WALCL']['name']}: {get_fred_data(fred, 'WALCL')}\n"
        m1 += f"• {INDICATORS['M2SL']['name']}: {get_fred_data(fred, 'M2SL')}\n"
        m1 += f"• {INDICATORS['WTREGEN']['name']}: {get_fred_data(fred, 'WTREGEN')}\n"
        m1 += f"• {INDICATORS['RRPONTSYD']['name']}: {get_fred_data(fred, 'RRPONTSYD')}\n\n"
        m1 += f"• {INDICATORS['DPSACBW027SBOG']['name']}: {get_fred_data(fred, 'DPSACBW027SBOG')}\n"
        m1 += f"• {INDICATORS['TOTLL']['name']}: {get_fred_data(fred, 'TOTLL')}\n"
        send_msg(token, chat_id, m1)

        # Report 2
        m2 = f"📈 <b>Rates & Risk (금리 및 리스크)</b>\n<small>Date: {now}</small>\n\n"
        m2 += f"• {INDICATORS['IORB']['name']}: {get_fred_data(fred, 'IORB')}\n"
        m2 += f"• {INDICATORS['EFFR']['name']}: {get_fred_data(fred, 'EFFR')}\n"
        m2 += f"• {INDICATORS['SOFR']['name']}: {get_fred_data(fred, 'SOFR')}\n"
        m2 += f"• {INDICATORS['BAMLH0A0HYM2']['name']}: {get_fred_data(fred, 'BAMLH0A0HYM2')}\n"
        send_msg(token, chat_id, m2)
    except Exception as e:
        # 에러 발생 시 텔레그램으로 에러 내용 전송 (디버깅용)
        send_msg(os.environ['TELEGRAM_TOKEN'], os.environ['CHAT_ID'], f"❌ 시스템 에러 발생: {str(e)}")

if __name__ == "__main__":
    main()

