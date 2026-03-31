from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# 브라우저 꺼짐 방지 옵션
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)

# 드라이버 설정 (경로 입력 없이 바로 실행 가능!)
driver = webdriver.Chrome(options=chrome_options)

# 테스트 실행
driver.get("https://www.google.com")
print(driver.title)