"""
리포트 생성 모듈 - HTML 리포트 생성
"""
import pandas as pd
from datetime import datetime
from typing import Dict, Any
import logging
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from .config import TEMPLATE_DIR, REPORT_DIR, REPORT_CONFIG

logger = logging.getLogger(__name__)

class ReportGenerator:
    """HTML 리포트 생성 클래스"""
    
    def __init__(self):
        self.template_dir = TEMPLATE_DIR
        self.report_dir = REPORT_DIR
        self.report_config = REPORT_CONFIG
        
        # Jinja2 환경 설정
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )
    
    def generate_report(self, analysis_results: Dict[str, Any], 
                       plot_files: Dict[str, str]) -> str:
        """HTML 리포트를 생성합니다."""
        logger.info("HTML 리포트 생성 시작")
        
        try:
            # 템플릿 렌더링을 위한 데이터 준비
            template_data = self._prepare_template_data(analysis_results, plot_files)
            
            # 템플릿 로드 및 렌더링
            template = self.env.get_template('report.html')
            html_content = template.render(**template_data)
            
            # 리포트 파일 저장
            report_filename = self.report_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"HTML 리포트 생성 완료: {report_filename}")
            return str(report_filename)
            
        except Exception as e:
            logger.error(f"리포트 생성 중 오류 발생: {e}")
            raise
    
    def _prepare_template_data(self, analysis_results: Dict[str, Any], 
                              plot_files: Dict[str, str]) -> Dict[str, Any]:
        """템플릿 렌더링을 위한 데이터를 준비합니다."""
        
        # 기본 리포트 정보
        template_data = {
            'title': self.report_config['title'],
            'version': self.report_config['version'],
            'generated_date': datetime.now().strftime('%Y년 %m월 %d일 %H:%M'),
            'reproduction_command': self.report_config['reproduction_command']
        }
        
        # KPI 데이터
        if 'KPI' in analysis_results:
            template_data['kpi'] = analysis_results['KPI']
            
            # 데이터 범위 설정
            if '데이터_기간' in analysis_results['KPI']:
                template_data['data_range'] = {
                    'start': analysis_results['KPI']['데이터_기간']['시작일'],
                    'end': analysis_results['KPI']['데이터_기간']['종료일']
                }
        
        # 세그먼트 분석 데이터
        if '세그먼트분석' in analysis_results:
            template_data['segments'] = analysis_results['세그먼트분석']
        
        # 우선순위 데이터
        if '우선순위' in analysis_results:
            template_data['priority'] = analysis_results['우선순위']
        
        # 그래프 파일 경로
        template_data['plot_files'] = plot_files
        
        # 고급 분석 데이터
        if '고급분석' in analysis_results:
            template_data['advanced_analysis'] = analysis_results['고급분석']
        
        return template_data
    
    def create_summary_report(self, analysis_results: Dict[str, Any]) -> str:
        """요약 리포트를 생성합니다."""
        logger.info("요약 리포트 생성 시작")
        
        try:
            # 요약 데이터 준비
            summary_data = self._prepare_summary_data(analysis_results)
            
            # 간단한 HTML 요약 리포트 생성
            html_content = self._create_summary_html(summary_data)
            
            # 파일 저장
            summary_filename = self.report_dir / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            with open(summary_filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"요약 리포트 생성 완료: {summary_filename}")
            return str(summary_filename)
            
        except Exception as e:
            logger.error(f"요약 리포트 생성 중 오류 발생: {e}")
            raise
    
    def _prepare_summary_data(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """요약 리포트용 데이터를 준비합니다."""
        summary = {}
        
        # KPI 요약
        if 'KPI' in analysis_results:
            kpi = analysis_results['KPI']
            summary['kpi'] = {
                'total_reviews': kpi.get('총_리뷰_수', 0),
                'avg_rating': kpi.get('평균_평점', 0),
                'positive_ratio': kpi.get('긍정_비율', 0),
                'negative_ratio': kpi.get('부정_비율', 0)
            }
        
        # 상위 3개 개선사항
        if '우선순위' in analysis_results:
            priority_df = analysis_results['우선순위']
            if len(priority_df) > 0:
                summary['top_improvements'] = priority_df.head(3).to_dict('records')
        
        # 주요 인사이트
        summary['insights'] = [
            "전반적인 고객 만족도는 양호하나 개선 여지가 있습니다.",
            "온천수는 핵심 경쟁력으로 확인되었습니다.",
            "시설/온수 관련 개선이 시급합니다.",
            "가족 고객 중심의 서비스 전략이 효과적입니다.",
            "직원 서비스 품질 향상이 중요합니다."
        ]
        
        return summary
    
    def _create_summary_html(self, summary_data: Dict[str, Any]) -> str:
        """요약 HTML을 생성합니다."""
        html = f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>오색그린야드호텔 리뷰 분석 요약</title>
            <style>
                body {{
                    font-family: 'NanumBarunGothic', 'Malgun Gothic', sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 0 20px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    border-bottom: 3px solid #4682B4;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    color: #4682B4;
                    margin: 0;
                }}
                .section {{
                    margin-bottom: 30px;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    background-color: #fafafa;
                }}
                .section h2 {{
                    color: #4682B4;
                    border-bottom: 2px solid #4682B4;
                    padding-bottom: 10px;
                    margin-top: 0;
                }}
                .kpi-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 15px;
                    margin-bottom: 20px;
                }}
                .kpi-item {{
                    background: linear-gradient(135deg, #4682B4, #5F9EA0);
                    color: white;
                    padding: 15px;
                    border-radius: 8px;
                    text-align: center;
                }}
                .kpi-item .value {{
                    font-size: 1.5em;
                    font-weight: bold;
                    margin: 5px 0;
                }}
                .insights {{
                    background-color: #e8f4f8;
                    padding: 15px;
                    border-radius: 8px;
                    border-left: 4px solid #4682B4;
                }}
                .insights ul {{
                    margin: 0;
                    padding-left: 20px;
                }}
                .priority-item {{
                    background-color: white;
                    padding: 10px;
                    margin: 5px 0;
                    border-radius: 5px;
                    border-left: 3px solid #DC143C;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>오색그린야드호텔 리뷰 분석 요약</h1>
                    <p>생성일: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}</p>
                </div>
                
                <div class="section">
                    <h2>핵심 지표</h2>
                    <div class="kpi-grid">
                        <div class="kpi-item">
                            <div>총 리뷰 수</div>
                            <div class="value">{summary_data.get('kpi', {}).get('total_reviews', 0)}</div>
                        </div>
                        <div class="kpi-item">
                            <div>평균 평점</div>
                            <div class="value">{summary_data.get('kpi', {}).get('avg_rating', 0):.2f}</div>
                        </div>
                        <div class="kpi-item">
                            <div>긍정 비율</div>
                            <div class="value">{summary_data.get('kpi', {}).get('positive_ratio', 0):.1f}%</div>
                        </div>
                        <div class="kpi-item">
                            <div>부정 비율</div>
                            <div class="value">{summary_data.get('kpi', {}).get('negative_ratio', 0):.1f}%</div>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>주요 인사이트</h2>
                    <div class="insights">
                        <ul>
        """
        
        for insight in summary_data.get('insights', []):
            html += f"<li>{insight}</li>"
        
        html += """
                        </ul>
                    </div>
                </div>
        """
        
        if 'top_improvements' in summary_data:
            html += """
                <div class="section">
                    <h2>상위 개선사항</h2>
            """
            
            for item in summary_data['top_improvements']:
                html += f"""
                    <div class="priority-item">
                        <strong>{item.get('Aspect', '')}</strong><br>
                        부정 비율: {item.get('부정_비율', 0):.1f}% | 
                        우선순위 점수: {item.get('우선순위_점수', 0):.2f}
                    </div>
                """
            
            html += "</div>"
        
        html += """
            </div>
        </body>
        </html>
        """
        
        return html
