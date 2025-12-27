import os
import requests
from fredapi import Fred

def get_finance_data():
    # 저장해둔 GitHub Secrets에서 정보를 가져옵니다
    try:
        fred = Fred(api_key=os.environ['FRED_API_KEY'])
        token = os.environ['TELEGRAM_TOKEN']
        chat_id = os.environ['CHAT_ID']
        
        # FRED 지표 설정 (TGA, RRP, MMF)
        indicators = {
            'WTREGEN': '🏦 TGA 잔고',
            'RRPONTSYD': '🔄 역레포(RRP)',
            'WMMNS': '💰 MMF 규모'
        }
        
        msg_lines = ["📊 [데일리 유동성 변동 리포트]\n"]
        
        for ticker, name in indicators.items():
            series = fred.get_series(ticker)
            
            # 최신값과 전일값 추출
            today_val = series.iloc[-1]
            yesterday_val = series.iloc[-2]
            diff = today_val - yesterday_val
            
            # MMF는 단위가 커서 T(Trillion)로 변환, 나머지는 B(Billion)
            if ticker == 'WMMNS':
                today_val /= 1000000 
                yesterday_val /= 1000000
                diff /= 1000000
                unit = "T"
            else:
                unit = "B"
                
            sign = "+" if diff > 0 else ""
            line = f"{name}: {yesterday_val:,.1f}{unit} → {today_val:,.1f}{unit} ({sign}{diff:,.1f}{unit})"
            msg_lines.append(line)
        
        msg = "\n".join(msg_lines)
        msg += "\n\n※ 수치는 FRED 최신 업데이트 기준입니다."
        
        # 텔레그램 발송
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": msg})
        
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    get_finance_data()
