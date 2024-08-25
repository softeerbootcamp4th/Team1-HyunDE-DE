from airflow import DAG
from airflow.operators.email_operator import EmailOperator
from airflow.operators.dummy_operator import DummyOperator
from datetime import datetime, timedelta
import pendulum

kst = pendulum.timezone('Asia/Seoul')

# DAG 설정
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 8, 23, tzinfo=kst),  # 시작 날짜 설정
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'email_self_notification',  # DAG 이름 변경 필요
    default_args=default_args,
    description='Send email to self as notification',
    schedule_interval=None,  # 다른 DAG에 의해 트리거됨
    catchup=False,
    max_active_runs=1,
    tags=['notification'],
)

start = DummyOperator(
    task_id='start',
    dag=dag,
)

send_email_task = EmailOperator(
    task_id='send_email',
    to='dlawork9888devtest@gmail.com',
    subject='Airflow Notification: TEST',
    html_content="""<h3>Airflow DAG has been triggered successfully!</h3>""",
    dag=dag,
)

end = DummyOperator(
    task_id='end',
    dag=dag,
)

# Task Dependencies
start >> send_email_task >> end
