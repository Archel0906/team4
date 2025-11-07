import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

@pytest.fixture(scope="session")
def driver():
    print("브라우저 실행 중...")
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")  # 창 최대화
    options.add_argument("--disable-notifications")  # 알림 차단
    driver = webdriver.Chrome(service=service, options=options)
    yield driver
    driver.quit()


@pytest.fixture(scope="session")
# 드라이버 세팅 (Chrome) 

def driver():
    print("브라우저 실행 중...")
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")  # 창 최대화
    options.add_argument("--disable-popup-blocking")  # 팝업 차단 비활성화

    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(10)  # 대기 (요소 기다림)
    yield driver
    print("브라우저 종료 중...")
    driver.quit()

@pytest.fixture
def login(driver):
    pass  # 로그인 과정이 필요 없다면 pass 가능

# 작성자: 김은아(11/07)

