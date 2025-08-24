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

# 차트 생성 모듈 import
try:
    from src.plots import PlotGenerator
    from src.config import FIGURES_DIR
    CHARTS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"차트 모듈 import 실패: {e}")
    CHARTS_AVAILABLE = False

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
        
        # Aspect별 감정 분석
        aspect_sentiment = {}
        if '내용' in df.columns and '평점' in df.columns:
            for aspect, keywords in aspect_keywords.items():
                aspect_mentions = df[df['내용'].str.contains('|'.join(keywords), na=False)]
                if len(aspect_mentions) > 0:
                    positive_count = len(aspect_mentions[aspect_mentions['평점'] >= 8])
                    negative_count = len(aspect_mentions[aspect_mentions['평점'] <= 6])
                    neutral_count = len(aspect_mentions) - positive_count - negative_count
                    
                    aspect_sentiment[aspect] = {
                        'total': len(aspect_mentions),
                        'positive': positive_count,
                        'negative': negative_count,
                        'neutral': neutral_count,
                        'positive_ratio': round((positive_count / len(aspect_mentions)) * 100, 1),
                        'negative_ratio': round((negative_count / len(aspect_mentions)) * 100, 1),
                        'neutral_ratio': round((neutral_count / len(aspect_mentions)) * 100, 1)
                    }
        
        # 개선사항 우선순위 점수 계산
        priority_scores = {}
        if aspect_results:
            for aspect, mention_count in aspect_results.items():
                if aspect in aspect_sentiment:
                    # 부정 비율이 높을수록 높은 점수 (우선순위)
                    negative_ratio = aspect_sentiment[aspect]['negative_ratio']
                    mention_weight = min(mention_count / 10, 1.0)  # 언급 횟수 가중치
                    priority_scores[aspect] = round(negative_ratio * mention_weight, 1)
                else:
                    priority_scores[aspect] = 0.0
        
        # 우선순위 계산 (개선된 버전)
        if priority_scores:
            top_aspect = max(priority_scores.items(), key=lambda x: x[1])[0]
        elif aspect_results:
            top_aspect = max(aspect_results.items(), key=lambda x: x[1])[0]
        else:
            top_aspect = '분석 완료'
        
        # 차트 생성 (가능한 경우)
        chart_files = {}
        if CHARTS_AVAILABLE:
            try:
                # 출력 디렉토리 설정
                output_dir = session_folder / 'charts'
                output_dir.mkdir(exist_ok=True)
                
                # PlotGenerator 초기화
                plotter = PlotGenerator(output_dir)
                
                # 감정 분포 파이 차트 생성
                sentiment_data = {
                    '긍정': positive,
                    '부정': negative,
                    '중립': neutral
                }
                sentiment_chart = plotter.create_sentiment_pie_chart(sentiment_data)
                if sentiment_chart:
                    chart_files['sentiment'] = sentiment_chart
                
                # 연도별 트렌드 차트 (날짜 데이터가 있는 경우)
                if '작성일자' in df.columns:
                    try:
                        df['날짜'] = pd.to_datetime(df['작성일자'])
                        df['연도'] = df['날짜'].dt.year
                        yearly_data = df.groupby('연도').agg({
                            '평점': ['count', 'mean']
                        }).round(2)
                        yearly_data.columns = ['리뷰_수', '평균_평점']
                        
                        trend_chart = plotter.create_yearly_trend_plot(yearly_data)
                        if trend_chart:
                            chart_files['trend'] = trend_chart
                    except Exception as e:
                        logger.warning(f"연도별 트렌드 차트 생성 실패: {e}")
                
                # 부정 키워드 차트 (텍스트 데이터가 있는 경우)
                if '내용' in df.columns:
                    try:
                        # 부정 키워드 분석
                        negative_keywords = [
                            '아쉽', '실망', '별로', '안좋', '나쁘', '불편', '문제', '결함', '고장',
                            '부족', '떨어지', '낮', '안되', '못하', '싫', '짜증', '화나', '불쾌',
                            '실종', '허', '늘어지', '떨어지', '낡', '오래', '노후', '지저분', '더럽',
                            '차갑', '춥', '시끄럽', '소음', '비싸', '바가지', '불친절', '무시',
                            '격양', '말문막힘', '아쉬워', '후회', '다시안갈', '추천안함'
                        ]
                        
                        keyword_counts = []
                        for keyword in negative_keywords:
                            count = df['내용'].str.contains(keyword, na=False).sum()
                            if count > 0:
                                keyword_counts.append((keyword, count))
                        
                        # 상위 10개 키워드 선택
                        keyword_counts.sort(key=lambda x: x[1], reverse=True)
                        top_keywords = keyword_counts[:10]
                        
                        if top_keywords:
                            keywords_chart = plotter.create_negative_keywords_bar(top_keywords)
                            if keywords_chart:
                                chart_files['keywords'] = keywords_chart
                    except Exception as e:
                        logger.warning(f"부정 키워드 차트 생성 실패: {e}")
                
                logger.info(f"차트 생성 완료: {list(chart_files.keys())}")
                
            except Exception as e:
                logger.error(f"차트 생성 중 오류: {e}")
        
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
            },
            'charts': chart_files if CHARTS_AVAILABLE else {},
            'aspect_sentiment': aspect_sentiment,
            'priority_scores': priority_scores,
            'key_insights': {
                'overall_sentiment': '긍정' if positive_ratio > negative_ratio else '부정' if negative_ratio > positive_ratio else '중립',
                'main_strength': max(aspect_sentiment.items(), key=lambda x: x[1]['positive_ratio'])[0] if aspect_sentiment else '분석 불가',
                'main_weakness': max(aspect_sentiment.items(), key=lambda x: x[1]['negative_ratio'])[0] if aspect_sentiment else '분석 불가',
                'improvement_potential': round((negative_ratio / 100) * total_reviews, 0) if negative_ratio > 0 else 0
            },
            'strategic_recommendations': {
                'immediate_action': top_aspect,
                'long_term_focus': '고객 만족도 향상' if negative_ratio > 30 else '서비스 품질 유지',
                'priority_level': '높음' if negative_ratio > 40 else '중간' if negative_ratio > 20 else '낮음'
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
        
        # 차트 생성 (가능한 경우)
        chart_files = {}
        if CHARTS_AVAILABLE:
            try:
                # 출력 디렉토리 설정
                output_dir = session_folder / 'charts'
                output_dir.mkdir(exist_ok=True)
                
                # PlotGenerator 초기화
                plotter = PlotGenerator(output_dir)
                
                # 감정 분포 파이 차트 생성
                sentiment_data = {
                    '긍정': positive,
                    '부정': negative,
                    '중립': neutral
                }
                sentiment_chart = plotter.create_sentiment_pie_chart(sentiment_data)
                if sentiment_chart:
                    chart_files['sentiment'] = sentiment_chart
                
                # 연도별 트렌드 차트 (날짜 데이터가 있는 경우)
                if '작성일자' in df.columns:
                    try:
                        df['날짜'] = pd.to_datetime(df['작성일자'])
                        df['연도'] = df['날짜'].dt.year
                        yearly_data = df.groupby('연도').agg({
                            '평점': ['count', 'mean']
                        }).round(2)
                        yearly_data.columns = ['리뷰_수', '평균_평점']
                        
                        trend_chart = plotter.create_yearly_trend_plot(yearly_data)
                        if trend_chart:
                            chart_files['trend'] = trend_chart
                    except Exception as e:
                        logger.warning(f"연도별 트렌드 차트 생성 실패: {e}")
                
                # 부정 키워드 차트 (텍스트 데이터가 있는 경우)
                if '내용' in df.columns:
                    try:
                        # 부정 키워드 분석
                        negative_keywords = [
                            '아쉽', '실망', '별로', '안좋', '나쁘', '불편', '문제', '결함', '고장',
                            '부족', '떨어지', '낮', '안되', '못하', '싫', '짜증', '화나', '불쾌',
                            '실종', '허', '늘어지', '떨어지', '낡', '오래', '노후', '지저분', '더럽',
                            '차갑', '춥', '시끄럽', '소음', '비싸', '바가지', '불친절', '무시',
                            '격양', '말문막힘', '아쉬워', '후회', '다시안갈', '추천안함'
                        ]
                        
                        keyword_counts = []
                        for keyword in negative_keywords:
                            count = df['내용'].str.contains(keyword, na=False).sum()
                            if count > 0:
                                keyword_counts.append((keyword, count))
                        
                        # 상위 10개 키워드 선택
                        keyword_counts.sort(key=lambda x: x[1], reverse=True)
                        top_keywords = keyword_counts[:10]
                        
                        if top_keywords:
                            keywords_chart = plotter.create_negative_keywords_bar(top_keywords)
                            if keywords_chart:
                                chart_files['keywords'] = keywords_chart
                    except Exception as e:
                        logger.warning(f"부정 키워드 차트 생성 실패: {e}")
                
                logger.info(f"차트 생성 완료: {list(chart_files.keys())}")
                
            except Exception as e:
                logger.error(f"차트 생성 중 오류: {e}")
        
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
                },
                'charts': chart_files if CHARTS_AVAILABLE else {},
                'aspect_sentiment': aspect_sentiment,
                'priority_scores': priority_scores,
                'key_insights': {
                    'overall_sentiment': '긍정' if positive_ratio > negative_ratio else '부정' if negative_ratio > positive_ratio else '중립',
                    'main_strength': max(aspect_sentiment.items(), key=lambda x: x[1]['positive_ratio'])[0] if aspect_sentiment else '분석 불가',
                    'main_weakness': max(aspect_sentiment.items(), key=lambda x: x[1]['negative_ratio'])[0] if aspect_sentiment else '분석 불가',
                    'improvement_potential': round((negative_ratio / 100) * total_reviews, 0) if negative_ratio > 0 else 0
                },
                'strategic_recommendations': {
                    'immediate_action': top_aspect,
                    'long_term_focus': '고객 만족도 향상' if negative_ratio > 30 else '서비스 품질 유지',
                    'priority_level': '높음' if negative_ratio > 40 else '중간' if negative_ratio > 20 else '낮음'
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
    """그래프 이미지 제공"""
    try:
        session_folder = UPLOAD_FOLDER / session_id
        charts_folder = session_folder / 'charts'
        
        # 차트 파일 경로 설정
        chart_files = {
            'sentiment': 'sentiment_distribution.png',
            'trend': 'yearly_trend.png',
            'keywords': 'negative_keywords.png'
        }
        
        if plot_name not in chart_files:
            return jsonify({'error': '지원하지 않는 차트 유형입니다.'}), 404
        
        chart_file = charts_folder / chart_files[plot_name]
        
        if not chart_file.exists():
            return jsonify({
                'error': f'차트 파일을 찾을 수 없습니다: {plot_name}',
                'available': list(chart_files.keys())
            }), 404
        
        return send_file(chart_file, mimetype='image/png')
        
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
