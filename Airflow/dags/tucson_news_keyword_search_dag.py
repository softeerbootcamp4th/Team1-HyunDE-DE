from airflow import DAG
from airflow.operators.python_operator import PythonOperator, BranchPythonOperator
from airflow.operators.email_operator import EmailOperator
from airflow.operators.dummy_operator import DummyOperator
from datetime import datetime, timedelta
import pendulum
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging

# DAG 설정
kst = pendulum.timezone('Asia/Seoul')
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 8, 23, tzinfo=kst),  # 시작 날짜
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'tucson_news_keyword_search_dag',
    default_args=default_args,
    description='A DAG to search Tucson news and send results via email',
    schedule_interval='30 1,4,7,10,13,16,19,22 * * *',
    catchup=False,
    max_active_runs=1,
    tags=['news', 'tucson', 'email'],
)

def execute_news_search_and_email(**kwargs):
    # WebDriver 초기화
    service = Service(executable_path='/usr/bin/chromedriver')
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(service=service, options=options)

    try:
        # 뉴스 검색 및 처리 로직
        def get_news_info(driver, model):
            query = model
            base_url = "https://search.naver.com/search.naver"
            params = f"?where=news&query={query}&sm=tab_opt&sort=1&photo=0&field=0&pd=9&docid=&related=0&mynews=0&office_type=0&office_section_code=0&news_office_checked=&nso=so%3Add%2Cp%3Aall&is_sug_officeid=0&office_category=0&service_area=0"
            url = base_url + params

            # 첫 페이지 로드
            logging.info(f"Loading URL: {url}")
            driver.get(url)
            time.sleep(3)  # 페이지 로딩을 기다림
            logging.info("Page loaded. Scrolling to the bottom...")

            # 스크롤하여 끝까지 로드
            def scroll_to_bottom(driver):
                last_height = driver.execute_script("return document.body.scrollHeight")
                while True:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)  # 페이지 로딩을 기다림
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height

            scroll_to_bottom(driver)
            logging.info("Finished scrolling. Parsing page content...")

            # 뉴스 정보 추출
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            articles = soup.find_all('li', class_='bx')
            logging.info(f"Found {len(articles)} articles.")

            news_data = []
            for index, article in enumerate(articles):
                logging.info(f"Processing article {index + 1}/{len(articles)}")
                title_tag = article.find('a', class_='news_tit')
                link = title_tag.get('href') if title_tag else None
                title = title_tag.get('title') if title_tag else "제목 없음"
                logging.info(f"Title: {title}")

                # 기사 페이지 들어가서 내용 가져오기
                if link:
                    try:
                        logging.info(f"Accessing article link: {link}")
                        driver.get(link)
                        time.sleep(5)
                        article_soup = BeautifulSoup(driver.page_source, 'html.parser')
                        content = article_soup.get_text(strip=True)
                        news_data.append({'Title': title, 'Link': link, 'Content': content})
                        logging.info(f"Article content retrieved, length: {len(content)} characters.")
                    except Exception as e:
                        logging.error(f"Error accessing the article at {link}: {e}")
                        break
                else:
                    logging.warning("No valid link found for this article.")

            logging.info("Finished processing all articles.")
            return news_data

        # 뉴스 정보 가져오기
        news_info = get_news_info(driver, '투싼')
        if news_info:
            html_content = "<h1>Recent Tucson News</h1>"
            for info in news_info:
                html_content += f"<h3>{info['Title']}</h3>"
                html_content += f"<p><a href='{info['Link']}'>기사 링크</a></p>"
                html_content += f"<p>{info['Content'][:500]}...</p>"
                html_content += "<hr>"
            kwargs['ti'].xcom_push(key='email_content', value=html_content)
            return 'send_email'
        else:
            logging.info("No news articles found.")
            return 'no_email'

    finally:
        # WebDriver 종료
        driver.quit()
        logging.info("WebDriver session ended.")

# 뉴스 검색 및 이메일 내용 준비하는 PythonOperator
prepare_news_task = PythonOperator(
    task_id='prepare_news',
    python_callable=execute_news_search_and_email,
    provide_context=True,
    dag=dag,
)

# BranchPythonOperator를 사용하여 뉴스가 있는 경우에만 이메일 전송
branch_task = BranchPythonOperator(
    task_id='branch_task',
    provide_context=True,
    python_callable=lambda **kwargs: kwargs['ti'].xcom_pull(task_ids='prepare_news'),
    dag=dag,
)

# 이메일 전송을 위한 EmailOperator
send_email_task = EmailOperator(
    task_id='send_email',
    to='dlawork9888devtest@gmail.com',
    subject='# Airflow Notification ----- Recent Tucson News',
    html_content="{{ ti.xcom_pull(task_ids='prepare_news', key='email_content') }}",
    dag=dag,
)

# 이메일 전송이 없는 경우를 처리하기 위한 DummyOperator
no_email_task = DummyOperator(
    task_id='no_email',
    dag=dag,
)

prepare_news_task >> branch_task
branch_task >> send_email_task
branch_task >> no_email_task
