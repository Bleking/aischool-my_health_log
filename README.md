<img width="1856" height="772" alt="헬스케어 관리자 페이지 (6)" src="https://github.com/user-attachments/assets/a4daaefc-09ca-4677-ab83-6e5dd68e4d00" /><img width="1860" height="767" alt="헬스케어 관리자 페이지 (5)" src="https://github.com/user-attachments/assets/3a1a400b-ae95-4e7e-ab12-84fa0747fdca" /><img width="1862" height="770" alt="헬스케어 관리자 페이지 (3)" src="https://github.com/user-attachments/assets/a79e1598-c580-4463-9636-e27830c8512d" /># 인공지능사관학교 7기 미니프로젝트 4주차

## 프로젝트 소개
건강 기록을 관리하고 분석하는 나만의 API를 설계·구현·배포하는 개인 과제

몸무게·키·혈압·혈당 등 건강 수치를 기록하면, 서버가 BMI를 자동 계산하고 건강 상태를 분류하여, 그동안 쌓인 기록으로 통계를 제공

## 기능 목록
### 사용자
- 신체 조건 입력 (몸무게, 키)
- 건강 상태 값 입력 (수축기 및 이완기 혈압, 공복 혈당)
- (선택 사항) 걸음걸이, 수면 시간, 메모
- 필수 사항 모두 입력시 BMI 수치 및 상태, 혈압 상테, 혈당 상태 확인 가능

### 관리자
- 회원별 개인 및 건강 정보 조회
- 회원별 건강 정보 수정 및 삭제

## 실행 방법
### 사용자 가이드
1. 회원가입/로그인: 성명과 전화번호를 입력합니다. 새로 이용하는 경우 회원가입이 되며, 기존에 회원 가입을 한 적이 있으면 로그인이 됩니다.
<img width="640" height="845" alt="헬스케어 로그인 화면" src="https://github.com/user-attachments/assets/62615634-fcaf-4025-afd1-a85e32807f11" />

2. 로그인을 하면 다음과 같이 신체 및 건강 정보를 입력하는 페이지가 나옵니다.
몸무게, 키, 수축기 및 이완기 혈압, 공복 혈당을 필수 입력 사항입니다.
<img width="957" height="907" alt="헬스케어 사용자 설문 화면 (1)" src="https://github.com/user-attachments/assets/46492855-894c-4515-a85a-29fe3b6cc65c" />

걸음 걸이, 수면 시간, 메모는 선택사항입니다. 필수 항목을 모두 체우고 나면 제출하기 버튼을 누릅니다.
<img width="932" height="907" alt="헬스케어 사용자 설문 화면 (2)" src="https://github.com/user-attachments/assets/5ed47dfb-ed81-4384-aeb6-af8997fc24c8" />

3. 검사 결과 화면
다음과 같이 BMI 수치 및 상태, 그리고 혈압, 공복 상태를 확인할 수 있습니다. 
<img width="917" height="911" alt="헬스케어 사용자 결과 화면" src="https://github.com/user-attachments/assets/96df4c65-f579-4b12-bee9-d8188ab5d884" />

### 관리자 가이드
1. 관리자 로그인을 하기 위해서는 관리자로 등록된 사람의 이름과 전화 번호를 입력합니다.
<img width="640" height="845" alt="헬스케어 로그인 화면" src="https://github.com/user-attachments/assets/fdbb1a76-6bec-4df7-810d-d9dab8b1f480" />

2. 그러면 다음과 같이 건강 검사를 진행한 회원의 정보를 확인할 수 있습니다.
<img width="1855" height="775" alt="헬스케어 관리자 페이지 (1)" src="https://github.com/user-attachments/assets/9faa0a98-f432-4b1e-a699-30bf7e3ed307" />

3. 회원 건강 정보 수정
또한 특정 회원의 신체 정보 및 건강 수치 정보를 수정하기 위해서는 수정 버튼을 누릅니다.
<img width="1857" height="772" alt="헬스케어 관리자 페이지 (2)" src="https://github.com/user-attachments/assets/d06ead34-3ea0-48d8-99d7-28490760cd58" />

정승원 회원의 수축기 혈압 값은 현재 80입니다.
<img width="1862" height="770" alt="헬스케어 관리자 페이지 (3)" src="https://github.com/user-attachments/assets/5d20aaea-7155-454b-bc7b-96f97ffa77c4" />

이 값을 75로 수정해보겠습니다.
<img width="1865" height="776" alt="헬스케어 관리자 페이지 (4)" src="https://github.com/user-attachments/assets/c7148abe-bbc7-4c97-ac5b-c8a37aad5e23" />

수정을 완료했으면 수정 완료 버튼을 누릅니다.
<img width="1860" height="767" alt="헬스케어 관리자 페이지 (5)" src="https://github.com/user-attachments/assets/c4e3c254-e325-41ed-885a-1f36b4a313f0" />

수정 사항이 정상적으로 적용되었습니다.
<img width="1856" height="772" alt="헬스케어 관리자 페이지 (6)" src="https://github.com/user-attachments/assets/c0a10e0c-a597-4cd6-aa09-e94eb57264a3" />

4. 회원 건강 정보 삭제
한 회원의 특정 건강 정보를 삭제하려면 삭제 버튼을 누릅니다.
<img width="1857" height="772" alt="헬스케어 관리자 페이지 (7)" src="https://github.com/user-attachments/assets/34395af3-4742-4bf1-97a4-0caad61fc584" />

정상적으로 삭제되었습니다.
<img width="1857" height="757" alt="헬스케어 관리자 페이지 (8)" src="https://github.com/user-attachments/assets/1d010d36-765d-467b-8044-e6176b96558c" />


## 기술 스택
- FastAPI
- Docker
- SQLite
- CRUD

## ERD
<img width="785" height="676" alt="헬스케어 ERD" src="https://github.com/user-attachments/assets/60ea255b-c534-4bde-9543-31769c881ce5" />


## 접속 URL
http://52.78.241.246:8001/
