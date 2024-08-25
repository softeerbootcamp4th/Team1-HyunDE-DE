from kafka import KafkaConsumer
import json
import redis
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dagrun_operator import TriggerDagRunOperator
from datetime import datetime, timedelta
import logging
import pandas as pd
import pendulum 
import pymysql


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
    'dcinside_livewatch_tucson', ############ ############ ############ ############ ############ ############ ############ ############ ############ 바꿀 곳
    default_args=default_args,
    description='DCInside LiveWatch (tucson)',
    schedule_interval= None, #0 1,4,7,10,13,16,19,22 * * *', # Trigger로 변경
    catchup=False,
    max_active_runs=1,
    tags=['LiveWatch'],
)



def dcinside_livewatch_tucson():
    # Kafka Consumer 설정
    topic = 'tucson_community'
    
    # Redis 연결
    redis_client = redis.Redis(host='10.1.1.224', port=6379, db=0)
    
    # KafkaConsumer 설정
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=['10.1.3.19:9091', '10.1.3.19:9092', '10.1.3.19:9093'],
        value_deserializer=lambda x: json.loads(x.decode('utf-8')),
        auto_offset_reset='earliest',
        group_id='tucson_live_cg0',
        max_poll_records=2000
    )
    
    # 메시지 가져오기
    messages = consumer.poll(timeout_ms=15000)

    # Consumer 종료(POLLLL!!!!!!!)
    consumer.close()
    
    # Redis에서 모든 키를 가져와 set으로 저장
    all_redis_keys = [key.decode('utf-8') for key in redis_client.keys("*")]
    all_redis_keys = set(all_redis_keys)
    
    
    logging.info(f"-----DEBUG----- 레디스에서 읽어온 모든 키 길이: {len(all_redis_keys)}")
    
    # 중복 및 새로운 데이터 확인을 위한 변수
    input_data_count = 0
    duplicate_count = 0
    new_post_count = 0
    duplicates = []
    view_count_edge_post = [0, None, None, None] # 뷰카운트 증가량, Title, Content, URL
    full_view_count_increase = 0
    keyword = '결함' ##### ##### ##### ##### ##### ##### ##### ##### ##### 새로운 포스트 키워드 검사
    new_posts_having_keyword = []
    new_comments_having_keyword = []
    
    # 메시지 처리 및 Redis 갱신
    for tp, records in messages.items():
        
        for record in records:
            
            input_data_count += 1
            
            key = record.key.decode('utf-8')  # 키 디코드
            value = record.value
    
            if key == 'dc_post' or key == 'dc_comment':
                if key == 'dc_post':
                    redis_key = value['URL']
                else:
                    redis_key = f"{value['URL']} - {value['Content']}"
    
                redis_value = json.dumps(value)  # JSON 형태로 변환
    
                
                # Redis에서 해당 키로 데이터 조회
                if redis_client.exists(redis_key):
                    # 중복 데이터 존재 시
                    duplicate_count += 1
                    stored_value = json.loads(redis_client.get(redis_key))  # Redis에 저장된 데이터 가져오기
                    
                    # ViewCount 비교 및 계산
                    if 'ViewCount' in value:
                        old_view_count = stored_value.get('ViewCount', 0)
                        new_view_count = value['ViewCount']
                        view_count_increase = int(new_view_count) - int(old_view_count)
                        full_view_count_increase += view_count_increase
                        duplicates.append(f"{redis_key} (ViewCount Increase: {view_count_increase})")
                        if view_count_increase >= view_count_edge_post[0]:
                            view_count_edge_post[0] = view_count_increase
                            view_count_edge_post[1] = value['Title']
                            view_count_edge_post[2] = value['Content']
                            view_count_edge_post[3] = value['URL']
                    
    
    
                # 중복 데이터가 아닐떄 => 새로 들어온 데이터일 때        
                else:
                    if key == 'dc_post':
                        new_post_count += 1  # 새로운 post 카운트 증가 ##### 새로운 카운트만
                        if keyword in value['Title'] or keyword in value['Content']:
                            new_posts_having_keyword.append(['post', value['Title'], value['Content'], value['URL']])
                    elif key == 'dc_comment':
                        if keyword in value['Content']:
                            new_comments_having_keyword.append(['comment', None ,value['Content'], value['URL']])
                            
                            
                # Redis 데이터 갱신 (기존 키가 있든 없든 갱신)
                redis_client.set(redis_key, redis_value)
                #logging.info(f"-----DEBUG----- 지우면 안되는 데이터는 all_redis_keys에서 삭제------{redis_key}")
                all_redis_keys.discard(redis_key)  # 처리된 키는 set에서 제거
                
    
    # 중복되지 않은 키를 삭제
    logging.info(f"-----DEBUG----- Redis에서 지워야할 데이터 길이: {len(all_redis_keys)}")
    for key in all_redis_keys:
        #logging.info(f'-----DEBUG----- 처리가 안된 데이터----- {key}')
        redis_client.delete(key)
    
    # 결과 출력
    logging.info(f'들어온 데이터포인트 수: {input_data_count}')
    logging.info(f"중복된 항목 수: {duplicate_count}")
    logging.info(f"# 새로 들어온 Post 데이터 수: {new_post_count}")
    logging.info(f'삭제된 데이터 수: {len(all_redis_keys)}')
    logging.info(f'# 총 조회 증가량: {full_view_count_increase}')
    logging.info(f'# 조회수 증가가 가장 큰 포스트: {view_count_edge_post}')
    logging.info(f'# new_posts_having_keyword: {new_posts_having_keyword}')
    logging.info(f'# new_comments_having_keyword: {new_comments_having_keyword}')

    ##### ##### ##### RDS View Table에 삽입
    
    ##### ##### RDS MySQL 인스턴스에 연결
    connection = pymysql.connect(
        host='de1rds1.cfcteckvwznt.ap-northeast-2.rds.amazonaws.com',
        user='dlawork9888',
        password= {},
        database='Dashboard',
        port=3306
    )

    try:
        with connection.cursor() as cursor:
            # 현재 시간
            current_time_kst = pendulum.now('Asia/Seoul').to_datetime_string()
            print(f'##### ##### ##### ##### ##### {current_time_kst} ##### ##### ##### ##### #####')
            ##### NewContentHavingKeywordTable ----- Posts, Comments
            sql_insert = """
            INSERT INTO NewContentHavingKeywordTable (DateTime, ContentType, Title, Content, URL)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            if new_posts_having_keyword:
                cursor.executemany(sql_insert,[[current_time_kst] + ele for ele in new_posts_having_keyword])
                logging.info("'new_posts_having_keyword' has been inserted into 'NewContentHavingKeywordTable'.")
            else:
                logging.info("No new posts having keyword found. Skipping insert operation.")
            
            if new_comments_having_keyword:
                cursor.executemany(sql_insert,[[current_time_kst] + ele for ele in new_comments_having_keyword])
                logging.info("'new_comments_having_keyword' has been inserted into 'NewContentHavingKeywordTable'.")
            else:
                logging.info("No new comments having keyword found. Skipping insert operation.")
            # 커밋
            connection.commit()

            if view_count_edge_post[0] != 0:
                ##### MostIncreasePostTable
                sql_insert = """
                INSERT INTO MostIncreasingPostTable (DateTime, Increase, Title, Content, URL)
                VALUES (%s, %s, %s, %s, %s)
                """
                data = [current_time_kst] + view_count_edge_post
                cursor.execute(sql_insert, data)
                # 커밋
                connection.commit()
                logging.info("# 'view_count_edge_post' has been inserted into 'MostIncreasePostTable'")
            else:
                logging.info("# MostIncreasePostTable ----- There's no view table change.")


            ##### IncreaseScoreTable
            sql_insert = """
            INSERT INTO IncreaseScoreTable (DateTime, IncreaseScore)
            VALUES (%s, %s)
            """
            # 들어온 데이터 수 - 중복 데이터 수 = 새로운 포스트 + 새로운 댓글
            # 새로운 댓글 = 들어온 데이터 수 - 중복 데이터 수 - 새로운 포스트 
            # 10*새로운 포스트 수 + 2*새로운 댓글 수 + 총 조회수 증가량
            try:
                score = new_post_count * 10 + (input_data_count - duplicate_count - new_post_count) * 2 + full_view_count_increase
            except TypeError as e:
                logging.info(f'# Type Error Occurred: {e}')
                score = int(new_post_count) * 10 + (int(input_data_count) - int(duplicate_count) - int(new_post_count)) * 2 + int(full_view_count_increase)
            logging.info(f'# Now Increase Score: {score}')
            data = (current_time_kst, score)
            cursor.execute(sql_insert, data)
            # 커밋
            connection.commit()
            logging.info("# IncreaseScore has been inserted into 'IncreaseScoreTable'.")

            
    except Exception as e:
        logging.error(e)

    finally:
        # 연결 종료
        connection.close()
            


# PythonOperator 설정
dcinside_livewatch_tucson_task = PythonOperator(
    task_id='dcinside_livewatch_tucson',
    python_callable=dcinside_livewatch_tucson,
    dag=dag,
)

# TriggerDagRunOperator 추가
trigger_done_email = TriggerDagRunOperator(
    task_id='trigger_done_email',
    trigger_dag_id='dc_tucson_email_noti_dag', 
    dag=dag,
)

dcinside_livewatch_tucson_task >> trigger_done_email