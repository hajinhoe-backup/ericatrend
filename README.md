# Notice
## 폴더 구조 변경
- elk : elk 스택 관련
  - collector : 크롤러
  - data : 데이터가 저장되는 곳
  - config : elk 설정 파일
- static : 플라스크 정적 파일
  - js
  - css
- templates
# dependency
Bootstrap v4.3.1 (CDN:한국서버 있음)

Font Awesome v5.7.2 (CDN:한국서버 있음)
# To-do
## 범위 구체화
전자 제품의 어떤 제품을, 몇년 이내 제품을 수집할 것인지? 혹은 다른 세부사항은? -> 의미있는 결과를 도출할 수 있는 제품군일지?
## 일렉서치
### 크롤러 개발
1. 아마존 리뷰 수집 크롤러 자동화 및 모듈화
## 프론트엔드 개발
1. 프론트 엔드 예시 페이지 개발


## 웹서버
export FLASK_APP=__init__.py #최초 1회만
flask run --host=0.0.0.0