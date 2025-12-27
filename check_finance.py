import os
import requests
from fredapi import Fred

def get_finance_data():
    try:
        fred = Fred(api_key=os.environ['FRED_API_KEY'])
        token = os.environ['TELEGRAM_TOKEN']
        chat_id = os.environ['CHAT_ID']
        
        # 지표 설정 (가장 안정적인 티커로 변경)
        # WALCL: 연준 총자산 (유동성 확인용 추가)
        # RRPONTSYD: 역레포 (가장 정확한 일간 데이터)
        # WTREGEN: 재무부 일반계정(TGA)
        indicators = {
            'WTREGEN': '🏦 TGA 잔고',
            'RRPONTSYD': '🔄 역레포(RRP)'
        }
        
        msg_lines = ["📊 [데일리 유동성 변동 리포트]\n"]
        
        for ticker, name in indicators.items():
            series = fred.get_series(ticker)
            
            # 최신값과 전일값 추출 (데이터가 없는 날을 대비해 마지막 2개 추출)
            valid_data = series.dropna() # 값이 없는 날짜 제외
            today_val = valid_data.iloc[-1]
            yesterday_val = valid_data.iloc[-2]
            diff = today_val - yesterday_val
            
            unit = "B"
            sign = "+" if diff > 0 else ""
            line = f"{name}: {yesterday_val:,.1f}{unit} → {today_val:,.1f}{unit} ({sign}{diff:,.1f}{unit})"
            msg_lines.append(line)
        
        msg = "\n".join(msg_lines)
        msg += f"\n\n기준일: {valid_data.index[-1].strftime('%Y-%m-%d')}"
        
        # 텔레그램 발송
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        response = requests.post(url, json={"chat_id": chat_id, "text": msg})
        
        # 텔레그램 자체 에러 확인용 (로그에 찍힘)
        if response.status_code != 200:
            print(f"텔레그램 전송 실패: {response.text}")
            
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    get_finance_data()
