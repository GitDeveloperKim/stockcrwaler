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
    """네이버 증권에서 이름과 종목 코드를 함께 추출"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    url = "https://finance.naver.com/sise/sise_quant.naver"
    driver.get(url)
    time.sleep(2)

    # 종목명이 들어있는 a 태그들을 찾습니다.
    stock_elements = driver.find_elements(By.CLASS_NAME, "tltle")
    
    top_10_info = []
    for s in stock_elements[:10]:
        name = s.text
        # href 속성값 예: "/item/main.naver?code=005930"
        link = s.get_attribute('href')
        code = link.split('code=')[-1] # 'code=' 뒷부분만 잘라냄
        
        top_10_info.append({'name': name, 'code': code})
    
    driver.quit()
    return top_10_info

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
        # 헤더 수정 (뉴스 1, 2, 3 열 생성)
        headers = ["순위", "종목명", "종목코드", "뉴스 1", "뉴스 2", "뉴스 3"]
        worksheet.append_row(headers)

        for item in stock_data_list:
            # [순위, 종목명] + [뉴스1, 뉴스2, 뉴스3] 리스트를 합칩니다.
            row = [item['rank'], item['name'], item['code']] + item['news_columns']
            
            # [중요] value_input_option='USER_ENTERED'가 있어야 클릭 가능한 링크가 됩니다!
            worksheet.append_row(row, value_input_option='USER_ENTERED')
            print(f" > [{item['rank']}위] {item['name']} 저장 완료 (뉴스 3개 열 분리)")

        print("✅ 3개 열에 뉴스 링크 저장이 완료되었습니다!")

    except Exception as e:
        print(f"❌ 시트 저장 중 에러 발생: {e}")

# --- 실제 연동 시 예시 데이터 ---
# stock_data_list = [
#     {"rank": 1, "name": "삼성전자", "code": "005930", "news": ["뉴스1", "뉴스2"]},
#     ...
# ]
# save_to_google_sheet(stock_data_list)

if __name__ == "__main__":
    # 1. 이제 이름과 코드가 담긴 리스트를 받습니다.
    top_stocks_info = get_top_10_stocks()
    
    data_for_excel = []

    for i, stock in enumerate(top_stocks_info, 1):
        name = stock['name']
        code = stock['code']
        
        # 구글 뉴스 RSS 수집 부분 (기존과 동일)
        encoded_keyword = urllib.parse.quote(f"{name} 주식")
        rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(rss_url)
        
        news_links = []
        for entry in feed.entries[:3]:
            title = entry.title.split(" - ")[0].replace('"', '""')
            formula = f'=HYPERLINK("{entry.link}", "{title}")'
            news_links.append(formula)
        
        while len(news_links) < 3:
            news_links.append("")

        # 엑셀 데이터 구성 (코드 열 추가)
        data_for_excel.append({
            "rank": i,
            "name": name,
            "code": code, # <--- 수집한 코드 삽입
            "news_columns": news_links
        })
        print(f" > {i}위 {name}({code}) 데이터 준비 완료")

    # 3. 엑셀 저장 함수 호출 (헤더에 '코드' 추가 확인)
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