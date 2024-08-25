from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dagrun_operator import TriggerDagRunOperator
from datetime import datetime, timedelta
import pendulum
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import random
import time
from selenium.common.exceptions import TimeoutException
import boto3
from io import BytesIO
from kafka import KafkaProducer
import json

# 한국 시간대 설정
kst = pendulum.timezone('Asia/Seoul')

# DAG 설정
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 8, 19, tzinfo=kst),  # 시작 날짜 설정
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'dcinside_scraper_tucson', ############ ############ ############ ############ ############ ############ ############ ############ ############ 바꿀 곳
    default_args=default_args,
    description='DCInside scraper DAG (tucson)',
    schedule_interval='0 */3 * * *',  # 매 3시간마다 실행
    catchup=False,
    max_active_runs=1,
    tags=['scraper'],
)

def scrape_dcinside_tucson():
    # ChromeDriver 경로 설정
    service = Service(executable_path='/usr/bin/chromedriver')

    # Chrome WebDriver 초기화
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(service=service, options=options)

    driver.set_page_load_timeout(10)

    # 페이지 이동 함수
    def move_date(wait, driver, date):
        fast_move = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "btn_grey_roundbg.btn_schmove"))
        )
        fast_move.click()
        time.sleep(1)

        input_element = wait.until(EC.presence_of_element_located((By.ID, "calendarInput")))
        driver.execute_script("arguments[0].removeAttribute('readonly');", input_element)
        input_element.clear()
        input_element.send_keys(date)

        button_path = "/html/body/div[2]/div[3]/main/section[1]/article[2]/div[4]/div[3]/div/div[2]/div[2]/button"
        button = wait.until(EC.element_to_be_clickable((By.XPATH, button_path)))
        button.click()
        time.sleep(1)

    keyword = "투싼" ############ ############ ############ ############ ############ ############ ############ ############ ############ 바꿀 곳
    base_url = f"https://gall.dcinside.com/board/lists/?id=car_new1&s_type=search_subject_memo&s_keyword={keyword}"

    try:
        driver.get(base_url)
        WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.TAG_NAME, "a"))
        )
    except TimeoutException:
        logging.info("Page Loading Failed in 3 sec, Next step ...")

    start_time = pd.to_datetime(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    wait = WebDriverWait(driver, 10)
    past_date = start_time - pd.Timedelta(days=7)
    past_date_str = past_date.strftime("%Y-%m-%d")

    start_pos = None
    try:
        source = BeautifulSoup(driver.page_source, 'html.parser')
        for ele in source.find("a", "search_next")['href'].split('&'):
            if ele.startswith("search_pos"):
                start_pos = int(ele.split('=')[1]) - 10000
    except:
        logging.info("다음 검색 찾을 수 없음")

    move_date(wait, driver, past_date_str)
    past_pos = None
    try:
        source = BeautifulSoup(driver.page_source, 'html.parser')
        for ele in source.find("a", "search_next")['href'].split('&'):
            if ele.startswith("search_pos"):
                past_pos = int(ele.split('=')[1]) - 10000
    except:
        logging.info("다음 검색 찾을 수 없음")

    now_pos = start_pos
    post_urls = []
    while past_pos > now_pos:
        target_page = f"https://gall.dcinside.com/board/lists/?id=car_new1&search_pos={now_pos}&s_type=search_subject_memo&s_keyword={keyword}"
        pages = []
        try:
            page_component = source.find("div", "bottom_paging_box iconpaging")
            for ele in page_component.find_all():
                try:
                    pages.append(int(ele.text))
                except:
                    pass
        except:
            logging.info("페이지 탐색 불가")
        logging.info(f'#####################-----pos:{now_pos}, pages: {pages}')
        logging.info(f"############# 페이지 탐색")
        for page in pages:
            logging.info(f'-----now_pos: {now_pos}, now_page: {page}')
            target_page = f"https://gall.dcinside.com/board/lists/?id=car_new1&page={page}&search_pos={now_pos}&s_type=search_subject_memo&s_keyword={keyword}"
            try:
                logging.info(f'-----{target_page}')
                driver.get(target_page)
                WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.TAG_NAME, "a"))
                )
            except TimeoutException:
                logging.info("Page Loading Failed in 3 sec, Next step ...")
            source = BeautifulSoup(driver.page_source, 'html.parser')
            post_components = source.find_all("tr", "ub-content us-post")
            for post_component in post_components:
                post_urls.append("https://gall.dcinside.com"+post_component.find("a")['href'])
        now_pos += 10000

    post_urls = list(set(post_urls))
    df_post = pd.DataFrame(columns=['URL', 'Title', 'DateTime', 'ViewCount', 'Content', 'CarName', 'DefectID'])
    df_comment = pd.DataFrame(columns=['URL', 'DateTime', 'Content', 'DefectID', 'CarName'])

    post_urls = ['&'.join(url.split("&")[0:2]) for url in post_urls]

    for post_url in post_urls:
        try:
            logging.info(f'-----{post_url}')
            sleep_time = random.uniform(0.1, 3.0)
            time.sleep(sleep_time)
            try:
                driver.get(post_url)
                WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.TAG_NAME, "a"))
                )
            except TimeoutException:
                logging.info("Page Loading Failed in 3 sec, Next step ...")
            source = BeautifulSoup(driver.page_source, 'html.parser')
            Title = source.find('span', class_='title_subject').text
            DateTime = source.find('span', class_='gall_date')['title']
            Content = source.find('div', 'write_div').text if source.find('div', 'write_div') != None else None
            ViewCount = source.find('span', 'gall_count').text.split()[1]
            comments = []
            for cmt_comp in source.find_all('li','ub-content'):
                if cmt_comp.find('p', 'usertxt ub-word') and cmt_comp.find('span', 'date_time'):
                    CommentContent = cmt_comp.find('p', 'usertxt ub-word').text
                    CommentDateTime = cmt_comp.find('span', 'date_time').text
                    comments.append({"CommentContent": CommentContent, "CommentDateTime": CommentDateTime})
            result = {
                'post': {
                    'URL': post_url,
                    'Title': Title,
                    'DateTime': DateTime,
                    'ViewCount': ViewCount,
                    'Content': Content,
                    'CarName': keyword, ############ ############ ############ ############ ############ ############ ############ ############ ############ 확인
                    'DefectID': None,
                    'Sentiment': None
                },
                'comments':[
                    {
                        'URL': post_url,
                        'DateTime': comment["CommentDateTime"],
                        'Content': comment["CommentContent"],
                        'DefectID': None,
                        'CarName': keyword, ############ ############ ############ ############ ############ ############ ############ ############ ############ 확인
                        'Sentiment' : None
                    } for comment in comments
                ]
            }
            df_post.loc[len(df_post)] = result['post']
            for comment in result['comments']:
                df_comment.loc[len(df_comment)] = comment
        except:
            logging.info(f'failed-----{post_url} ')

    #df_post.to_csv("test_post.csv")
    #df_comment.to_csv("test_comment.csv")

    logging.info("########## DONE! ##########")

    driver.quit()


    #####
    ##### 파일 업로드 및 메시지 전송
    #####

    ##### S3업로드
    def upload_df_to_s3_as_csv(df, bucket, key):
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
        csv_buffer.seek(0)
        s3_resource = boto3.resource('s3')
        s3_resource.Bucket(bucket).upload_fileobj(csv_buffer, key)
        logging.info(f"File uploaded to {bucket}/{key}")
    
    current_time = pendulum.now(tz=kst).strftime("%Y%m%d_%H%M%S")
    bucket_name = 'de1s3'
    folder_path = 'demo1_test_real_time/'

    key_posts = f'{folder_path}{keyword}_post_{current_time}.csv'
    key_comments = f'{folder_path}{keyword}_comment_{current_time}.csv'

    upload_df_to_s3_as_csv(df_post, bucket_name, key_posts)
    upload_df_to_s3_as_csv(df_comment, bucket_name, key_comments)

    logging.info("##### S3 Upload Done.")


    # 브로커에 메시지 전송
    
    # Kafka 클러스터의 브로커 리스트
    bootstrap_servers = ['10.1.3.19:9091', '10.1.3.19:9092', '10.1.3.19:9093']
    
    # Kafka Producer 생성
    producer = KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8')
    )
    
    try:
        # 각 행을 Kafka에 전송
        for index, row in df_post.iterrows():
            key = 'dc_post'  # 고정된 키 값
            value = row.to_dict()  # 행을 딕셔너리로 변환
            producer.send('tucson_community', key=key, value=value)
    
        for index, row in df_comment.iterrows():
            key = 'dc_comment'  # 고정된 키 값
            value = row.to_dict()  # 행을 딕셔너리로 변환
            producer.send('tucson_community', key=key, value=value)
    
        producer.flush()  # 모든 메시지를 보낸 후 flush()를 한 번만 호출
    
        logging.info("##### All messages sent to Kafka.")
    except Exception as e:
        logging.exception("Something went wrong with Kafka logic. Check This.")
    finally:
        producer.close()
        

# PythonOperator 설정
scraper_task = PythonOperator(
    task_id='scrape_dcinside_task',
    python_callable=scrape_dcinside_tucson,
    dag=dag,
)

# TriggerDagRunOperator 추가
trigger_livewatch_task = TriggerDagRunOperator(
    task_id='trigger_livewatch',
    trigger_dag_id='dcinside_livewatch_tucson', # dcinside_livewatch_tucson -> trigger
    dag=dag,
)

scraper_task >> trigger_livewatch_task

