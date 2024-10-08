## 프로젝트 개요

이 프로젝트는 특정 자동차 모델 및 이슈에 관련된 네이버 뉴스 기사를 크롤링하고, 그 데이터를 정리하여 Excel 파일로 저장하는 Python 스크립트입니다. 이 프로젝트에는 두 가지 버전의 스크립트가 포함되어 있으며, 각각 다른 방식으로 데이터를 수집 및 처리합니다.

## 파일 구조

```

.../
├── news_v1.py
├── news_v2.py
└── readme.md

```

- **`news_v1.py`**: 초기 버전으로, 간단한 검색어를 바탕으로 네이버 뉴스에서 관련 기사를 크롤링하여 데이터를 추출합니다.
- **`news_v2.py`**: 개선된 버전으로, 날짜 범위와 검색어 조합을 통해 더욱 정교하게 데이터를 수집하며, 다양한 날짜 형식과 기사 내용을 처리할 수 있습니다.
- **`readme.md`**: 프로젝트에 대한 개요 및 각 스크립트에 대한 설명을 제공합니다.

## news_v1.py 설명

`news_v1.py`는 초기 버전의 스크립트로, 특정 모델의 결함을 바탕으로 네이버 뉴스에서 관련 기사를 크롤링합니다.

### 주요 기능

- 크롬 드라이버를 자동으로 설치 및 설정하여 사용자가 별도의 설정 없이 스크립트를 실행할 수 있습니다.
- 기본적인 기사 제목, 날짜, 링크를 추출하여 데이터를 수집합니다.
- 마지막 페이지까지 스크롤하며 모든 기사를 수집합니다.
- 수집된 데이터를 pandas DataFrame으로 변환하여 Excel 파일로 저장합니다.

### 사용법

1. 필요한 라이브러리 설치:
    
    ```
    
    pip install pandas beautifulsoup4 selenium chromedriver-autoinstaller
    
    ```
    
2. 스크립트를 실행하면, 기본 설정된 모델에 대한 뉴스 기사를 크롤링하여 지정된 경로에 Excel 파일로 저장합니다.

## news_v2.py 설명

`news_v2.py`는 `news_v1.py`를 개선한 버전으로, 더욱 정교하게 기사를 크롤링하고, 다양한 날짜 형식 및 기사 내용을 처리할 수 있는 기능이 추가되었습니다.

### 주요 기능

- **날짜 범위 설정**: 특정 날짜를 기준으로 ±90일의 범위에서 기사를 검색합니다.
- **정교한 기사 추출**: 다양한 날짜 형식과 기사 본문을 정확하게 추출하여 데이터를 수집합니다.
- **유연한 파일 저장**: 모델명과 이슈명을 기준으로 파일명을 생성하여 데이터를 Excel 파일로 저장합니다.

### 사용법

1. 필요한 라이브러리 설치:
    
    ```
    
    pip install pandas beautifulsoup4 selenium chromedriver-autoinstaller
    
    ```
    
2. 스크립트를 실행하면, 설정된 모델과 이슈에 대한 뉴스 기사를 크롤링하여, 각각의 이슈에 대해 별도의 Excel 파일로 데이터를 저장합니다.

## 크롤링 결과

각 스크립트를 실행한 후, 지정된 경로에 생성된 Excel 파일에는 크롤링된 뉴스 기사의 제목, 날짜, 링크, 기사 본문(해당 시)이 포함되어 있습니다. 이러한 데이터는 모델 및 이슈별로 구분되어 저장됩니다.
