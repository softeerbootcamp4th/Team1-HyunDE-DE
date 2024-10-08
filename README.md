# Team HyunDE

### 저희 팀은 투싼을 대상으로 이슈를 트래킹하고, 현재의 소비자 반응과 과거 이슈 당시의 소비자 반응을 비교분석하여 의사결정에 도움을 줄 수 있는 서비스 제작을 목표로 하였습니다.

<img src="https://github.com/ssangmin-junior/softeer_wiki/blob/main/files/grafana.png?raw=true" >

##### 저희 시스템은 3시간 배치 스케줄로 동작하는 서비스 ,그리고 매일의 이슈를 종합하여 분석하는 데일리 배치 서비스를 제공합니다. 
#### Three hours Batch
##### **Live Watch** 
<img src="https://github.com/ssangmin-junior/softeer_wiki/blob/main/files/dash1.png?raw=true" >
  - 투싼에 대해 이야기하는 게시글과 댓글의 변화량을 감지하여 그래프로 나타내었습니다.
  - 투싼에 대한 게시글들의 조회수가 크게 증가하거나,
  - 게시글과 댓글이 많이 생성될 수록 그래프가 가파르게 상승함을 알 수 있습니다.

<img src="https://github.com/ssangmin-junior/softeer_wiki/blob/main/files/dash2.png?raw=true" >

##### **Most Increasing Post**

  - 3시간 이전 커뮤니티 스냅샷과 비교하였을 때, 조회수가 가장 크게 증가한 게시글을 간략히 보여줍니다.

##### **Content Having Keywords**

  - 사용자가 사전에 설정한 키워드가 포함된 새로운 게시글이나 댓글을 감지하면 그 정보를 제공합니다.
  - 현재 설정된 키워드는 “결함”과  “고장”으로 이를 포함한 게시글 혹은 댓글을 감지 중에 있습니다.

#### **E-Mail Alert**
<img src="https://github.com/ssangmin-junior/softeer_wiki/blob/main/files/dash5.png?raw=true" >
  - 라이브워치에 대한 정보를 메일 알림으로도 제공을 합니다.
  - 키워드가 포함된 게시글이나 댓글, 혹은 뉴스가 발견되면 메일에서도 알림으로 받아볼 수 있습니다.

#### Daily Batch

#### **Similar DashBoard**

<img src="https://github.com/ssangmin-junior/softeer_wiki/blob/main/files/dash3.png?raw=true" >

  - 현재 투싼에 대한 소비자들의  관심도 그래프와 가장 유사한 과거 케이스를 보여줍니다.
  - 유사한 차종과 날짜, 유사도, 결함분류, 대상수량을 볼 수 있습니다.
  - 여러 케이스중 하나의 케이스를 선택하면 Similar Graph에 그 case의 그래프를 보여줍니다.
  - Similar Graph에서는 선택한 case의 그래프와 투싼의 그래프를 함께 보여줍니다.
  - Score가 40점이 넘으면 위험수준임을 알 수 있습니다.
  - 과거의 케이스에서는 이런 변화가 있었으니 현재 상황에서도 비슷한 양상으로 진행 될 가능성이 있음을 나타냅니다.

#### **Customer Reaction**
<img src="https://github.com/ssangmin-junior/softeer_wiki/blob/main/files/dash4.png?raw=true" >
  - 투싼에 대해 트래킹 하는 게시글이나 댓글에 대한 정보가 있는 날짜를 선택하면
  - 선택한 날짜의 Sentiment Pie Chart가 보이게됩니다
  - 또한 해당 날짜에 comment들에 대한 워드 클라우드를 확인 할 수 있고, 해당  날짜의 ViewCount가 가장 높은 게시글 또한 확인 할 수 있습니다.



