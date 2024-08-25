import signal
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from bs4 import BeautifulSoup


## logger

import os
import time


#####
##### {현재시간}---{message}
#####
def logger(log_txt_path, message):
    # 현재 시간을 'YYYY-MM-DD HH:MM:SS' 형식으로 가져옴
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    # 로그 메시지를 "{현재시간}---{message}" 형식으로 생성
    log_message = f"{current_time}-----{message}\n"
    # 파일이 없으면 생성하고, 있으면 추가 모드로 열기
    with open(log_txt_path, 'a') as log_file:
        log_file.write(log_message)

# 전역 변수
car_name = None
df_post = None
df_comment = None

# 종료 시 호출될 핸들러
def handle_exit(signal, frame):
    print("Interrupted. Saving progress...")
    if df_post is not None:
        df_post.to_csv(f'{car_name}_post.csv', index=False)
    if df_comment is not None:
        df_comment.to_csv(f'{car_name}_comment.csv', index=False)
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)


#####
##### 댓글 추출 함수
#####

def sub_extract_comments(car_name, commentlistbox_outer_html, url):
    try:
        soup = BeautifulSoup(commentlistbox_outer_html, 'html.parser')
        comments = soup.select('ul.basiclist li')
        comment_list = []
        for comment in comments:
            try:
                date_str = comment.select_one('.date').text
                date = pd.to_datetime(date_str, format='%y.%m.%d %H:%M')
                content = comment.select_one('dd').text.strip()
                comment_list.append({'date': date, 'content': content})
            except:
                message = f"Error Occured in one comment ----- {url}"
                logger(f"{car_name}_crawler_log.txt", message)
                message = f"Skipping one ..."
                logger(f"{car_name}_crawler_log.txt", message)
                continue
        return comment_list 
    except Exception as e:
        message =  f"Comment extraction failed ----- {url}"
        logger(f'{car_name}_crawler_log.txt', f"Comment extraction failed: {str(e)}")
        message = f"ERROR: {str(e)}"
        logger(f'{car_name}_crawler_log.txt', message)
        return None

##### 게시글 추출 함수
def extract_post_contents(car_name, url, driver):
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        title = driver.find_element(By.XPATH, '/html/body/div[1]/div[6]/div/div/div[1]/div[3]/div[1]/div[1]/dl/dt/strong').text
        span_element = driver.find_element(By.XPATH, '/html/body/div[1]/div[6]/div/div/div[1]/div[3]/div[1]/div[1]/dl/dt/span')
        date_raw = span_element.text
        date_parts = date_raw.split(" ")
        date_str = date_parts[6] + " " + date_parts[8]
        date = pd.to_datetime(date_str, format="%Y.%m.%d %H:%M")
        view_count_raw = driver.find_element(By.XPATH, '/html/body/div[1]/div[6]/div/div/div[1]/div[3]/div[1]/div[1]/dl/dt/span/em[1]').text
        view_count = int(view_count_raw.replace(",", ""))
        content_element = driver.find_element(By.XPATH, '/html/body/div[1]/div[6]/div/div/div[1]/div[3]/div[1]/div[2]/div')
        content = content_element.text
        commentlistbox_outer_html = driver.find_element(By.XPATH, '/html/body/div[1]/div[6]/div/div/div[1]/div[9]/div').get_attribute('outerHTML')
        comment_list = sub_extract_comments(car_name, commentlistbox_outer_html, url)
        return {
            "url": url,
            "title": title,
            "date": date,
            "view_count": view_count,
            "content": content,
            "car": car_name,
            "defect_cause": None,
            "comment_list": comment_list
        }
    except Exception as e:
        message = f"Post extraction failed ----- {url}"
        logger(f'{car_name}_crawler_log.txt', message)
        return None



########## 2024.8.6 ----- 컬럼명 변경
def df_append(extraction_result, df_post, df_comment):
    if extraction_result is not None:
        post_data = {
            'URL': extraction_result['url'],
            'Title': extraction_result['title'],
            'DateTime': extraction_result['date'],
            'ViewCount': extraction_result['view_count'],
            'Content': extraction_result['content'],
            'CarName': extraction_result['car'],
            'DefectCause': extraction_result['defect_cause']
        }
        df_post.loc[len(df_post)] = post_data
        if extraction_result['comment_list'] is not None:
            for comment in extraction_result['comment_list']:
                comment_data = {
                    'URL': extraction_result['url'],
                    'DateTime': comment['date'],
                    'Content': comment['content'],
                    'DefectCause': extraction_result['defect_cause'],
                    'CarName': extraction_result['car']
                }
                df_comment.loc[len(df_comment)] = comment_data


##### 
##### extract_from_page
#####

def extract_from_page(car_name_input, start_line_num = 0):
    global car_name, df_post, df_comment
    car_name = car_name_input

    try:
        df_post = pd.read_csv(f"{car_name}_post.csv")
        df_comment = pd.read_csv(f"{car_name}_comment.csv")
    except FileNotFoundError:
        print('CSV files not found. Creating new ones...')
        df_post = pd.DataFrame(columns=['URL', 'Title', 'DateTime', 'ViewCount', 'Content', 'CarName', 'DefectCause'])
        df_comment = pd.DataFrame(columns=['URL', 'DateTime', 'Content', 'DefectCause', 'CarName'])

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    with open(f'{car_name}_post_url_log.txt', 'r') as file:
        lines = file.readlines()
    
    midterm_inspection_count = 0
    for idx, line in enumerate(lines):
        if idx < start_line_num:
            continue

        try:
            url = line.split('-----')[2]
            print(f"Now in line {idx} ----- url: {url}")
            try:
                extraction_result = extract_post_contents(car_name, url, driver)
                df_append(extraction_result, df_post, df_comment)
            except Exception as e:
                message = f"Post Extraction Failed ------ line {idx} ----- {url}"
                print(message)
                logger(f"{car_name}_crawler_log.txt", message)
                continue
        except Exception as e:
            message = f"Cannot read the line {idx} - line parsing: {str(e)}"
            print(message)
            logger(f"{car_name}_crawler_log.txt", message)
            continue

        if midterm_inspection_count % 100 == 0:
            print(f'----- midterm inspection ----- tail(3)')
            print(df_post.tail(3))
        midterm_inspection_count += 1

    try:
        df_post.to_csv(f'{car_name}_post.csv', index=False)
        df_comment.to_csv(f'{car_name}_comment.csv', index=False)
    except Exception as e:
        print(f"***** Failed to save CSV files: {str(e)}")

    print(f'{car_name}.csv saved')

    driver.quit()

if __name__ == "__main__":
    car_name_input = input('car_name_input: ')
    start_line_num = int(input('start_line_num: '))
    extract_from_page(car_name_input, start_line_num)