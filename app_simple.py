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
        
        summary = {
            'total_reviews': total_reviews,
            'average_rating': round(average_rating, 2),
            'positive_ratio': round(positive_ratio, 1),
            'negative_ratio': round(negative_ratio, 1),
            'neutral_ratio': round(neutral_ratio, 1),
            'top_priority': '분석 완료',
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
        
        session_info = {
            'session_id': session_id,
            'created_at': datetime.now().isoformat(),
            'summary': {
                'total_reviews': total_reviews,
                'average_rating': round(average_rating, 2),
                'positive_ratio': positive_ratio,
                'negative_ratio': negative_ratio,
                'neutral_ratio': neutral_ratio,
                'top_priority': '분석 완료',
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
        flash('결과를 불러오는 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('index'))

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
