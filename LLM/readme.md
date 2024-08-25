아래는 요청하신 네 가지 파일(`Defect_말뭉치.ipynb`, `defect_llm`, `sentiment.ipynb`, `summary_llm.ipynb`)에 대한 마크다운 정리입니다. 각 파일의 주요 내용과 그 기능을 간략하게 설명하며, 코드와 주요 개념을 중심으로 요약하였습니다.

---

# Defect_말뭉치.ipynb

**주제**: 사전 기반 결함 분류

## 주요 내용

- **말뭉치 기반 결함 분류**:
    - 결함 관련 텍스트 데이터를 사전 기반으로 전처리하여 특정 카테고리로 분류하는 과정.
    - 사용자는 결함 텍스트를 입력하며, 사전에 정의된 매핑 규칙에 따라 해당 텍스트를 특정 카테고리로 변환합니다.

## 코드 설명

- **데이터 전처리**:
    
    ```python
    import re
    import numpy as np
    import pandas as pd
    import json
    
    with open('/path/to/label.json', 'r', encoding='utf-8') as file:
        mapping = json.load(file)
    
    df = pd.read_csv('/path/to/issue.csv')
    
    def preprocess_data(data, mapping):
        preprocessed_data = []
        for item in data:
            if item is not np.nan:
                item_clean = re.sub(r'\\([^)]*\\)', '', item).strip()
                item_clean = item_clean.replace(" 기타", "")
                preprocessed_data.append(mapping.get(item_clean, item_clean))
            else:
                preprocessed_data.append(np.nan)
        return np.array(preprocessed_data)
    
    preprocessed_data = preprocess_data(df['장치분류'], mapping)
    
    ```
    
- **결과 저장**:
    
    ```python
    df['장치분류'] = preprocessed_data
    df.to_csv('filtered_issue.csv')
    
    ```
    

---

# defect_llm

**주제**: LLM을 사용한 결함 분류

## 주요 내용

- **LLM 기반 결함 분류**:
    - Pre-trained language model을 활용하여 차량 결함 텍스트를 분석하고, 해당 텍스트가 어떤 결함에 속하는지를 예측.
    - 모델 로드, 토큰화, 추론 및 결과 해석 과정을 포함.

## 코드 설명

- **모델 로드 및 토크나이저 설정**:
    
    ```python
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    import torch.nn.functional as F
    
    model_id = "meta-llama/Meta-Llama-3-8B-Instruct"
    hf_token = "your_hf_token"
    tokenizer = AutoTokenizer.from_pretrained(model_id, token=hf_token)
    
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForSequenceClassification.from_pretrained(
        model_id,
        num_labels=15,  # 카테고리 수에 맞게 조정
        token=hf_token
    )
    
    ```
    
- **결함 분류 함수**:
    
    ```python
    def classify_post(post, model, tokenizer, defect_catalog):
        inputs = tokenizer(post, return_tensors="pt", truncation=True, padding=True, max_length=512)
        input_ids = inputs.input_ids.to(model.device)
        attention_mask = inputs.attention_mask.to(model.device)
    
        outputs = model(input_ids, attention_mask=attention_mask)
        logits = outputs.logits
        probabilities = F.softmax(logits, dim=1)
        predicted_label = torch.argmax(probabilities, dim=1).item()
    
        return defect_catalog[predicted_label]
    
    ```
    
- **사용 예**:
    
    ```python
    post = "차량에서 배터리 경고등이 켜졌어요."
    result = classify_post(post, model, tokenizer, defect_catalog)
    print(f"게시글 분류 결과: {result}")
    
    ```
    

---

# sentiment.ipynb

**주제**: 감정 분석

## 주요 내용

- **감정 분석**:
    - 주어진 텍스트 데이터를 바탕으로 감정 상태를 분석.
    - 감정 상태를 분류하기 위해 사전 학습된 모델을 사용하며, 긍정, 중립, 부정으로 분류.

## 코드 설명

- **감정 분석 모델 로드 및 설정**:
    
    ```python
    from transformers import pipeline
    
    sentiment_analysis = pipeline("sentiment-analysis")
    
    ```
    
- **감정 분석 함수**:
    
    ```python
    def analyze_sentiment(text):
        result = sentiment_analysis(text)
        return result
    
    ```
    
- **사용 예**:
    
    ```python
    text = "오늘은 정말 기분이 좋다!"
    sentiment_result = analyze_sentiment(text)
    print(sentiment_result)
    
    ```
    

---

# summary_llm.ipynb

**주제**: 텍스트 요약

## 주요 내용

- **LLM을 사용한 텍스트 요약**:
    - 긴 텍스트를 간결하게 요약하는 기능.
    - 사전 학습된 언어 모델을 활용하여 긴 문장을 요약된 문장으로 변환.

## 코드 설명

- **요약 모델 로드 및 설정**:
    
    ```python
    from transformers import pipeline
    
    summarizer = pipeline("summarization")
    
    ```
    
- **요약 함수**:
    
    ```python
    def summarize_text(text, max_length=150, min_length=30):
        summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
        return summary[0]['summary_text']
    
    ```
    
- **사용 예**:
    
    ```python
    long_text = "최근 몇 달 동안 차량이 이상하게 느껴졌습니다. 처음에는 가벼운 엔진 경고등이 들어왔고, 그때마다 정비소에 방문해 점검을 받았습니다."
    summary_result = summarize_text(long_text)
    print(summary_result)
    
    ```
    

---

이와 같은 마크다운 정리를 통해 각 파일의 핵심 내용을 요약하고, 코드 사용 방법과 주요 기능을 쉽게 이해할 수 있도록 설명했습니다. 필요한 경우 파일의 위치나 내용을 추가적으로 설명하여 더욱 상세한 README 파일을 작성할 수 있습니다.