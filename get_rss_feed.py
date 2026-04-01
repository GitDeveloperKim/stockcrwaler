import feedparser
from bs4 import BeautifulSoup
import requests


def get_stock_news_rss(keyword):
    # 구글 뉴스 RSS URL (삼성전자 등 종목명으로 검색 가능)
    rss_url = f"https://news.google.com/rss/search?q={keyword}&hl=ko&gl=KR&ceid=KR:ko"

    # RSS 파싱
    feed = feedparser.parse(rss_url)

    news_results = []

    # 최근 뉴스 5개만 추출
    for entry in feed.entries[:5]:
        title = entry.title
        link = entry.link
        pub_date = entry.published

        # RSS는 본문 전체를 주지 않는 경우가 많으므로, 필요시 링크 접속해서 본문 파싱
        # 여기서는 제목과 요약 정보를 LLM에 넘길 준비만 함
        news_results.append({
            'title': title,
            'link': link,
            'date': pub_date
        })

    return news_results


# 실행 및 출력
keyword = "삼성전자"
news_data = get_stock_news_rss(keyword)

for i, news in enumerate(news_data, 1):
    print(f"[{i}] {news['title']}")
    print(f"   날짜: {news['date']}")
    print(f"   링크: {news['link']}\n")