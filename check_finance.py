import os
import requests
from fredapi import Fred
from datetime import datetime

def get_info(fred, ticker, unit_type="B"):
    try:
        s = fred.get_series(ticker).dropna()
        curr, prev = s.iloc[-1], s.iloc[-2]
        d_curr, d_prev = s.index[-1].strftime('%m/%d'), s.index[-2].strftime('%m/%d')
        diff = curr - prev
        
        if unit_type == "T": curr, prev, diff, unit = curr/1e6, prev/1e6, diff/1e6, "T"
        elif unit_type == "B": curr, prev, diff, unit = curr/1e3, prev/1e3, diff/1e3, "B"
        else: unit = "%"
            
        sign = "+" if diff >= 0 else ""
        res = f"{prev:,.1f}{unit}({d_prev}) → {curr:,.1f}{unit}({d_curr}) <b>[{sign}{diff:,.1f}{unit}]</b>"
        if unit == "%":
            res = f"{prev:.2f}%({d_prev}) → {curr:.2f}%({d_curr}) <b>[{sign}{diff:.2f}%]</b>"
        return res
    except: return "N/A"

def send_msg(token, chat_id, text):
    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                  json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})

def main():
    fred = Fred(api_key=os.environ['FRED_API_KEY'])
    token, chat_id = os.environ['TELEGRAM_TOKEN'], os.environ['CHAT_ID']
    now = datetime.now().strftime('%m/%d %H:%M')
    
    # --- 첫 번째 메시지: 유동성, 통화량 및 대출/예금 ---
    report1 = f"💰 <b>유동성 및 금융 시스템 ({now})</b>\n\n"
    report1 += "<b>[유동성/통화량]</b>\n"
    report1 += f"• 연준자산: {get_info(fred, 'WALCL', 'T')}\n"
    report1 += f"• M2 통화: {get_info(fred, 'M2SL', 'B')}\n"
    report1 += f"• TGA잔고: {get_info(fred, 'WTREGEN', 'B')}\n"
    report1 += f"• 역레포: {get_info(fred, 'RRPONTSYD', 'B')}\n\n"
    
    report1 += "<b>[은행 대출/예금]</b>\n"
    report1 += f"• 은행예금: {get_info(fred, 'DPSACBW027SBOG', 'B')}\n"
    report1 += f"• 은행대출: {get_info(fred, 'TOTLL', 'B')}"
    
    send_msg(token, chat_id, report1)

    # --- 두 번째 메시지: 금리 및 리스크 ---
    report2 = f"📈 <b>금리 및 신용 리스크 ({now})</b>\n\n"
    report2 += f"• IORB: {get_info(fred, 'IORB', '%')}\n"
    report2 += f"• EFFR: {get_info(fred, 'EFFR', '%')}\n"
    report2 += f"• SOFR: {get_info(fred, 'SOFR', '%')}\n"
    report2 += f"• HY스프레드: {get_info(fred, 'BAMLH0A0HYM2', '%')}"
    
    send_msg(token, chat_id, report2)

if __name__ == "__main__":
    main()
