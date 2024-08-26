# EMR 클러스터 관리 람다 함수

## 개요

이 프로젝트는 AWS Lambda를 사용하여 EMR 클러스터를 시작하고, Spark 작업을 제출하며, 처리된 결과를 RDS로 전송하는 기능을 포함합니다.

## 주요 구성 요소

- **EMR 클러스터**: 대규모 데이터 처리를 위한 Apache Spark 실행 환경을 제공합니다.
- **Spark 작업**: `Data_processing.py` 스크립트를 실행하여 데이터를 전처리하고 변환합니다.
- **S3 버킷**: 처리할 데이터 파일을 저장하고, 결과 데이터를 임시로 저장하는 데 사용됩니다.
- **RDS**: 최종 처리 결과를 저장하여 분석과 비즈니스 의사결정에 활용합니다.

## Lambda 함수 역할

- **lambda_emr**: EMR 클러스터를 시작하고, Spark 작업(`Data_processing.py`)을 EMR에 제출합니다.
- **lambda_start**: EMR 클러스터 작업이 완료된 후 클러스터를 종료하고, 처리 결과를 RDS에 저장합니다.

## 사용 모듈

- `boto3`: AWS 리소스 관리 (EMR, S3)
- `pymysql`: RDS에 연결하여 데이터베이스 작업 수행
- `pandas`: 데이터프레임으로 CSV 파일을 처리
- `SQLAlchemy`: RDS에 데이터를 효율적으로 삽입

## 실행 방법

1. **람다 함수 배포**: `lambda_emr`와 `lambda_start` 함수를 AWS Lambda에 배포합니다.
2. **환경 변수 설정**: S3 버킷 이름, RDS 접속 정보 등 필요한 환경 변수를 설정합니다.
3. **람다 함수 실행**: `lambda_emr`를 실행하여 EMR 클러스터를 시작하고 데이터를 처리합니다. 작업이 완료되면 `lambda_start`가 자동으로 클러스터를 종료하고 RDS로 결과를 전송합니다.

