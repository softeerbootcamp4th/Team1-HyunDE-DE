from kafka import KafkaConsumer
import json
import redis
from airflow import DAG
from airflow.operators.python_operator import PythonOperator, BranchPythonOperator
from airflow.operators.email_operator import EmailOperator
from airflow.operators.dummy_operator import DummyOperator
from datetime import datetime, timedelta
import logging
import pendulum

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
    'dcinside_keyword_search_dag',
    default_args=default_args,
    description='dcinside_keyword_search_dag',
    schedule_interval='0 1,4,7,10,13,16,19,22 * * *',
    catchup=False,
    max_active_runs=1,
    tags=['KeywordSearch'],
)


def dc_tucson_keyword_search(**kwargs):
    try:
        # Kafka Consumer 설정
        topic = 'tucson_community'

        # Redis 연결
        redis_client = redis.Redis(host='10.1.1.224', port=6379, db=1)  # LiveWatch랑 다른 DB를 이용

        # KafkaConsumer 설정
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=['10.1.3.19:9091', '10.1.3.19:9092', '10.1.3.19:9093'],
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            auto_offset_reset='earliest',
            group_id='tucson_keyword_search_cg0',
            max_poll_records=3000
        )

        # 메시지 가져오기
        messages = consumer.poll(timeout_ms=15000)
        consumer.close()  # Consumer 종료

        # Redis에서 모든 키를 가져와 set으로 저장
        all_redis_keys = set([key.decode('utf-8') for key in redis_client.keys("*")])

        logging.info(f"-----DEBUG----- 레디스에서 읽어온 모든 키 길이: {len(all_redis_keys)}")

        # 중복 및 새로운 데이터 확인을 위한 변수
        input_data_count = 0
        duplicate_count = 0
        new_post_count = 0
        keywords = ['결함', '고장']  # 새로운 포스트 키워드 검사
        new_posts_having_keyword = []
        new_comments_having_keyword = []

        # 메시지 처리 및 Redis 갱신
        for tp, records in messages.items():
            for record in records:
                input_data_count += 1
                key = record.key.decode('utf-8')  # 키 디코드
                value = record.value

                if key in ['dc_post', 'dc_comment']:
                    redis_key = value['URL'] if key == 'dc_post' else f"{value['URL']} - {value['Content']}"
                    redis_value = json.dumps(value)  # JSON 형태로 변환

                    if redis_client.exists(redis_key):
                        duplicate_count += 1  # 중복 데이터 존재 시 처리
                    else:
                        if key == 'dc_post':
                            new_post_count += 1  # 새로운 post 카운트 증가
                            for keyword in keywords:
                                if keyword in value['Title'] or keyword in value['Content']:
                                    new_posts_having_keyword.append(
                                        ['post', keyword, value['Title'], value['Content'], value['URL']])
                        elif key == 'dc_comment':
                            for keyword in keywords:
                                if keyword in value['Content']:
                                    new_comments_having_keyword.append(
                                        ['comment', keyword, value['Content'], value['URL']])

                    # Redis 데이터 갱신 (기존 키가 있든 없든 갱신)
                    redis_client.set(redis_key, redis_value)
                    all_redis_keys.discard(redis_key)  # 처리된 키는 set에서 제거

        # 중복되지 않은 키를 삭제
        logging.info(f"-----DEBUG----- Redis에서 지워야할 데이터 길이: {len(all_redis_keys)}")
        for key in all_redis_keys:
            redis_client.delete(key)

        # 결과 출력
        logging.info(f'들어온 데이터포인트 수: {input_data_count}')
        logging.info(f"중복된 항목 수: {duplicate_count}")
        logging.info(f"# 새로 들어온 Post 데이터 수: {new_post_count}")
        logging.info(f'삭제된 데이터 수: {len(all_redis_keys)}')
        logging.info(f'# new_posts_having_keyword: {new_posts_having_keyword}')
        logging.info(f'# new_comments_having_keyword: {new_comments_having_keyword}')

        # 결과를 XCom으로 푸시
        kwargs['ti'].xcom_push(key='new_posts_having_keyword', value=new_posts_having_keyword)
        kwargs['ti'].xcom_push(key='new_comments_having_keyword', value=new_comments_having_keyword)
        kwargs['ti'].xcom_push(key='keywords', value=keywords)

        # 분기 태스크에서 사용할 다음 태스크 결정
        if new_posts_having_keyword or new_comments_having_keyword:
            return 'prepare_email_content'
        else:
            return 'skip_email'

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return 'skip_email'


def send_email_notification(**kwargs):
    new_posts = kwargs['ti'].xcom_pull(key='new_posts_having_keyword', task_ids='dc_tucson_keyword_search')
    new_comments = kwargs['ti'].xcom_pull(key='new_comments_having_keyword', task_ids='dc_tucson_keyword_search')
    keywords = kwargs['ti'].xcom_pull(key='keywords', task_ids='dc_tucson_keyword_search')

    email_content = f"""
    <html>
        <body>
            <h1>Tucson Keyword Search Notification</h1>
            <p><strong>Configured Keywords:</strong> {', '.join(keywords)}</p>
            <hr>
            <h3><strong>New Posts with Keywords:</strong></h3>
            {'<br>'.join([f"Keyword: {post[1]}<br>Title: {post[2]}<br>Content: {post[3]}<br>URL: <a href='{post[4]}'>{post[4]}</a><br>" for post in new_posts]) if new_posts else "No new posts found."}
            <hr>
            <h3><strong>New Comments with Keywords:</strong></h3>
            {'<br>'.join([f"Keyword: {comment[1]}<br>Content: {comment[2]}<br>URL: <a href='{comment[3]}'>{comment[3]}</a>" for comment in new_comments]) if new_comments else "No new comments found."}
            <hr>
        </body>
    </html>
    """

    return email_content


# PythonOperator 설정
dcinside_livewatch_tucson_task = PythonOperator(
    task_id='dc_tucson_keyword_search',
    python_callable=dc_tucson_keyword_search,
    provide_context=True,
    dag=dag,
)

# BranchPythonOperator를 사용하여 뉴스가 있는 경우에만 이메일 전송
branch_task = BranchPythonOperator(
    task_id='branch_task',
    provide_context=True,
    python_callable=lambda **kwargs: kwargs['ti'].xcom_pull(task_ids='dc_tucson_keyword_search'),
    dag=dag,
)

# 이메일 전송을 위한 PythonOperator
send_email_task = PythonOperator(
    task_id='prepare_email_content',
    python_callable=send_email_notification,
    provide_context=True,
    dag=dag,
)

# 이메일 전송을 위한 EmailOperator
email_task = EmailOperator(
    task_id='send_email',
    to='dlawork9888devtest@gmail.com',
    subject='# Airflow Notification ----- Keyword Found for Tucson',
    html_content="{{ ti.xcom_pull(task_ids='prepare_email_content') }}",
    dag=dag,
)

# 이메일 전송이 없는 경우를 처리하기 위한 DummyOperator
skip_email_task = DummyOperator(
    task_id='skip_email',
    dag=dag,
)

dcinside_livewatch_tucson_task >> branch_task
branch_task >> send_email_task >> email_task
branch_task >> skip_email_task
