# DE1 - AIRFLOW

### Port ?

- 18888:8888 - Jupyter Lab

- 8080:8080 - Airflow Web UI

- + Postgre :5432

- (추가, Compose X)+ Redis :6379

## Dockerfile & docker-compose.yml 

- arm64 기반 아키텍처 -> chromium 이용
- chromium & driver 용량 -> 이미지 빌드 후 DockerHub에서 Push하여 이용

```
docker build -t dlaawork9888/custom_airflow_image:0.0.0 .

docker push dlaawork9888/custom_airflow_image:0.0.0
```

- 이후 배포용 EC2에서 git repo clone(private), docker pull

```
docker pull dlaawork9888/custom_airflow_image:0.0.0

docker tag dlaawork9888/custom_airflow_image:0.0.0 custom_airflow_image
```

- docker compose up

```
docker compose up -d
```

- 이후, airflow 컨테이너에 접속하여 jupyter lab 실행

    - `jupyter lab --allow-root --no-browser --port=8888 --ip=0.0.0.0 --NotebookApp.token='{}'`

    - 루트 디렉터리에서 실행,실행중이라면 

- jupyter lab을 통해 task test 및 DAG 작성

- *** `docker-compose down -v` -> 컴포즈에서 지정한 볼륨까지 같이 Down !

### Dockerfile

```Dockerfile

FROM apache/airflow:slim-2.10.0-python3.10

USER root

LABEL maintainer="dlawork9888"

# 기본 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    wget \
    git \
    xvfb \
    vim \
    nano \
    net-tools \
    iputils-ping \
    dnsutils \
    libpq-dev \
    libnss3 \
    libxss1 \
    libgconf-2-4 \
    libasound2 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxi6 \
    libxtst6 \
    libglib2.0-0 \
    libfontconfig1 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libgbm-dev \
    xdg-utils \
    gnupg \
    ca-certificates \
    gdebi-core \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 필요한 파일 복사 (root 사용자로)
COPY requirements.txt /requirements.txt

# Python 패키지 설치
RUN pip3 install --no-cache-dir -r /requirements.txt

# PostgreSQL 드라이버 설치
RUN pip3 install --no-cache-dir psycopg2

# 크롬 드라이버 복사
COPY --chown=airflow:root ./chromium_deb /chromium_deb

# Install Chromium and dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libgbm-dev && \
    gdebi -n /chromium_deb/chromium-codecs-ffmpeg-extra_112.0.5615.49-0ubuntu0.18.04.1_arm64.deb && \
    gdebi -n /chromium_deb/chromium-browser_112.0.5615.49-0ubuntu0.18.04.1_arm64.deb && \
    gdebi -n /chromium_deb/chromium-chromedriver_112.0.5615.49-0ubuntu0.18.04.1_arm64.deb && \
    rm -rf /var/lib/apt/lists/*

# DAGs 복사
COPY --chown=airflow:root ./dags /opt/airflow/dags
COPY --chown=airflow:root ./before_dag.ipynb /before_dag.ipynb

# entrypoint 스크립트 복사 및 실행 권한 부여
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# entrypoint 설정
ENTRYPOINT ["/entrypoint.sh"]
```

### docker-compose.yml

```yml
services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: {}
      POSTGRES_DB: airflow
    ports:
      - "5432:5432"

  airflow:
    image: custom_airflow_image
    environment:
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:{}@postgres/airflow
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
    depends_on:
      - postgres
    ports:
      - "8080:8080"
      - "18888:8888"
    volumes:
      - ./dags:/opt/airflow/dags

networks:
  kafka_airflow_net:
    external: true
```

## 사전 세팅

### Redis 

```sh
sudo docker pull redis

docker run -d \
  --name my-redis \
  -v /redis_data:/data \
  -p 6379:6379 \
  redis:latest \
  redis-server --appendonly yes # 이건 일단 X
```


### EmailOperator 

- dlawork9888devtest@gmail.com 사용

  - Gmail 설정에서 IMAP Access 사용으로 변경 필요

  - airflow.cfg에 아래 필요 - smtp블록 전부 대체(docker compose에 명시하면 편함!-> 0.0.4 커스텀 버전에 반영하기)

  - docker compose down -> X, 컨테이너만 종료했다가 다시 실행, 변경된 config 반영
    
    - webserver, scheduler 다시 실행하는 것보다 이게 빠름

    - 볼륨 유지됨

    - Postgre가 살아있으므로 필요한 데이터도 모두 유지됨.

```  
[smtp]
smtp_host = smtp.gmail.com
smtp_starttls = True
smtp_ssl = False
smtp_user = dlawork9888devtest@gmail.com
smtp_password = {2차 인증 후 앱 비밀번호}
smtp_port = 587
smtp_mail_from = dlawork9888devtest@gmail.com
```