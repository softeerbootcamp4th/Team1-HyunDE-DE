import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from tempfile import mkdtemp
import json
import pandas as pd
from datetime import datetime, timedelta
import boto3
from dotenv import load_dotenv

def setup_selenium_driver():
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-tools")
    chrome_options.add_argument("--no-zygote")
    chrome_options.add_argument("--single-process")
    chrome_options.add_argument(f"--user-data-dir={mkdtemp()}")
    chrome_options.add_argument(f"--data-path={mkdtemp()}")
    chrome_options.add_argument(f"--disk-cache-dir={mkdtemp()}")
    chrome_options.add_argument("--remote-debugging-pipe")
    chrome_options.add_argument("--verbose")
    chrome_options.add_argument("--log-path=/tmp")
    chrome_options.binary_location = "/opt/chrome/chrome-linux64/chrome"

    service = Service(
        executable_path="/opt/chrome-driver/chromedriver-linux64/chromedriver",
        service_log_path="/tmp/chromedriver.log"
    )

    driver = webdriver.Chrome(
        service=service,
        options=chrome_options
    )

    return driver


def login_to_naver(driver, dotenv_path='login_info.env'):
    driver.get("naver_cafe_url")
    time.sleep(5)
    load_dotenv(dotenv_path=dotenv_path, verbose=True)
    login_id = os.getenv("NAVER_ID")
    login_pw = os.getenv("NAVER_PW")
    driver.execute_script(
        f"document.querySelector('input[id=\"id\"]').setAttribute('value', '{login_id}')"
    )
    time.sleep(2)
    driver.execute_script(
        f"document.querySelector('input[id=\"pw\"]').setAttribute('value', '{login_pw}')"
    )
    time.sleep(1)
    login_button = driver.find_element(By.ID, "log.login")
    login_button.click()
    time.sleep(10)  


def scrape_posts(driver):

    driver.get('naver_cafe_url')
    time.sleep(10)

    search_input = driver.find_element(By.ID, 'topLayerQueryInput')
    search_input.send_keys('결함')
    search_input.send_keys(Keys.ENTER)

    time.sleep(8)
    driver.switch_to.frame("cafe_main") 

    current_date = datetime.now().date()
    seven_days_ago = current_date - timedelta(days=7)

    num = 0
    post_date = []
    current_page = 1

    try:
        while True:
            WebDriverWait(driver, 25).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tbody > tr'))
            )
            
            posts = driver.find_elements(By.CSS_SELECTOR, 'tbody > tr')
            for post in posts:
                try:
                    date_text = post.find_element(By.CSS_SELECTOR, 'td.td_date').text
                    if ':' in date_text:
                        post_date_obj = current_date 
                    else:
                        post_date_obj = datetime.strptime(date_text, '%Y.%m.%d.').date()

                    if post_date_obj < seven_days_ago:
                        print("7일 전 날짜를 벗어난 게시물을 만나 크롤링을 중단합니다.")
                        raise Exception("날짜 범위 초과") 

                    if seven_days_ago <= post_date_obj <= current_date:
                        title = post.find_element(By.CSS_SELECTOR, 'a.article').text
                        link = post.find_element(By.CSS_SELECTOR, 'a.article').get_attribute('href')
                        views = post.find_element(By.CSS_SELECTOR, 'td.td_view').text
                        num += 1
                        post_date.append({
                            'Title': title,
                            'Date': str(post_date_obj),
                            'ViewCount': views,
                            'URL': link,
                            'CarName': '싼타페'
                        })
                except NoSuchElementException:
                    continue  

            page_buttons = driver.find_elements(By.CSS_SELECTOR, 'div.prev-next a')
            if current_page % 10 == 0: 
                for button in page_buttons:
                    if '다음' in button.text:
                        button.click()
                        current_page += 1
                        time.sleep(2)
                        break
            else:
                found_next_page = False
                for button in page_buttons:
                    if button.text.isdigit() and int(button.text) == current_page + 1:
                        button.click()
                        current_page += 1
                        time.sleep(2)
                        found_next_page = True
                        break
                if not found_next_page:
                    print("! 더 이상 페이지가 없음 !")
                    break

    except Exception as e:
        print(f"에러 발생: {e}")

    print(f'처리된 게시물 수: {num}')
    df_posts = pd.DataFrame(post_date)
    return df_posts


def scrape_content_and_comments(driver, df_posts):
    df_posts['DateTime'] = ""
    df_posts['Content'] = ""
    comments_list = []

    for index, row in df_posts.iterrows():
        try:
            driver.get(row['URL'])
            wait = WebDriverWait(driver, 20)
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, 'cafe_main')))

            date_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span.date')))
            print("날짜: ", date_element.text)

            content_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.se-main-container')))
            print("게시글 내용: ", content_element.text.strip())

            comment_elements = driver.find_elements(By.CSS_SELECTOR, 'div.comment_text_box span.text_comment')
            comment_date_elements = driver.find_elements(By.CSS_SELECTOR, 'span.comment_info_date')

            for comment, comment_date in zip(comment_elements, comment_date_elements):
                comments_list.append({
                    'URL': row['URL'], 
                    'CommentContent': comment.text.strip(),
                    'DateTime': comment_date.text.strip()
                })
                print("댓글 : ", comment.text.strip(), "댓글 날짜: ", comment_date.text.strip())

            df_posts.at[index, 'DateTime'] = date_element.text
            df_posts.at[index, 'Content'] = content_element.text.strip()

        except Exception as e:
            print(f"오류 발생: {e}")

    df_comments = pd.DataFrame(comments_list)
    return df_posts, df_comments


def save_dataframes_to_s3(df_posts, df_comments, bucket_name, target_folder):
    df_posts = df_posts.drop('Date',axis=1)
    df_posts['DefectID']= None
    df_posts['Sentiment']=None
    df_comments['DefectID'] = None
    df_comments['Sentiment'] = None

    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

    file_name_posts = f'santafe_post_{current_time}.csv'
    file_name_comments = f'santafe_comment_{current_time}.csv'

    tmp_path_posts = f'/tmp/{file_name_posts}'
    tmp_path_comments = f'/tmp/{file_name_comments}'
    df_posts.to_csv(tmp_path_posts, index=False, encoding='utf-8-sig')
    df_comments.to_csv(tmp_path_comments, index=False, encoding='utf-8-sig')

    s3_resource = boto3.resource('s3')
    s3_resource.Bucket(bucket_name).upload_file(tmp_path_posts, f'{target_folder}{file_name_posts}')
    s3_resource.Bucket(bucket_name).upload_file(tmp_path_comments, f'{target_folder}{file_name_comments}')


def lambda_handler(event, context):
    driver = setup_selenium_driver()

    try:
        login_to_naver(driver)
        df_posts = scrape_posts(driver)
        df_posts, df_comments = scrape_content_and_comments(driver, df_posts)

        # S3에 데이터 저장
        bucket_name = 'your bucket name' 
        target_folder = 'your target folder'
        save_dataframes_to_s3(df_posts, df_comments, bucket_name, target_folder)

    finally:
        driver.quit()

    return {
        'statusCode': 200,
        'body': json.dumps('Data scraped and saved successfully!')
    }
