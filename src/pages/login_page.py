from selenium.webdriver.common.by import By
from .base_page import BasePage

class LoginPage(BasePage):

    # 로그인 화면 요소 정의
    USERNAME_INPUT = (By.NAME, "loginId")  # 사용자 이름 입력창. username 이 부분 웹 페이지 개발자 모드 상 이름 찾아야 함
    PASSWORD_INPUT = (By.NAME, "password")  # 비밀번호 입력창. 개발자모드 내 이름 찾기
    LOGIN_BUTTON = (By.XPATH, "//button[contains(text(), 'Login')]")  # 로그인 버튼. 이름 변경 필요

    # 로그인 기능 함수
    def login(self, username, password):
        
        # 아이디, 비밀번호 입력 후 로그인 버튼 클릭
        self.type(self.USERNAME_INPUT, username)  # 아이디 입력
        self.type(self.PASSWORD_INPUT, password)  # 비밀번호 입력
        self.click(self.LOGIN_BUTTON)              # 로그인 버튼 클릭

# 11/10 김은아 작성