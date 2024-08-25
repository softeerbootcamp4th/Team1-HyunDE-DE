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
from bs4 import BeautifulSoup


##### logger
def logger(log_txt_path, message):
    # 현재 시간을 'YYYY-MM-DD HH:MM:SS' 형식으로 가져옴
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    # 로그 메시지를 "{현재시간}---{message}" 형식으로 생성
    log_message = f"{current_time}-----{message}\n"
    # 파일이 없으면 생성하고, 있으면 추가 모드로 열기
    with open(log_txt_path, 'a') as log_file:
        log_file.write(log_message)


# 자동차갤
def dc_post_searcher(start_page_num):

    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 브라우저 창을 열지 않음
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    for now_page_num in range(start_page_num, 600):
    
        post_list_url = f"https://gall.dcinside.com/board/lists/?id=car_new1&page={now_page_num}&exception_mode=recommend"
        
        driver.get(post_list_url)

        # body 태그가 보일 때까지 기다림
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        if driver.current_url != post_list_url:
            print(driver.current_url)
            print("done!")
            break

        # body 태그가 있긴한데, 안에 빈 내용이 들어있을 수 있음 
        body_element = driver.find_element(By.TAG_NAME, "body")
        
        # body 태그 안의 내용이 비어있는지 확인하고, 비어있다면 새로고침 반복
        refresh_count = 0
        skip_flag = False

        while not body_element.text.strip():
            driver.refresh()
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            body_element = driver.find_element(By.TAG_NAME, "body")

            if refresh_count > 3:
                message = f"page fault-----{now_page_num}"
                logger("post_searcher_log.txt", message)
                print(message)
                skip_flag = True
                break    

        if skip_flag == True:
            continue
    
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # class="ub-content us-post"인 컴포넌트가 여러 개 있음
        posts = soup.select('tbody .ub-content.us-post')
        
        # 각 게시물에 대해 href 추출 및 출력
        for post in posts:
            # 그 안에 class="gall_tit ub-word"가 하나 있음
            title_element = post.select_one('.gall_tit.ub-word')
            if title_element:
                # 그 안에 a 태그가 두 개 있는데, 그 중 첫 번째 태그의 href에 있는 주소를 프린트
                a_tag = title_element.find_all('a')[0]
                post_url = a_tag['href']
                message = f'page{now_page_num}-----{post_url}'
                logger("post_urls_log.txt", message)
            
    message = "Post List Error.(or Done.)"
    print(message)
    logger("post_searcher_log.txt", message)
    driver.quit()

if __name__ == "__main__":
    dc_post_searcher(1)
