import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

##### logger
def logger(log_txt_path, message):
    # 현재 시간을 'YYYY-MM-DD HH:MM:SS' 형식으로 가져옴
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    # 로그 메시지를 "{현재시간}---{message}" 형식으로 생성
    log_message = f"{current_time}-----{message}\n"
    # 파일이 없으면 생성하고, 있으면 추가 모드로 열기
    with open(log_txt_path, 'a') as log_file:
        log_file.write(log_message)


#####
def post_searcher(start_page_num, car_name):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 브라우저 창을 열지 않음
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.get("https://www.bobaedream.co.kr")

    # 페이지의 body 태그가 로드될 때까지 대기
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # JavaScript를 사용하여 검색어 설정
    driver.execute_script(f"document.querySelector('#keyword').value = '{car_name}';")

    # 폼 제출
    driver.execute_script("document.search_form.submit();")

    # 검색 결과가 로드될 때까지 대기
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "a.more[href^=\"javascript:s_go('community','ALL');\"]"))
    )

    # 결과 더보기 클릭
    driver.find_element(By.CSS_SELECTOR, 'a.more[href^="javascript:s_go(\'community\',\'ALL\');"]').click()

    page_count = start_page_num

    while True:
        try:
            print(f'------- Now on page {page_count} --------')
            # 페이지의 li 태그가 로드될 때까지 대기
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, '/html/body/div/div[3]/div[2]/div/ul/li'))
            )

            # /html/body/div/div[3]/div[2]/div/ul/li[1]/dl/dt/a 여기 href주소를 프린트
            links = driver.find_elements(By.XPATH, '/html/body/div/div[3]/div[2]/div/ul/li/dl/dt/a')

            if not links:
                break

            for link in links:
                url = link.get_attribute('href')
                logger(f'{car_name}_post_url_log.txt', f'{page_count}-----{url}')

            page_count += 1
            s_go_js = f"javascript:s_go('community', 'ALL', {page_count});"
            driver.execute_script(s_go_js)

            # 페이지 로드 대기
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '/html/body/div/div[3]/div[2]/div/ul/li'))
            )

        except:
            print(f"Error occurred.(or Page Done.)")
            break

    driver.quit()


if __name__ == "__main__":
    start_page_num = int(input("start_page_num: "))
    car_name = input("car_name: ")
    post_searcher(start_page_num, car_name)