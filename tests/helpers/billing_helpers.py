"""
Billing 테스트를 위한 헬퍼 함수 모음
"""
import time
import os
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.common.exceptions import MoveTargetOutOfBoundsException

DEBUG_MODE = os.getenv('TEST_DEBUG', 'false').lower() == 'true'

# ======================
# ✅ 디버그/스크린샷 함수
# ======================

def debug_wait(driver, seconds=0.5):
    """디버그 모드에서만 대기"""
    if DEBUG_MODE:
        time.sleep(seconds)
        print(f"[DEBUG] {seconds}초 대기")

def _dump(name, driver):
    """페이지 소스와 스크린샷 저장"""
    path = os.path.join(os.getcwd(), name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    driver.save_screenshot(name.replace(".html", ".png"))
    print("디버그 저장:", path)


def _dump_on_fail(driver, name="credit_debug"):
    """테스트 실패 시 디버그 정보 저장"""
    try:
        driver.save_screenshot(f"{name}.png")
        with open(f"{name}.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
    except Exception:
        pass


# ======================
# ✅ 크레딧 관련 함수
# ======================

def _find_credit_btn(driver, wait):
    """크레딧 버튼 찾기"""
    # href 우선 + 아이콘 백업 셀렉터
    sel = "a[href$='/admin/org/billing/payments/credit'], a:has(svg[data-testid*='circle-c'])"
    return wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, sel)))


def _extract_amount(text):
    """
    'Credit ₩1,234,567' → 1234567
    텍스트에서 금액 숫자만 추출
    """
    text = text.replace("￦", "₩").replace(",", "")
    m = re.search(r"(\d+)", text)
    if not m:
        raise ValueError(f"금액 추출 실패: {text}")
    return int(m.group(1))


def _has_won_symbol(driver, el, raw_text: str, retry=3) -> bool:
    """
    요소에 원화 기호(₩)가 있는지 확인
    여러 번 시도해서 안정적으로 검증
    """
    for i in range(retry):
        # 텍스트 내 변환 문자 통합
        txt = (raw_text or "").replace("¥", "₩")
        if "₩" in txt:
            return True

        # 접근성/툴팁 속성
        for attr in ("aria-label", "title", "data-tooltip"):
            v = (el.get_attribute(attr) or "").replace("¥", "₩")
            if "₩" in v:
                return True

        # 의사요소 content 검사
        before = driver.execute_script("return getComputedStyle(arguments[0],'::before').content;", el) or ""
        after  = driver.execute_script("return getComputedStyle(arguments[0],'::after').content;", el) or ""
        before = before.replace("¥", "₩")
        after  = after.replace("¥", "₩")
        
        if ("₩" in before) or ("₩" in after):
            return True
        
        # 재시도 전 짧은 대기 (DOM 업데이트 시간)
        if i < retry - 1:
            WebDriverWait(driver, 0.3).until(lambda d: True)
    
    return False


# ======================
# ✅ CSS/스타일 관련 함수
# ======================

# 크레딧 버튼 hover 관련 CSS 속성들
PROPS = [
    "background-color",
    "color",
    "border-color",
    "box-shadow",
]


def _css(driver, el, prop):
    """요소의 CSS 속성값 가져오기"""
    return driver.execute_script("return window.getComputedStyle(arguments[0]).getPropertyValue(arguments[1]);", el, prop)


def _computed_bg(driver, el):
    """요소의 배경색 가져오기"""
    return driver.execute_script("return getComputedStyle(arguments[0]).backgroundColor;", el)


def _any_prop_changed(driver, el, before_props):
    """CSS 속성이 변경되었는지 확인"""
    after = {p: _css(driver, el, p) for p in PROPS}
    changed = any(before_props[p] != after[p] for p in PROPS)
    return changed, after


def _style_snapshot(driver, el):
    """요소의 스타일 스냅샷 생성"""
    props = [
        # 색/배경/선
        "background-color", "color", "border-color", "outline-color", "outline-width",
        # 효과
        "box-shadow", "text-shadow",
        # 테마가 자주 쓰는 값들
        "opacity", "filter", "backdrop-filter", "transform",
    ]
    snap = {p: _css(driver, el, p) for p in props}
    # 의사요소(오버레이)까지 확인
    snap["::before-bg"] = driver.execute_script("return getComputedStyle(arguments[0],'::before').backgroundColor;", el)
    snap["::after-bg"]  = driver.execute_script("return getComputedStyle(arguments[0],'::after').backgroundColor;", el)
    return snap


