"""
오색그린야드호텔 리뷰 분석 웹 애플리케이션 (간단 버전)
"""
import os
import uuid
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
import pandas as pd

# Flask 앱 초기화
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# 업로드 설정
UPLOAD_FOLDER = Path('uploads')
ALLOWED_EXTENSIONS = {'csv'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB 제한

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# 업로드 폴더 생성
UPLOAD_FOLDER.mkdir(exist_ok=True)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def allowed_file(filename):
    """파일 확장자 검증"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_session_id():
    """세션 ID 생성"""
    return str(uuid.uuid4())

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """파일 업로드 처리"""
    try:
        if 'file' not in request.files:
            flash('파일이 선택되지 않았습니다.', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('파일이 선택되지 않았습니다.', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # 세션 ID 생성
            session_id = generate_session_id()
            session_folder = UPLOAD_FOLDER / session_id
            session_folder.mkdir(exist_ok=True)
            
            # 파일 저장
            filename = 'data.csv'
            file_path = session_folder / filename
            file.save(str(file_path))
            
            logger.info(f"파일 저장 완료: {file_path}")
            
            flash('파일이 성공적으로 업로드되었습니다.', 'success')
            return redirect(url_for('analyze', session_id=session_id))
        else:
            flash('CSV 파일만 업로드 가능합니다.', 'error')
            return redirect(request.url)
            
    except Exception as e:
        logger.error(f"파일 업로드 오류: {e}")
        flash('파일 업로드 중 오류가 발생했습니다.', 'error')
        return redirect(request.url)

@app.route('/analyze/<session_id>')
def analyze(session_id):
    """분석 페이지"""
    return render_template('analyze.html', session_id=session_id)

@app.route('/api/analyze/<session_id>', methods=['POST'])
def start_analysis(session_id):
    """분석 API (간단 버전)"""
    try:
        logger.info(f"분석 시작: {session_id}")
        
        session_folder = UPLOAD_FOLDER / session_id
        csv_file = session_folder / 'data.csv'
        
        if not csv_file.exists():
            return jsonify({'error': 'CSV 파일을 찾을 수 없습니다.'}), 404
        
        # 간단한 데이터 분석
        df = pd.read_csv(csv_file)
        
        # 기본 통계
        total_reviews = len(df)
        average_rating = df['평점'].mean() if '평점' in df.columns else 0
        
        # 감정 분석 (간단한 규칙)
        if '평점' in df.columns:
            positive = len(df[df['평점'] >= 8])
            negative = len(df[df['평점'] <= 6])
            neutral = total_reviews - positive - negative
            
            positive_ratio = (positive / total_reviews) * 100
            negative_ratio = (negative / total_reviews) * 100
            neutral_ratio = (neutral / total_reviews) * 100
        else:
            positive_ratio = negative_ratio = neutral_ratio = 0
        
        # Aspect 분석 (간단한 키워드 매칭)
        aspect_keywords = {
            '청결': ['청결', '깨끗', '더럽', '지저분', '먼지', '바닥', '청소', '깔끔', '위생'],
            '시설/온수': ['시설', '온수', '샤워', '온도', '따뜻', '차갑', '잠금장치', '리모델링', '노후', '낡'],
            '직원응대': ['직원', '응대', '서비스', '친절', '불친절', '태도', '안내', '프론트'],
            '가격': ['가격', '비싸', '저렴', '가성비', '요금', '비용', '패키지', '강정', '조식'],
            '온천수': ['온천', '탄산', '온천수', '탕', '사우나', '찜질방', '목욕', '온천욕']
        }
        
        # 텍스트 데이터가 있는 경우 Aspect 분석
        aspect_results = {}
        if '내용' in df.columns:
            for aspect, keywords in aspect_keywords.items():
                mention_count = 0
                for keyword in keywords:
                    mention_count += df['내용'].str.contains(keyword, na=False).sum()
                aspect_results[aspect] = mention_count
        
        # 우선순위 계산 (간단한 버전)
        if aspect_results:
            top_aspect = max(aspect_results.items(), key=lambda x: x[1])[0]
        else:
            top_aspect = '분석 완료'
        
        summary = {
            'total_reviews': total_reviews,
            'average_rating': round(average_rating, 2),
            'positive_ratio': round(positive_ratio, 1),
            'negative_ratio': round(negative_ratio, 1),
            'neutral_ratio': round(neutral_ratio, 1),
            'top_priority': top_aspect,
            'data_period': '성공',
            'files': {
                'html_report': None,
                'pdf_report': None,
                'pptx_summary': None
            }
        }
        
        logger.info(f"분석 완료: {session_id}")
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"분석 오류: {e}")
        import traceback
        logger.error(f"상세 오류: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/results/<session_id>')
def results(session_id):
    """결과 페이지 (간단 버전)"""
    try:
        session_folder = UPLOAD_FOLDER / session_id
        csv_file = session_folder / 'data.csv'
        
        if not csv_file.exists():
            flash('업로드된 파일을 찾을 수 없습니다.', 'error')
            return redirect(url_for('index'))
        
        # 간단한 분석 수행
        df = pd.read_csv(csv_file)
        total_reviews = len(df)
        average_rating = df['평점'].mean() if '평점' in df.columns else 0
        
        if '평점' in df.columns:
            positive = len(df[df['평점'] >= 8])
            negative = len(df[df['평점'] <= 6])
            neutral = total_reviews - positive - negative
            
            positive_ratio = (positive / total_reviews) * 100
            negative_ratio = (negative / total_reviews) * 100
            neutral_ratio = (neutral / total_reviews) * 100
        else:
            positive_ratio = negative_ratio = neutral_ratio = 0
        
        # Aspect 분석 (간단한 키워드 매칭)
        aspect_keywords = {
            '청결': ['청결', '깨끗', '더럽', '지저분', '먼지', '바닥', '청소', '깔끔', '위생'],
            '시설/온수': ['시설', '온수', '샤워', '온도', '따뜻', '차갑', '잠금장치', '리모델링', '노후', '낡'],
            '직원응대': ['직원', '응대', '서비스', '친절', '불친절', '태도', '안내', '프론트'],
            '가격': ['가격', '비싸', '저렴', '가성비', '요금', '비용', '패키지', '강정', '조식'],
            '온천수': ['온천', '탄산', '온천수', '탕', '사우나', '찜질방', '목욕', '온천욕']
        }
        
        # 텍스트 데이터가 있는 경우 Aspect 분석
        aspect_results = {}
        if '내용' in df.columns:
            for aspect, keywords in aspect_keywords.items():
                mention_count = 0
                for keyword in keywords:
                    mention_count += df['내용'].str.contains(keyword, na=False).sum()
                aspect_results[aspect] = mention_count
        
        # 우선순위 계산 (간단한 버전)
        if aspect_results:
            top_aspect = max(aspect_results.items(), key=lambda x: x[1])[0]
        else:
            top_aspect = '분석 완료'
        
        session_info = {
            'session_id': session_id,
            'created_at': datetime.now().isoformat(),
            'summary': {
                'total_reviews': total_reviews,
                'average_rating': round(average_rating, 2),
                'positive_ratio': positive_ratio,
                'negative_ratio': negative_ratio,
                'neutral_ratio': neutral_ratio,
                'top_priority': top_aspect,
                'data_period': '성공',
                'files': {
                    'html_report': None,
                    'pdf_report': None,
                    'pptx_summary': None
                }
            },
            'analysis_results': {
                'KPI': {'총_리뷰_수': total_reviews},
                '우선순위': {'상위_3개': []},
                '고급분석': False
            }
        }
        
        return render_template('results.html', 
                             session_info=session_info,
                             session_id=session_id)
        
    except Exception as e:
        logger.error(f"결과 페이지 오류: {e}")
        import traceback
        logger.error(f"상세 오류: {traceback.format_exc()}")
        flash('결과를 불러오는 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('index'))

@app.route('/api/plot/<session_id>/<plot_name>')
def get_plot(session_id, plot_name):
    """그래프 이미지 제공 (간단 버전에서는 지원하지 않음)"""
    try:
        # 현재 간소화된 버전에서는 이미지가 생성되지 않음
        return jsonify({
            'error': '현재 버전에서는 이미지 차트를 지원하지 않습니다. 분석 결과는 텍스트로만 제공됩니다.'
        }), 404
        
    except Exception as e:
        logger.error(f"이미지 제공 오류: {e}")
        return jsonify({'error': '이미지를 불러오는 중 오류가 발생했습니다.'}), 500

@app.route('/download/<session_id>/<file_type>')
def download_file(session_id, file_type):
    """파일 다운로드 (간단 버전에서는 지원하지 않음)"""
    try:
        # 현재 간소화된 버전에서는 리포트 파일이 생성되지 않음
        if file_type in ['html', 'pdf', 'pptx']:
            flash(f'현재 버전에서는 {file_type.upper()} 리포트 다운로드를 지원하지 않습니다. 결과 페이지에서 직접 확인해주세요.', 'info')
            return redirect(url_for('results', session_id=session_id))
        else:
            flash('지원하지 않는 파일 형식입니다.', 'error')
            return redirect(url_for('results', session_id=session_id))
            
    except Exception as e:
        logger.error(f"파일 다운로드 오류: {e}")
        flash('파일 다운로드 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('results', session_id=session_id))

@app.errorhandler(413)
def too_large(e):
    """파일 크기 초과 오류"""
    flash('파일 크기가 너무 큽니다. (최대 16MB)', 'error')
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(e):
    """페이지 없음 오류"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    """서버 오류"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    # 배포 환경에서는 환경 변수에서 포트를 가져옴
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    # 배포 환경에서는 0.0.0.0으로 바인딩
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
