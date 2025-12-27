import os
import requests
from fredapi import Fred
from datetime import datetime

def get_finance_data():
    try:
        fred = Fred(api_key=os.environ['FRED_API_KEY'])
        token = os.environ['TELEGRAM_TOKEN']
        chat_id = os.environ['CHAT_ID']
        
        # 1. 지표 그룹 설정
        # 유동성 그룹
        liquidity = {
            'WALCL': '🏦 연준 총자산',
            'WTREGEN': '💰 TGA 잔고',
            'RRPONTSYD': '🔄 역레포(RRP)',
            'WRESBAL': '🏦 지급준비금'
        }
        # 실물경제 대출 현황 (신규 추가)
        bank_credit = {
            'TOTLL': '💳 상업은행 총대출'
        }
        # 금리 및 리스크 그룹 (%)
        rates_risk = {
            'SOFR': '📈 SOFR(담보금리)',
            'EFFR': '📉 EFFR(실효연방금리)',
            'IORB': '💵 IORB(준비금이자)',
            'BAMLH0A0HYM2': '⚠️ 하이일드 스프레드'
        }
        
        msg = f"📊 [데일리 금융지표 리포트] ({datetime.now().strftime('%m/%d')})\n"
        
        # 2. 유동성 데이터 처리
        msg += "\n💠 [유동성 현황 (B/T)]"
        for ticker, name in liquidity.items():
            series = fred.get_series(ticker).dropna()
            today_val = series.iloc[-1]
            yesterday_val = series.iloc[-2]
            diff = today_val - yesterday_val
            
            if ticker == 'WALCL':
                unit, factor = "T", 1000000
            else:
                unit, factor = "B", 1000
                
            today_val /= factor
            yesterday_val /= factor
            diff /= factor
            
            sign = "+" if diff > 0 else ""
            msg += f"\n• {name}: {today_val:,.1f}{unit} ({sign}{diff:,.1f}{unit})"

        # 3. 실물경제 대출 데이터 처리 (TOTLL)
        msg += "\n\n💠 [실물경제 대출현황 (B)]"
        for ticker, name in bank_credit.items():
            series = fred.get_series(ticker).dropna()
            today_val = series.iloc[-1] / 1000 # Billion 단위로 변환
            yesterday_val = series.iloc[-2] / 1000
            diff = today_val - yesterday_val
            
            sign = "+" if diff > 0 else ""
            msg += f"\n• {name}: {today_val:,.1f}B ({sign}{diff:,.1f}B)"

        # 4. 금리 및 리스크 데이터 처리
        msg += "\n\n💠 [금리 및 신용리스크 (%)]"
        for ticker, name in rates_risk.items():
            series = fred.get_series(ticker).dropna()
            today_val = series.iloc[-1]
            yesterday_val = series.iloc[-2]
            diff = today_val - yesterday_val
            
            sign = "+" if diff > 0 else ""
            msg += f"\n• {name}: {today_val:.2f}% ({sign}{diff:.2f}%)"
            
        msg += "\n\n※ FRED 최신 업데이트 기준"
        
        # 5. 텔레그램 발송
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": msg})
            
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    get_finance_data()
