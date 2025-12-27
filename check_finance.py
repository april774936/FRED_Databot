import os
import requests
from fredapi import Fred
from datetime import datetime

def get_data_info(fred, ticker, unit_type="B"):
    """FRED에서 데이터를 가져와 포맷팅하는 함수"""
    try:
        series = fred.get_series(ticker).dropna()
        if series.empty:
            return None
        
        curr_val = series.iloc[-1]
        prev_val = series.iloc[-2]
        last_date = series.index[-1].strftime('%m/%d')
        diff = curr_val - prev_val
        
        # 단위 변환 (T: Trillion, B: Billion, %: Percent)
        if unit_type == "T":
            curr_val /= 1000000
            prev_val /= 1000000
            diff /= 1000000
            unit = "T"
        elif unit_type == "B":
            # FRED의 많은 데이터는 Million 단위로 제공되므로 Billion으로 변환
            curr_val /= 1000
            prev_val /= 1000
            diff /= 1000
            unit = "B"
        else:
            unit = "%"
            
        sign = "+" if diff >= 0 else ""
        
        if unit == "%":
            return f"{prev_val:.2f}% → {curr_val:.2f}% ({sign}{diff:.2f}%), ({last_date})"
        else:
            return f"{prev_val:,.1f}{unit} → {curr_val:,.1f}{unit} ({sign}{diff:,.1f}{unit}), ({last_date})"
    except:
        return "데이터 불러오기 실패"

def send_telegram(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})

def main():
    fred = Fred(api_key=os.environ['FRED_API_KEY'])
    token = os.environ['TELEGRAM_TOKEN']
    chat_id = os.environ['CHAT_ID']
    
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')

    # --- 리포트 1: 거시 유동성 및 통화량 ---
    msg1 = f"<b>[1. 거시 유동성 및 통화량]</b>\n(업데이트: {now_str})\n\n"
    msg1 += f"• 연준 총자산 (WALCL): {get_data_info(fred, 'WALCL', 'T')}\n"
    msg1 += f"• M2 통화량 (M2SL): {get_data_info(fred, 'M2SL', 'B')}\n"
    msg1 += f"• TGA 잔고 (WTREGEN): {get_data_info(fred, 'WTREGEN', 'B')}\n"
    msg1 += f"• 역레포 잔액 (RRPONTSYD): {get_data_info(fred, 'RRPONTSYD', 'B')}\n"
    msg1 += f"• 지급준비금 (WRESBAL): {get_data_info(fred, 'WRESBAL', 'B')}\n"
    send_telegram(token, chat_id, msg1)

    # --- 리포트 2: 금리 체계 및 리스크 ---
    # RRP 금리는 RRPONTSYAWARD 티커 사용
    msg2 = f"<b>[2. 금리 체계 및 신용 리스크]</b>\n\n"
    msg2 += f"• IORB (준비금이자): {get_data_info(fred, 'IORB', '%')}\n"
    msg2 += f"• EFFR (실효연방금리): {get_data_info(fred, 'EFFR', '%')}\n"
    msg2 += f"• SOFR (담보금리): {get_data_info(fred, 'SOFR', '%')}\n"
    msg2 += f"• RRP 금리 (역레포금리): {get_data_info(fred, 'RRPONTSYAWARD', '%')}\n"
    msg2 += f"• 하이일드 스프레드: {get_data_info(fred, 'BAMLH0A0HYM2', '%')}\n"
    send_telegram(token, chat_id, msg2)

    # --- 리포트 3: 은행 및 민간 대출 상태 ---
    msg3 = f"<b>[3. 은행 및 민간 대출 현황]</b>\n\n"
    msg3 += f"• 상업은행 총 예금 (DPSACBW027SBOG): {get_data_info(fred, 'DPSACBW027SBOG', 'B')}\n"
    msg3 += f"• 상업은행 총 대출 (TOTLL): {get_data_info(fred, 'TOTLL', 'B')}\n"
    msg3 += f"• 민간 부문 대출 (USLPS): {get_data_info(fred, 'USLPS', 'B')}\n"
    msg3 += "\n※ USLPS는 업데이트 주기가 길 수 있습니다."
    send_telegram(token, chat_id, msg3)

if __name__ == "__main__":
    main()
