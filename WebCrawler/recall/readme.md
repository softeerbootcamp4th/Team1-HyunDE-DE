## 프로젝트 개요

이 프로젝트는 `www.car.go.kr`에서 자동차 리콜 정보를 크롤링하고, 그 데이터를 정리하여 Excel 또는 CSV 파일로 저장하는 Python 스크립트를 제공합니다. 프로젝트는 두 가지 주요 버전의 스크립트를 포함하고 있으며, 각각 다른 방식으로 데이터를 수집 및 처리합니다.

## 파일 구조

```
.../
├── recall_v1.ipynb
├── recall_v2.ipynb
└── readme.md

```

- **`recall_v1.ipynb`**: 초기 버전으로, 기본적인 리콜 정보를 크롤링하여 데이터를 수집합니다.
- **`recall_v2.ipynb`**: 개선된 버전으로, 더 상세한 리콜 정보를 포함하여 데이터를 수집하며, 각 리콜 항목의 세부 정보를 추출합니다.
- **`readme.md`**: 프로젝트에 대한 개요 및 각 스크립트에 대한 설명을 제공합니다.

## recall_v1.ipynb 설명

`recall_v1.ipynb`는 `www.car.go.kr`에서 기본적인 리콜 정보를 크롤링하는 초기 버전의 스크립트입니다.

### 주요 기능

- **크롬 드라이버 자동 설치 및 설정**: `chromedriver_autoinstaller`를 사용하여 크롬 드라이버를 자동으로 설치하고 설정합니다.
- **기본 정보 크롤링**: 리콜 목록에서 제목, 담당 부서, 날짜 정보를 추출하여 수집합니다.
- **페이지 네비게이션**: 여러 페이지에 걸쳐 있는 리콜 정보를 크롤링하기 위해 페이지를 순차적으로 이동하며 데이터를 수집합니다.
- **데이터 정리**: 수집한 데이터를 pandas DataFrame으로 정리하고, 이를 Excel 파일로 저장합니다.

### 사용법

1. 필요한 라이브러리 설치:
    
    ```
    pip install pandas beautifulsoup4 selenium chromedriver-autoinstaller
    
    ```
    
2. Jupyter Notebook에서 `recall_v1.ipynb`를 실행하면, 기본적인 리콜 정보를 크롤링하여 Excel 파일로 저장합니다.

## recall_v2.ipynb 설명

`recall_v2.ipynb`는 `recall_v1.ipynb`를 개선한 버전으로, 리콜 항목에 대한 더 상세한 정보를 크롤링합니다.

### 주요 기능

- **세부 정보 크롤링**: 리콜 목록의 각 항목에 대해 상세 페이지에 접근하여, 제작사, 차명, 생산 기간, 결함 내용 등의 추가 정보를 추출합니다.
- **더 많은 페이지 처리**: 더 많은 페이지 범위를 커버할 수 있도록 설계되었습니다.
- **데이터 저장**: 수집된 데이터를 pandas DataFrame으로 정리한 후 CSV 파일로 저장합니다.

### 사용법

1. 필요한 라이브러리 설치:
    
    ```
    pip install pandas beautifulsoup4 selenium chromedriver-autoinstaller
    
    ```
    
2. Jupyter Notebook에서 `recall_v2.ipynb`를 실행하면, 상세한 리콜 정보를 크롤링하여 CSV 파일로 저장합니다.

## 크롤링 결과

각 스크립트를 실행한 후, 지정된 경로에 생성된 Excel 또는 CSV 파일에는 크롤링된 리콜 정보가 포함되어 있습니다. `recall_v2.ipynb`의 경우, 각 리콜 항목의 세부 정보까지 포함되어 있어 더욱 풍부한 데이터를 제공합니다.