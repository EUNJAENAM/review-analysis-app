# 오색그린야드호텔 리뷰 분석 시스템

고객 리뷰 데이터를 분석하여 인사이트를 도출하는 웹 애플리케이션입니다.

## 🚀 배포된 애플리케이션

### Render 배포
- **URL**: https://your-app-name.onrender.com
- **배포 방법**: 아래 Render 배포 가이드 참조

### Railway 배포
- **URL**: https://your-app-name.railway.app
- **배포 방법**: 아래 Railway 배포 가이드 참조

## 📋 주요 기능

1. **데이터 업로드**: CSV 파일 업로드 및 분석
2. **KPI 분석**: 총 리뷰 수, 평균 평점, 감정 분포
3. **트렌드 분석**: 연도별, 분기별 트렌드
4. **Aspect 분석**: 청결, 시설, 직원응대, 가격, 온천수
5. **우선순위 분석**: 개선사항 우선순위 점수
6. **시각화**: 다양한 차트와 그래프
7. **리포트 생성**: HTML, PDF, PPTX 형식

## 🛠️ 기술 스택

- **Backend**: Python, Flask
- **Data Analysis**: Pandas, NumPy, Scikit-learn
- **Visualization**: Matplotlib
- **Frontend**: HTML, CSS, Bootstrap, JavaScript
- **Deployment**: Render, Railway, Vercel

## 📦 설치 및 실행

### 로컬 실행
```bash
# 1. 저장소 클론
git clone https://github.com/your-username/review-analysis.git
cd review-analysis

# 2. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 애플리케이션 실행
python run_web.py
```

### 웹 브라우저에서 접속
```
http://localhost:5000
```

## 🚀 배포 가이드

### Render 배포 (추천)

1. **GitHub에 코드 업로드**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Render 계정 생성**
   - https://render.com 에서 계정 생성

3. **새 Web Service 생성**
   - "New Web Service" 클릭
   - GitHub 저장소 연결
   - 다음 설정 적용:
     - **Name**: review-analysis-app
     - **Environment**: Python
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app`

4. **환경 변수 설정**
   - `FLASK_ENV`: `production`
   - `SECRET_KEY`: 랜덤 문자열 생성

5. **배포 완료**
   - 자동으로 배포가 시작됩니다
   - 배포 완료 후 제공되는 URL로 접속

### Railway 배포

1. **Railway 계정 생성**
   - https://railway.app 에서 계정 생성

2. **새 프로젝트 생성**
   - "New Project" 클릭
   - "Deploy from GitHub repo" 선택
   - GitHub 저장소 연결

3. **자동 배포**
   - Railway가 자동으로 감지하여 배포
   - 배포 완료 후 제공되는 URL로 접속

### Vercel 배포

1. **Vercel 계정 생성**
   - https://vercel.com 에서 계정 생성

2. **새 프로젝트 생성**
   - "New Project" 클릭
   - GitHub 저장소 연결

3. **설정 확인**
   - `vercel.json` 파일이 올바르게 설정되었는지 확인

4. **배포 완료**
   - 자동으로 배포가 시작됩니다

## 📊 사용 방법

1. **홈페이지 접속**: 배포된 URL로 접속
2. **파일 업로드**: CSV 파일 선택 및 업로드
3. **분석 시작**: "분석 시작" 버튼 클릭
4. **결과 확인**: 분석 완료 후 결과 페이지에서 확인
5. **리포트 다운로드**: HTML, PDF 형식으로 다운로드

## 📁 프로젝트 구조

```
Reviewanalysis/
├── app.py                 # Flask 애플리케이션
├── run_web.py            # 로컬 실행 스크립트
├── requirements.txt      # Python 의존성
├── src/                  # 소스 코드
│   ├── config.py        # 설정 파일
│   ├── load.py          # 데이터 로드
│   ├── analysis.py      # 분석 로직
│   ├── plots.py         # 시각화
│   ├── report.py        # 리포트 생성
│   └── export.py        # 파일 내보내기
├── templates/           # HTML 템플릿
├── static/             # 정적 파일
├── data/               # 샘플 데이터
└── assets/             # 폰트 등 자산
```

## 🔧 환경 변수

- `FLASK_ENV`: Flask 환경 (development/production)
- `SECRET_KEY`: Flask 시크릿 키
- `PORT`: 포트 번호 (배포 환경에서 자동 설정)

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 👥 기여

버그 리포트나 기능 요청은 GitHub Issues를 통해 제출해주세요.

## 📞 문의

- **회사**: (주)파로스
- **이메일**: contact@paros.com
- **웹사이트**: https://paros.com
