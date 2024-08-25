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

# entrypoint 스크립트 복사 및 실행 권한 부여
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# entrypoint 설정
ENTRYPOINT ["/entrypoint.sh"]
