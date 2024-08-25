from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import os
from bs4 import BeautifulSoup
import pandas as pd
import re
import time

##### logger
def logger(log_txt_path, message):
    # 현재 시간을 'YYYY-MM-DD HH:MM:SS' 형식으로 가져옴
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    # 로그 메시지를 "{현재시간}---{message}" 형식으로 생성
    log_message = f"{current_time}-----{message}\n"
    # 파일이 없으면 생성하고, 있으면 추가 모드로 열기
    with open(log_txt_path, 'a') as log_file:
        log_file.write(log_message)


def save_dataframes(df_post, df_comment):
    # 데이터를 CSV 파일로 저장
    df_post.to_csv('post_data.csv', index=False)
    df_comment.to_csv('comment_data.csv', index=False)
    print("DataFrames saved successfully.")


def signal_handler(sig, frame):
    print("Interrupt received, saving DataFrames...")
    save_dataframes(df_post, df_comment)
    driver.quit()  # 드라이버를 종료합니다.
    print("Driver closed.")
    exit(0)



def extract(post_url, driver):

    try:
        driver.get(post_url)

        WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

        xpath = '/html/body/div[2]/div[3]/main/section/article[2]/div[3]/div[1]/div/div[2]/button[2]'
        button = driver.find_element(By.XPATH, xpath)
        button.click()


        source = BeautifulSoup(driver.page_source, 'html.parser')

        Title = source.find('span', class_='title_subject').text

        DateTime = pd.to_datetime(source.find('span', class_='gall_date')['title'])

        Content = source.find('div', 'write_div').text if source.find('div', 'write_div') != None else None

        ViewCount = int(source.find('span', 'gall_count').text.split()[1])

        ##### 댓글
        next_cmt_count = []
        if source.find('div', 'cmt_paging').find_all('a'):
            next_cmt_count.append(int(source.find('div', 'cmt_paging').find_all('a')[0].text))


        comments = []
        for cmt_comp in source.find_all('li','ub-content'):
            if cmt_comp.find('p', 'usertxt ub-word') and cmt_comp.find('span', 'date_time'):
                CommentContent = cmt_comp.find('p', 'usertxt ub-word').text
                CommentDateTime = cmt_comp.find('span', 'date_time').text
                this_post_year = source.find('span', class_='gall_date')['title'][0:4]
                CommentDateTime = this_post_year+'.'+CommentDateTime
                CommentDateTime = pd.to_datetime(CommentDateTime, format='%Y.%m.%d %H:%M:%S')
                comments.append({"CommentContent": CommentContent, "CommentDateTime": CommentDateTime})

        for i in next_cmt_count:
            driver.execute_script(f"viewComments({i}, 'D');")
            time.sleep(1)
            source = BeautifulSoup(driver.page_source, 'html.parser')
            for cmt_comp in source.find_all('li','ub-content'):
                if cmt_comp.find('p', 'usertxt ub-word') and cmt_comp.find('span', 'date_time'):
                    CommentContent = cmt_comp.find('p', 'usertxt ub-word').text
                    CommentDateTime = cmt_comp.find('span', 'date_time').text
                    this_post_year = source.find('span', class_='gall_date')['title'][0:4]
                    CommentDateTime = this_post_year+'.'+CommentDateTime
                    CommentDateTime = pd.to_datetime(CommentDateTime, format='%Y.%m.%d %H:%M:%S')
                    comments.append({"CommentContent": CommentContent, "CommentDateTime": CommentDateTime})

        return {
            'post': {
                'URL': post_url,
                'Title': Title,
                'DateTime': DateTime,
                'ViewCount': ViewCount,
                'Content': Content,
                'CarName': None,
                'DefectCause': None
            },
            'comments':[
                {
                    'URL': post_url,
                    'DateTime': comment["CommentDateTime"],
                    'Content': comment["CommentContent"],
                    'DefectCause': None,
                    'CarName': None
                } for comment in comments
            ]
        }
    except:
        message = f"extration failed-----{post_url}"
        print(message)
        logger("extraction_log.txt", message)
        return None



if __name__ == "__main__":

    df_post = pd.DataFrame(columns=['URL', 'Title', 'DateTime', 'ViewCount', 'Content', 'CarName', 'DefectCause'])
    df_comment = pd.DataFrame(columns=['URL', 'DateTime', 'Content', 'DefectCause', 'CarName'])

    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 브라우저 창을 열지 않음
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    lines = []
    with open(f'post_urls_log.txt', 'r') as file:
        lines = file.readlines()

    lines = lines[2010:]

    try:
        for line in lines:
            try:
                post_url = "https://gall.dcinside.com/" + line.split('-----')[2]
                print(f'Now URL-----{post_url}')
                extract_result = extract(post_url, driver)
                if extract_result is not None:
                    df_post.loc[len(df_post)] = extract_result["post"]
                for comment in extract_result["comments"]:
                    df_comment.loc[len(df_comment)] = comment
            except:
                message = f"line failed-----{post_url}"
                print(message)
                logger("extraction_log.txt", message)
    except Exception as e:
        message = f"An error occurred(or ctrl + c): {e}"
        print(message)
        logger("extraction_log.txt", message)
    finally:
        save_dataframes(df_post, df_comment)
        driver.quit()