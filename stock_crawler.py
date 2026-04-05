from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
import time

def get_top_10_stocks():
    """네이버 증권에서 거래상위 10개 종목명과 코드를 가져옴"""
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    url = "https://finance.naver.com/sise/sise_quant.naver"
    driver.get(url)
    time.sleep(1) # 로딩 대기

    # 종목명 요소 찾기 (class='tltle')
    stock_elements = driver.find_elements(By.CLASS_NAME, "tltle")
    
    top_10 = []
    for s in stock_elements[:10]:
        name = s.text
        code = s.get_attribute("href").split("code=")[1]
        top_10.append({"name": name, "code": code})
    
    driver.quit()
    return top_10

def get_stock_news(stock_name, count=3):
    """특정 종목의 최신 뉴스 제목을 BeautifulSoup으로 수집"""
    # 네이버 뉴스 검색결과 URL (정렬: 최신순)
    search_url = f"https://search.naver.com/search.naver?where=news&query={stock_name}&sort=1"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    res = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # 뉴스 제목 요소 선택 (네이버 검색 결과 기준)
    news_titles = soup.select('a.news_tit')
    
    results = []
    for title in news_titles[:count]:
        results.append(title.get_text())
    return results

# --- 메인 실행 로직 ---
if __name__ == "__main__":
    print("🚀 네이버 증권 거래상위 10개 종목 분석 중...")
    stocks = get_top_10_stocks()
    
    final_report = []

    for idx, stock in enumerate(stocks, 1):
        print(f"[{idx}/10] {stock['name']}({stock['code']}) 뉴스 수집 중...")
        news = get_stock_news(stock['name'])
        
        # 데이터 정리
        stock_info = {
            "rank": idx,
            "name": stock['name'],
            "news": news
        }
        final_report.append(stock_info)
        time.sleep(0.5) # 서버 부하 방지용 짧은 휴식

    # --- 결과 출력 ---
    print("\n" + "="*50)
    print("📊 종목별 최신 뉴스 요약")
    print("="*50)
    for item in final_report:
        print(f"{item['rank']}위: {item['name']}")
        for n in item['news']:
            print(f"   - {n}")
        print("-" * 30)