#!/usr/bin/env python3
"""
오색그린야드호텔 리뷰 분석 메인 실행 파일
전체 분석 파이프라인을 실행합니다.
"""
import sys
import logging
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import ensure_directories
from src.load import load_and_preprocess_data
from src.analysis import ReviewAnalyzer
from src.plots import PlotGenerator
from src.report import ReportGenerator
from src.export import ExportGenerator

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def main():
    """메인 실행 함수"""
    try:
        logger.info("=" * 60)
        logger.info("오색그린야드호텔 리뷰 분석 시작")
        logger.info("=" * 60)
        
        # 1. 디렉터리 생성
        logger.info("1. 디렉터리 생성 중...")
        ensure_directories()
        logger.info("✓ 디렉터리 생성 완료")
        
        # 2. 데이터 로드 및 전처리
        logger.info("2. 데이터 로드 및 전처리 중...")
        df, data_info = load_and_preprocess_data()
        logger.info(f"✓ 데이터 로드 완료: {len(df)} 행, {len(df.columns)} 컬럼")
        logger.info(f"  - 데이터 기간: {data_info['데이터_기간']['시작일']} ~ {data_info['데이터_기간']['종료일']}")
        logger.info(f"  - 평균 평점: {data_info['평균_평점']:.2f}점")
        
        # 3. 분석 수행
        logger.info("3. 리뷰 분석 수행 중...")
        analyzer = ReviewAnalyzer(df)
        analysis_results = analyzer.get_analysis_summary()
        logger.info("✓ 분석 완료")
        
        # 분석 결과 요약 출력
        kpi = analysis_results['KPI']
        logger.info(f"  - 총 리뷰 수: {kpi['총_리뷰_수']:,}개")
        logger.info(f"  - 긍정 비율: {kpi['긍정_비율']:.1f}%")
        logger.info(f"  - 부정 비율: {kpi['부정_비율']:.1f}%")
        logger.info(f"  - 중립 비율: {kpi['중립_비율']:.1f}%")
        
        # 4. 그래프 생성
        logger.info("4. 그래프 생성 중...")
        plot_generator = PlotGenerator()
        plot_files = plot_generator.generate_all_plots(analysis_results)
        logger.info(f"✓ 그래프 생성 완료: {len(plot_files)}개")
        
        # 생성된 그래프 파일 목록 출력
        for plot_name, plot_path in plot_files.items():
            if plot_path:  # 빈 문자열이 아닌 경우만
                logger.info(f"  - {plot_name}: {Path(plot_path).name}")
        
        # 5. HTML 리포트 생성
        logger.info("5. HTML 리포트 생성 중...")
        report_generator = ReportGenerator()
        
        # 상세 리포트 생성
        report_file = report_generator.generate_report(analysis_results, plot_files)
        logger.info(f"✓ 상세 리포트 생성 완료: {Path(report_file).name}")
        
        # 요약 리포트 생성
        summary_file = report_generator.create_summary_report(analysis_results)
        logger.info(f"✓ 요약 리포트 생성 완료: {Path(summary_file).name}")
        
        # 6. PDF 및 PPTX 리포트 생성
        logger.info("6. PDF 및 PPTX 리포트 생성 중...")
        export_generator = ExportGenerator(report_file)
        export_results = export_generator.generate_all_formats(analysis_results, plot_files)
        
        if export_results['pdf']:
            logger.info(f"✓ PDF 리포트 생성 완료: {Path(export_results['pdf']).name}")
        else:
            logger.warning("⚠ PDF 생성 실패 (weasyprint 라이브러리 필요)")
            
        if export_results['pptx']:
            logger.info(f"✓ PPTX 요약 슬라이드 생성 완료: {Path(export_results['pptx']).name}")
        else:
            logger.warning("⚠ PPTX 생성 실패 (python-pptx 라이브러리 필요)")
        
        # 7. 최종 결과 출력
        logger.info("=" * 60)
        logger.info("분석 완료!")
        logger.info("=" * 60)
        
        # 주요 결과 요약
        logger.info("📊 주요 결과:")
        logger.info(f"  • 총 리뷰 수: {kpi['총_리뷰_수']:,}개")
        logger.info(f"  • 평균 평점: {kpi['평균_평점']:.2f}점")
        logger.info(f"  • 긍정 비율: {kpi['긍정_비율']:.1f}%")
        logger.info(f"  • 부정 비율: {kpi['부정_비율']:.1f}%")
        
        # 상위 개선사항 출력
        if '우선순위' in analysis_results and len(analysis_results['우선순위']) > 0:
            top_priority = analysis_results['우선순위'].iloc[0]
            logger.info(f"  • 최우선 개선사항: {top_priority['Aspect']} (부정 비율: {top_priority['부정_비율']:.1f}%)")
        
        logger.info("")
        logger.info("📁 생성된 파일:")
        logger.info(f"  • 상세 리포트: {report_file}")
        logger.info(f"  • 요약 리포트: {summary_file}")
        logger.info(f"  • 그래프 파일: {len(plot_files)}개 (outputs/figures/ 폴더)")
        
        # PDF/PPTX 파일 정보 추가
        if export_results['pdf']:
            logger.info(f"  • PDF 리포트: {export_results['pdf']}")
        if export_results['pptx']:
            logger.info(f"  • PPTX 요약: {export_results['pptx']}")
        logger.info("")
        logger.info("🎯 다음 단계:")
        logger.info("  1. 생성된 HTML 리포트를 웹 브라우저에서 확인하세요")
        logger.info("  2. 그래프 파일들을 확인하여 시각적 분석을 검토하세요")
        logger.info("  3. 우선순위 점수가 높은 개선사항부터 대응하세요")
        
        logger.info("=" * 60)
        logger.info("분석이 성공적으로 완료되었습니다! 🎉")
        logger.info("=" * 60)
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"파일을 찾을 수 없습니다: {e}")
        logger.error("데이터 파일 경로를 확인해주세요.")
        return 1
        
    except Exception as e:
        logger.error(f"분석 중 오류가 발생했습니다: {e}")
        logger.error("오류 상세 정보:", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
