import feedparser
import urllib.parse
import feedparser
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
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

def get_google_news_with_links(keyword, count=3):
    """종목별 뉴스 제목과 원본 링크를 함께 가져오기"""
    encoded_keyword = urllib.parse.quote(f"{keyword} 주식")
    rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
    
    feed = feedparser.parse(rss_url)
    news_items = []
    
    for entry in feed.entries[:count]:
        title = entry.title.split(" - ")[0] # 언론사명 제거
        link = entry.link                  # 원본 기사 링크
        # 엑셀에서 보기 좋게 "제목 (링크)" 형태로 합침
        news_items.append(f"{title}\n({link})")
        
    return news_items

def save_to_google_sheet(stock_data_list):
    print("\n[Step 3] 구글 시트 저장 시작...")
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)

        # 시트 열기 (본인의 시트 이름으로 수정)
        spreadsheet = client.open_by_key("1zBeoVfKZwP2_w71Fyd94mSFRyi6MO4rf7f_A_oUg2XY")
        
        today = datetime.now().strftime('%Y-%m-%d')
        try:
            worksheet = spreadsheet.add_worksheet(title=today, rows="100", cols="10")
            print(f" > 새 워크시트 생성 완료: {today}")
        except:
            worksheet = spreadsheet.worksheet(today)
            worksheet.clear()
            print(f" > 기존 워크시트 초기화 완료: {today}")

        # 헤더 및 데이터 쓰기
        headers = ["순위", "종목명", "최신뉴스 요약"]
        worksheet.append_row(headers)
        
        for item in stock_data_list:
            # 뉴스들 사이에 구분선을 넣어 가독성을 높임
            news_text = "\n\n".join(item['news']) 
            row = [item['rank'], item['name'], news_text]
            worksheet.append_row(row)
            print(f" > [{item['rank']}위] {item['name']} 저장 완료")

        print("✅ 모든 데이터가 구글 시트에 안전하게 기록되었습니다!")
    except Exception as e:
        print(f"❌ 시트 저장 중 에러 발생: {e}")

# --- 실제 연동 시 예시 데이터 ---
# stock_data_list = [
#     {"rank": 1, "name": "삼성전자", "code": "005930", "news": ["뉴스1", "뉴스2"]},
#     ...
# ]
# save_to_google_sheet(stock_data_list)

# --- 메인 실행 로직 수정 예시 ---
if __name__ == "__main__":
    top_stocks = get_top_10_stocks()
    
    all_data_for_gemini = ""  # 이건 Gemini용 (문자열)
    data_for_excel = []       # 이건 엑셀 저장용 (리스트)

    for i, name in enumerate(top_stocks, 1):
        # --- [수정 부분] RSS에서 제목과 링크를 모두 가져옵니다 ---
        encoded_keyword = urllib.parse.quote(f"{name} 주식")
        rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(rss_url)
        
        # 제목과 링크를 "제목 (링크)" 형태로 합친 리스트 생성
        news_list_with_links = []
        for entry in feed.entries[:3]: # 최신 뉴스 3개
            title = entry.title.split(" - ")[0] # 언론사명 제거
            link = entry.link
            news_list_with_links.append(f"{title}\n({link})")
        # --------------------------------------------------

        # 1. 엑셀 저장용 데이터 차곡차곡 쌓기
        stock_item = {
            "rank": i,
            "name": name,
            "code": "N/A", 
            "news": news_list_with_links # 링크가 포함된 리스트를 넣습니다.
        }
        data_for_excel.append(stock_item)

        # 2. Gemini용 텍스트 만들기 (분석용이므로 링크는 빼고 제목만 넣어도 충분합니다)
        titles_only = [n.split("\n")[0] for n in news_list_with_links]
        all_data_for_gemini += f"{i}위: {name}\n" + "\n".join(titles_only) + "\n\n"

        print(f" > {i}위 {name} 수집 완료 (뉴스 {len(news_list_with_links)}건)")

    # 3. 구글 시트 저장 함수 호출
    save_to_google_sheet(data_for_excel)
    
    print("\n✅ 모든 작업이 완료되었습니다. 구글 시트를 확인해 보세요!")

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