import feedparser
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import urllib.parse

def get_top_10_stocks():
    """네이버 증권에서 거래상위 10개 종목명 가져오기 (Selenium)"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless') # 창 안 띄우기 (속도 향상)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    url = "https://finance.naver.com/sise/sise_quant.naver"
    driver.get(url)
    time.sleep(2)

    stock_elements = driver.find_elements(By.CLASS_NAME, "tltle")
    top_10_names = [s.text for s in stock_elements[:10]]
    
    driver.quit()
    return top_10_names

def get_google_news_rss(keyword, count=3):
    """구글 뉴스 RSS를 통해 종목별 최신 뉴스 추출"""
    # 검색어 인코딩 (한글 깨짐 방지)
    encoded_keyword = urllib.parse.quote(f"{keyword} 주식")
    rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
    
    feed = feedparser.parse(rss_url)
    news_items = []
    
    for entry in feed.entries[:count]:
        # 제목에서 언론사명 제거 (보통 ' - 언론사' 형태로 붙음)
        clean_title = entry.title.split(" - ")[0]
        news_items.append(clean_title)
        
    return news_items

# --- 메인 실행 로직 ---
if __name__ == "__main__":
    print("📈 실시간 거래 상위 종목 및 뉴스 수집 시작...")
    
    # 1. 종목 리스트 가져오기
    top_stocks = get_top_10_stocks()
    
    all_data_for_gemini = "" # Gemini에게 던질 텍스트 뭉치

    print("\n--- 수집 결과 ---")
    for i, name in enumerate(top_stocks, 1):
        news_list = get_google_news_rss(name)
        
        stock_report = f"{i}위: {name}\n"
        for title in news_list:
            stock_report += f"  - {title}\n"
        
        print(stock_report)
        all_data_for_gemini += stock_report + "\n"

    # 2. 여기서 Gemini API 연동 (예시)
    """
    from google import genai
    client = genai.Client(api_key="YOUR_API_KEY")
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=f"다음은 오늘 거래량이 급증한 종목들과 관련 뉴스입니다. 시장의 주요 테마를 분석해주세요:\n\n{all_data_for_gemini}"
    )
    print("🤖 Gemini 분석 리포트:")
    print(response.text)
    """