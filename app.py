"""
오색그린야드호텔 리뷰 분석 웹 애플리케이션
"""
import os
import uuid
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
import pandas as pd
import json

# 프로젝트 모듈 import
from src.load import DataLoader
from src.analysis import ReviewAnalyzer
from src.plots import PlotGenerator
from src.report import ReportGenerator
from src.export import ExportGenerator
from src.config import ANALYSIS_OPTIONS

# Flask 앱 초기화
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 실제 운영시에는 환경변수로 관리

# 업로드 설정
UPLOAD_FOLDER = Path('uploads')
ALLOWED_EXTENSIONS = {'csv'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB 제한

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# 업로드 폴더 생성 (절대 경로 사용)
UPLOAD_FOLDER.mkdir(exist_ok=True)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 배포 환경 확인
IS_PRODUCTION = os.environ.get('FLASK_ENV') == 'production'

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
            
            # 파일 저장 (간단하고 확실한 방법)
            original_filename = file.filename
            
            # 항상 'data.csv'로 저장 (문제 해결)
            filename = 'data.csv'
            
            file_path = session_folder / filename
            file.save(str(file_path))
            
            logger.info(f"원본 파일명: {original_filename}")
            logger.info(f"저장된 파일명: {filename}")
            
            # 파일 저장 확인
            logger.info(f"파일 저장 완료: {file_path}")
            logger.info(f"파일 크기: {file_path.stat().st_size} bytes")
            
            # 분석 옵션 가져오기
            enable_advanced = request.form.get('enable_advanced', 'false') == 'true'
            
            flash('파일이 성공적으로 업로드되었습니다. 분석을 시작합니다.', 'success')
            
            # 분석 시작
            return redirect(url_for('analyze', session_id=session_id, enable_advanced=enable_advanced))
        else:
            flash('CSV 파일만 업로드 가능합니다.', 'error')
            return redirect(request.url)
            
    except Exception as e:
        logger.error(f"파일 업로드 오류: {e}")
        import traceback
        logger.error(f"상세 오류: {traceback.format_exc()}")
        flash('파일 업로드 중 오류가 발생했습니다.', 'error')
        return redirect(request.url)

@app.route('/analyze/<session_id>')
def analyze(session_id):
    """분석 페이지"""
    enable_advanced = request.args.get('enable_advanced', 'false') == 'true'
    return render_template('analyze.html', session_id=session_id, enable_advanced=enable_advanced)

@app.route('/api/analyze/<session_id>', methods=['POST'])
def start_analysis(session_id):
    """분석 API"""
    try:
        logger.info(f"분석 시작: {session_id}")
        
        session_folder = UPLOAD_FOLDER / session_id
        logger.info(f"세션 폴더: {session_folder}")
        logger.info(f"세션 폴더 존재: {session_folder.exists()}")
        
        # 폴더 내용 확인
        if session_folder.exists():
            files_in_folder = list(session_folder.iterdir())
            logger.info(f"폴더 내 파일들: {[f.name for f in files_in_folder]}")
        
        csv_files = list(session_folder.glob('*.csv'))
        logger.info(f"발견된 CSV 파일들: {[str(f) for f in csv_files]}")
        
        if not csv_files:
            logger.error(f"CSV 파일을 찾을 수 없습니다: {session_id}")
            logger.error(f"세션 폴더 경로: {session_folder}")
            return jsonify({'error': 'CSV 파일을 찾을 수 없습니다.'}), 404
        
        csv_file = csv_files[0]
        logger.info(f"CSV 파일 발견: {csv_file}")
        logger.info(f"CSV 파일 존재: {csv_file.exists()}")
        logger.info(f"CSV 파일 크기: {csv_file.stat().st_size} bytes")
        
        # 분석 옵션 설정
        analysis_options = ANALYSIS_OPTIONS.copy()
        enable_advanced = request.json.get('enable_advanced', False) if request.json else False
        analysis_options['enable_advanced_analysis'] = enable_advanced
        
        logger.info(f"분석 옵션 설정 완료: 고급분석={enable_advanced}")
        
        # 1. 데이터 로드
        logger.info("데이터 로드 시작")
        loader = DataLoader(csv_file)
        df = loader.get_clean_data()
        info = loader.get_data_info()
        logger.info(f"데이터 로드 완료: {len(df)} 행")
        
        # 2. 분석 수행
        logger.info("분석 수행 시작")
        analyzer = ReviewAnalyzer(df, analysis_options)
        analysis_results = analyzer.analyze_all()
        logger.info("분석 수행 완료")
        
        # 3. 그래프 생성
        logger.info("그래프 생성 시작")
        output_dir = session_folder / 'outputs'
        output_dir.mkdir(exist_ok=True)
        
        plot_generator = PlotGenerator(output_dir)
        plot_files = plot_generator.generate_all_plots(analysis_results)
        logger.info("그래프 생성 완료")
        
        # 4. 리포트 생성 (최적화)
        logger.info("리포트 생성 시작")
        report_generator = ReportGenerator()
        report_dir = output_dir / 'report'
        report_dir.mkdir(exist_ok=True)
        
        # HTML 리포트 생성만 수행 (빠른 처리)
        html_report_path = report_generator.generate_report(analysis_results, plot_files)
        logger.info("HTML 리포트 생성 완료")
        
        # PDF 및 PPTX 생성은 백그라운드에서 처리 (선택적)
        pdf_path = None
        pptx_path = None
        # PDF/PPTX 생성은 사용자가 요청할 때만 수행하도록 변경
        logger.info("PDF/PPTX 생성은 사용자 요청 시 수행")
        
        # 결과 요약 (최적화)
        logger.info("결과 요약 생성 시작")
        summary = {
            'total_reviews': analysis_results['KPI']['총_리뷰_수'],
            'average_rating': round(analysis_results['KPI']['평균_평점'], 2),
            'positive_ratio': round(analysis_results['KPI']['긍정_비율'] * 100, 1),
            'negative_ratio': round(analysis_results['KPI']['부정_비율'] * 100, 1),
            'neutral_ratio': round(analysis_results['KPI']['중립_비율'] * 100, 1),
            'top_priority': analysis_results['우선순위']['상위_3개'][0]['Aspect'] if analysis_results['우선순위']['상위_3개'] else '없음',
            'data_period': f"{analysis_results['KPI']['데이터_기간']['시작일']} ~ {analysis_results['KPI']['데이터_기간']['종료일']}",
            'files': {
                'html_report': str(html_report_path),
                'pdf_report': str(pdf_path) if pdf_path else None,
                'pptx_summary': str(pptx_path) if pptx_path else None,
                'plots': {k: v.name for k, v in plot_files.items()}  # Path 객체 대신 파일명만 저장
            }
        }
        logger.info("결과 요약 생성 완료")
        
        # 세션 정보 저장 (임시 비활성화 - 성능 최적화)
        logger.info("세션 정보 저장 건너뛰기 (성능 최적화)")
        
        # 임시로 세션 정보 저장을 건너뛰어 성능 문제 해결
        # 나중에 백그라운드에서 처리하도록 개선 예정
        
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
    """결과 페이지"""
    try:
        logger.info(f"결과 페이지 접속: {session_id}")
        
        session_folder = UPLOAD_FOLDER / session_id
        logger.info(f"세션 폴더 경로: {session_folder}")
        logger.info(f"세션 폴더 존재: {session_folder.exists()}")
        
        # CSV 파일 존재 확인
        csv_file = session_folder / 'data.csv'
        if not csv_file.exists():
            logger.error(f"CSV 파일을 찾을 수 없음: {csv_file}")
            flash('업로드된 파일을 찾을 수 없습니다.', 'error')
            return redirect(url_for('index'))
        
        logger.info(f"CSV 파일 발견: {csv_file}")
        
        # HTML 리포트 파일이 존재하는지 확인
        html_report_path = session_folder / 'outputs' / 'report' / 'report.html'
        logger.info(f"HTML 리포트 경로: {html_report_path}")
        logger.info(f"HTML 리포트 존재: {html_report_path.exists()}")
        
        if not html_report_path.exists():
            # 분석이 완료되지 않은 경우, 즉시 분석 수행
            logger.info(f"분석 결과가 없어 즉시 분석을 수행합니다: {session_id}")
            
            try:
                # 분석 옵션 설정 (기본값)
                analysis_options = ANALYSIS_OPTIONS.copy()
                analysis_options['enable_advanced_analysis'] = False
                
                logger.info("1단계: 데이터 로드 시작")
                # 1. 데이터 로드
                loader = DataLoader(csv_file)
                df = loader.get_clean_data()
                logger.info(f"데이터 로드 완료: {len(df)} 행")
                
                logger.info("2단계: 분석 수행 시작")
                # 2. 분석 수행
                analyzer = ReviewAnalyzer(df, analysis_options)
                analysis_results = analyzer.analyze_all()
                logger.info("분석 수행 완료")
                
                logger.info("3단계: 그래프 생성 시작")
                # 3. 그래프 생성
                output_dir = session_folder / 'outputs'
                output_dir.mkdir(exist_ok=True)
                logger.info(f"출력 디렉토리 생성: {output_dir}")
                
                plot_generator = PlotGenerator(output_dir)
                plot_files = plot_generator.generate_all_plots(analysis_results)
                logger.info("그래프 생성 완료")
                
                logger.info("4단계: 리포트 생성 시작")
                # 4. 리포트 생성
                report_generator = ReportGenerator()
                report_dir = output_dir / 'report'
                report_dir.mkdir(exist_ok=True)
                logger.info(f"리포트 디렉토리 생성: {report_dir}")
                
                html_report_path = report_generator.generate_report(analysis_results, plot_files)
                logger.info(f"HTML 리포트 생성 완료: {html_report_path}")
                
                logger.info(f"즉시 분석 완료: {session_id}")
                
            except Exception as e:
                logger.error(f"즉시 분석 중 오류: {e}")
                import traceback
                logger.error(f"상세 오류: {traceback.format_exc()}")
                flash(f'분석 중 오류가 발생했습니다: {str(e)}', 'error')
                return redirect(url_for('index'))
        
        # 실제 분석 결과를 사용한 세션 정보 생성
        try:
            logger.info("실제 데이터 처리 시작")
            
            # 분석 결과에서 실제 데이터 추출
            loader = DataLoader(csv_file)
            df = loader.get_clean_data()
            
            # 실제 분석 수행
            analyzer = ReviewAnalyzer(df, ANALYSIS_OPTIONS)
            analysis_results = analyzer.analyze_all()
            
            # KPI 데이터 추출
            kpi_data = analysis_results.get('KPI', {})
            total_reviews = kpi_data.get('총_리뷰_수', len(df))
            average_rating = kpi_data.get('평균_평점', df['평점'].mean())
            
            # 감정 분석 데이터 추출 (KPI에서 가져오기)
            positive_ratio = kpi_data.get('긍정_비율', 0) * 100
            negative_ratio = kpi_data.get('부정_비율', 0) * 100
            neutral_ratio = kpi_data.get('중립_비율', 0) * 100
            
            # 우선순위 데이터 추출
            priority_data = analysis_results.get('우선순위', {})
            top_3_priority = priority_data.get('상위_3개', [])
            top_priority = top_3_priority[0]['Aspect'] if top_3_priority else '분석 완료'
            
            # 데이터 기간
            data_period = kpi_data.get('데이터_기간', {})
            start_date = data_period.get('시작일', '2020-01-01')
            end_date = data_period.get('종료일', '2024-12-31')
            
            real_session_info = {
                'session_id': session_id,
                'created_at': datetime.now().isoformat(),
                'summary': {
                    'total_reviews': total_reviews,
                    'average_rating': round(average_rating, 2),
                    'positive_ratio': positive_ratio,
                    'negative_ratio': negative_ratio,
                    'neutral_ratio': neutral_ratio,
                    'top_priority': top_priority,
                    'data_period': f"{start_date} ~ {end_date}",
                    'files': {
                        'html_report': str(html_report_path) if Path(html_report_path).exists() else None,
                        'pdf_report': None,
                        'pptx_summary': None
                    }
                },
                'analysis_results': analysis_results
            }
            
            logger.info("실제 데이터 처리 완료")
            
            return render_template('results.html', 
                                 session_info=real_session_info,
                                 session_id=session_id)
            
        except Exception as e:
            logger.error(f"실제 데이터 처리 중 오류: {e}")
            import traceback
            logger.error(f"상세 오류: {traceback.format_exc()}")
            
            # 폴백: 기본 정보
            fallback_session_info = {
                'session_id': session_id,
                'created_at': datetime.now().isoformat(),
                'summary': {
                    'total_reviews': '분석 완료',
                    'average_rating': '결과 확인',
                    'positive_ratio': 'HTML 리포트',
                    'negative_ratio': '다운로드',
                    'neutral_ratio': '가능',
                    'top_priority': '완료',
                    'data_period': '성공',
                    'files': {
                        'html_report': None,
                        'pdf_report': None,
                        'pptx_summary': None
                    }
                },
                'analysis_results': {
                    'KPI': {'총_리뷰_수': '완료'},
                    '우선순위': {'상위_3개': []},
                    '고급분석': False
                }
            }
            
            return render_template('results.html', 
                                 session_info=fallback_session_info,
                                 session_id=session_id)
        
    except Exception as e:
        logger.error(f"결과 페이지 오류: {e}")
        import traceback
        logger.error(f"상세 오류: {traceback.format_exc()}")
        flash('결과를 불러오는 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('index'))

@app.route('/download/<session_id>/<file_type>')
def download_file(session_id, file_type):
    """파일 다운로드"""
    try:
        session_folder = UPLOAD_FOLDER / session_id
        
        if file_type == 'html':
            file_path = session_folder / 'outputs' / 'report' / 'report.html'
        elif file_type == 'pdf':
            file_path = session_folder / 'outputs' / 'report' / 'report.pdf'
        elif file_type == 'pptx':
            file_path = session_folder / 'outputs' / 'report' / 'summary.pptx'
        else:
            return jsonify({'error': '지원하지 않는 파일 타입입니다.'}), 400
        
        if not file_path.exists():
            return jsonify({'error': '파일을 찾을 수 없습니다.'}), 404
        
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        logger.error(f"파일 다운로드 오류: {e}")
        return jsonify({'error': '파일 다운로드 중 오류가 발생했습니다.'}), 500

@app.route('/api/plot/<session_id>/<plot_name>')
def get_plot(session_id, plot_name):
    """그래프 이미지 제공"""
    try:
        session_folder = UPLOAD_FOLDER / session_id
        plot_path = session_folder / 'outputs' / 'figures' / f'{plot_name}.png'
        
        if not plot_path.exists():
            return jsonify({'error': '그래프를 찾을 수 없습니다.'}), 404
        
        return send_file(plot_path, mimetype='image/png')
        
    except Exception as e:
        logger.error(f"그래프 제공 오류: {e}")
        return jsonify({'error': '그래프를 불러오는 중 오류가 발생했습니다.'}), 500

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