# ======================
# ✅ 마우스 인터랙션 함수
# ======================

def _hover(driver, el):
    """요소에 마우스 호버"""
    ActionChains(driver).move_to_element(el).perform()


def _hover_strong(driver, el):
    """강화된 마우스 호버 (스크롤 + 다중 시도)"""
    # 1) 뷰포트 중앙으로 스크롤
    driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'center'});", el)
    # 스크롤 완료 대기
    WebDriverWait(driver, 1).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

    # 2) 가장 안전한 방법: 요소로 직접 이동
    actions = ActionChains(driver)
    try:
        actions.move_to_element(el).perform()
    except MoveTargetOutOfBoundsException:
        # 일부 드라이버에서 요소 경계 계산이 어긋날 때 대비
        w = max(1, int(el.size.get("width", 2)) - 2)
        h = max(1, int(el.size.get("height", 2)) - 2)
        actions.move_to_element_with_offset(el, w//2, h//2).perform()

    # 3) JS 이벤트로 보강 (라이브러리 의존 UI에서 필요할 때가 있음)
    driver.execute_script("""
        const e = arguments[0];
        for (const type of ['mouseover','mouseenter']) {
            e.dispatchEvent(new MouseEvent(type, {bubbles:true, cancelable:true}));
        }
    """, el)


def _is_in_hover_chain(driver, el):
    """요소가 현재 hover 체인에 포함되어 있는지 확인"""
    # 현재 :hover 경로(루트→리프) 중에 el 또는 조상이 포함되면 True
    return driver.execute_script("""
        const hovered = document.querySelectorAll(':hover');
        return Array.from(hovered).some(h => h === arguments[0] || h.contains(arguments[0]));
    """, el) is True


# ======================
# ✅ 프로필/메뉴 관련 함수
# ======================

def _click_profile(driver, wait):
    """
    우상단 프로필 버튼 클릭
    헤더의 가장 오른쪽 버튼 선택 + 열린 메뉴 검증
    """
    # 1) 헤더 찾기
    header = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "header, [role='banner']")))

    # 2) 헤더 안에서 클릭 가능한 후보 수집
    candidates = header.find_elements(
        By.CSS_SELECTOR,
        "button, [role='button'], a[role='button']"
    )
    assert candidates, "헤더 내 클릭 가능한 버튼이 없음"

    # 3) 화면상 가장 오른쪽(x가 가장 큰) 요소 선택
    def rect_x(e):
        return driver.execute_script("return arguments[0].getBoundingClientRect().x;", e)

    # x가 큰 순서로 정렬하여 하나씩 시도 (툴팁 애니메이션/겹침 방지)
    candidates = sorted(candidates, key=rect_x, reverse=True)

    last_error = None
    for el in candidates[:4]:  # 상위 4개만 시도 (과도한 클릭 방지)
        try:
            wait.until(EC.element_to_be_clickable(el))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            el.click()
            
            # 드롭다운 메뉴가 나타날 때까지 대기
            WebDriverWait(driver, 2).until(
                lambda d: any(
                    f.is_displayed() 
                    for xp in ["//*[contains(text(),'Payment History') or contains(text(),'결제 내역')]"]
                    for f in d.find_elements(By.XPATH, xp)
                )
            )
            
            print("✅ 프로필 드롭다운 열림")
            return True
        except Exception as e:
            last_error = e
            continue

    raise Exception(f"프로필 버튼 클릭 실패 (우측 후보들 시도) : {last_error}")


def _logout(driver, wait):
    """로그아웃"""
    try:
        # 프로필 클릭
        _click_profile(driver, wait)
        
        # Logout 버튼이 클릭 가능할 때까지 대기
        logout_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), 'Logout') or contains(text(), '로그아웃')]")
        ))
        logout_btn.click()
        
        # 로그인 페이지 이동 확인
        wait.until(EC.url_contains("signin"))
        print("✅ 로그아웃 완료")
        
    except Exception as e:
        print(f"⚠️ UI 로그아웃 실패, 쿠키 삭제로 대체: {e}")
        driver.delete_all_cookies()
        driver.refresh()


def _open_payment_history(driver, wait):
    """프로필 → Payment History 클릭"""
    _click_profile(driver, wait)
    
    # Payment History 버튼이 클릭 가능할 때까지 대기
    payment_history = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//*[contains(text(), 'Payment History') or contains(text(), '결제 내역')]")
    ))
    payment_history.click()
    print("✅ Payment History 클릭")

