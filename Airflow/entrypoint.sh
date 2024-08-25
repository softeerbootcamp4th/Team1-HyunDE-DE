#!/bin/bash

set -e

# 데이터베이스 초기화
airflow db init

# 기본 관리자 계정 생성 (이미 생성된 경우 에러를 무시)
airflow users create \
    --username dlawork9888 \
    --firstname work \
    --lastname dla \
    --role Admin \
    --email dlawork9888@example.com \
    --password {} || true

# 스케줄러와 웹 서버 시작
airflow scheduler &
exec airflow webserver
