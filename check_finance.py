import os
import requests
from fredapi import Fred
from datetime import datetime

# ==========================================
# [설정] 지표별 원본 단위 및 변환 계수 검증 완료
# scale_div: 원본 데이터를 이 값으로 나누어야 목표 단위가 됨
# ==========================================
INDICATORS = {
    # 1. Liquidity & Money
    'WALCL': {
        'name': 'Fed Total Assets (연준총자산)', 
        'unit': 'T', 
        'scale_div': 1000000 # 원본 Million -> 목표 Trillion
    },
    'M2SL': {
        'name': 'M2 Money Stock (M2 통화량)', 
        'unit': 'T', 
        'scale_div': 1000    # 원본 Billion -> 목표 Trillion
    },
    'WTREGEN': {
        'name': 'TGA Balance (TGA 잔고)', 
        'unit': 'B', 
        'scale_div': 1000    # 원본 Million -> 목표 Billion
    },
    'RRPONTSYD': {
        'name': 'Reverse Repo (역레포 잔고)', 
        'unit': 'B', 
        'scale_div': 1       # 원본 Billion -> 목표 Billion (변환 없음)
    },
    
    # 2. Bank Loans & Deposits
    'DPSACBW027SBOG': {
        'name': 'Bank Deposits (은행 총예금)', 
        'unit': 'B', 
        'scale_div': 1       # 원본 Billion -> 목표 Billion (변환 없음)
    },
    'TOTLL': {
        'name': 'Bank Loans (은행 총대출)', 
        'unit': 'B', 
        'scale_div': 1       # 원본 Billion -> 목표 Billion (변환 없음)
    },
    
    # 3. Rates (Percent) - 변환 불필요
    'IORB': {'name': 'IORB (준비금이자)', 'unit': '%'},
    'EFFR': {'name': 'EFFR (실효연방금리)', 'unit': '%'},
    'SOFR': {'name': 'SOFR (담보금리)', 'unit': '%'},
    'BAMLH0A0HYM2': {'name': 'HY Spread (하이일드)', 'unit': '%'}
}

def get_fred_data(fred, ticker):
    """지표별 단위를 확인하여 포맷팅하는 함수"""
    try:
        config = INDICATORS.get(ticker)
        # FRED 데이터 호출 (날짜순 정렬 및 결측치 제거)
        series = fred.get_series(ticker).sort_index().dropna()
        
        if series.empty:
            return "No Data"

        # 최신 및 직전 데이터 추출
        curr_val = series.iloc[-1]
        prev_val = series.iloc[-2]
        
        # 날짜 포맷 (월/일)
        d_curr = series.index[-1].strftime('%m/%d')
        d_prev = series.index[-2].strftime('%m/%d')
        
        # 차이 계산
        diff = curr_val - prev_val
        unit = config['unit']

        # 단위 변환 로직 (Percent가 아닌 경우만 계산)
        if unit != "%":
            divisor = config['scale_div']
            curr_val /= divisor
            prev_val /= divisor
            diff /= divisor
            
            sign = "+" if diff >= 0 else ""
            return f"{prev_val:,.1f}{unit}({d_prev}) → {curr_val:,.1f}{unit}({d_curr}) <b>[{sign}{diff:,.1f}{unit}]</b>"
        
        else:
            # 금리(%) 처리
            sign = "+" if diff >= 0 else ""
            return f"{prev_val:.2f}%({d_prev}) → {curr_val:.2f}%({d_curr}) <b>[{sign}{diff:.2f}%]</b>"

    except Exception as e:
        return f"Error: {str(e)}"

def send_msg(token, chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id, 
            "text": text, 
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        requests.post(url, json=payload)
    except Exception as e:
        print(f"전송 실패: {e}")

def main():
    try:
        fred = Fred(api_key=os.environ['FRED_API_KEY'])
        token = os.environ['TELEGRAM_TOKEN']
        chat_id = os.environ['CHAT_ID']
        now = datetime.now().strftime('%m/%d %H:%M')

        # --- Report 1: Liquidity & Banking ---
        msg1 = f"💰 <b>Liquidity & Banking (유동성 및 은행)</b>\n"
        msg1 += f"<small>Date: {now}</small>\n\n"
        
        msg1 += "<b>[Liquidity & Money]</b>\n"
        msg1 += f"• {INDICATORS['WALCL']['name']}: {get_fred_data(fred, 'WALCL')}\n"
        msg1 += f"• {INDICATORS['M2SL']['name']}: {get_fred_data(fred, 'M2SL')}\n"
        msg1 += f"• {INDICATORS['WTREGEN']['name']}: {get_fred_data(fred, 'WTREGEN')}\n"
        msg1 += f"• {INDICATORS['RRPONTSYD']['name']}: {get_fred_data(fred, 'RRPONTSYD')}\n\n"
        
        msg1 += "<b>[Loans & Deposits]</b>\n"
        msg1 += f"• {INDICATORS['DPSACBW027SBOG']['name']}: {get_fred_data(fred, 'DPSACBW027SBOG')}\n"
        msg1 += f"• {INDICATORS['TOTLL']['name']}: {get_fred_data(fred, 'TOTLL')}\n"
        
        msg1 += "\n🔗 <a href='https://fred.stlouisfed.org/graph/?g=1yyY4'>[View Charts / 차트보기]</a>"
        send_msg(token, chat_id, msg1)

        # --- Report 2: Rates & Risk ---
        msg2 = f"📈 <b>Rates & Risk (금리 및 리스크)</b>\n"
        msg2 += f"<small>Date: {now}</small>\n\n"
        
        msg2 += f"• {INDICATORS['IORB']['name']}: {get_fred_data(fred, 'IORB')}\n"
        msg2 += f"• {INDICATORS['EFFR']['name']}: {get_fred_data(fred, 'EFFR')}\n"
        msg2 += f"• {INDICATORS['SOFR']['name']}: {get_fred_data(fred, 'SOFR')}\n"
        msg2 += f"• {INDICATORS['BAMLH0A0HYM2']['name']}: {get_fred_data(fred, 'BAMLH0A0HYM2')}\n"
        
        msg2 += "\n🔗 <a href='https://fred.stlouisfed.org/graph/?id=IORB,SOFR,EFFR'>[View Rates / 금리차트]</a>"
        send_msg(token, chat_id, msg2)

    except Exception as e:
        print(f"전체 실행 오류: {e}")

if __name__ == "__main__":
    main()
