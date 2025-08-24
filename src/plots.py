"""
시각화 모듈 - 그래프 생성 및 저장
"""
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
import logging
from pathlib import Path

from .config import FIGURES_DIR, PLOT_CONFIG, get_font_properties, FONT_PATH

logger = logging.getLogger(__name__)

class PlotGenerator:
    """그래프 생성 클래스"""
    
    def __init__(self, output_dir: Path = None):
        self.figures_dir = output_dir or FIGURES_DIR
        self.plot_config = PLOT_CONFIG
        self.colors = PLOT_CONFIG['colors']
        
        # 폰트 설정
        self._setup_fonts()
        
        # matplotlib 스타일 설정
        plt.style.use(self.plot_config['style'])
        
        # 폰트 크기 설정 (2배 증가)
        plt.rcParams['font.size'] = 16  # 기본 폰트 크기
        plt.rcParams['axes.titlesize'] = 20  # 제목 폰트 크기
        plt.rcParams['axes.labelsize'] = 18  # 축 라벨 폰트 크기
        plt.rcParams['xtick.labelsize'] = 16  # x축 눈금 라벨 폰트 크기
        plt.rcParams['ytick.labelsize'] = 16  # y축 눈금 라벨 폰트 크기
        plt.rcParams['legend.fontsize'] = 16  # 범례 폰트 크기
        plt.rcParams['figure.titlesize'] = 24  # 그림 제목 폰트 크기
        
    def _setup_fonts(self) -> None:
        """한글 폰트를 설정합니다."""
        # 폰트 파일이 있으면 직접 등록
        if FONT_PATH.exists():
            try:
                # 폰트 매니저에 직접 등록
                fm.fontManager.addfont(str(FONT_PATH))
                
                # 등록된 폰트 확인
                font_prop = fm.FontProperties(fname=str(FONT_PATH))
                font_name = font_prop.get_name()
                
                # matplotlib 설정에 적용
                plt.rcParams['font.family'] = font_name
                plt.rcParams['font.sans-serif'] = [font_name] + plt.rcParams['font.sans-serif']
                plt.rcParams['axes.unicode_minus'] = False
                
                # 전역 폰트 속성 저장
                self.font_prop = font_prop
                
                logger.info(f"한글 폰트 설정 완료: {font_name}")
                
            except Exception as e:
                logger.warning(f"폰트 설정 실패: {e}")
                self._setup_system_fonts()
        else:
            logger.warning("한글 폰트 파일을 찾을 수 없습니다. 시스템 폰트를 사용합니다.")
            self._setup_system_fonts()
    
    def _setup_system_fonts(self) -> None:
        """시스템 한글 폰트를 설정합니다."""
        # matplotlib 폰트 설정 초기화
        plt.rcdefaults()
        
        # Windows 환경에서 사용 가능한 한글 폰트들
        korean_fonts = [
            "Malgun Gothic",  # 맑은 고딕
            "NanumGothic",    # 나눔고딕
            "NanumBarunGothic", # 나눔바른고딕
            "Dotum",          # 돋움
            "Gulim",          # 굴림
            "Batang",         # 바탕
            "Gungsuh",        # 궁서
            "Arial Unicode MS", # Arial Unicode
            "DejaVu Sans"     # 기본 폰트
        ]
        
        # 시스템에 설치된 폰트 확인
        available_fonts = [f.name for f in fm.fontManager.ttflist]
        selected_font = None
        
        for font in korean_fonts:
            if font in available_fonts:
                selected_font = font
                break
        
        if selected_font:
            # matplotlib 폰트 설정
            plt.rcParams['font.family'] = selected_font
            plt.rcParams['font.sans-serif'] = [selected_font] + plt.rcParams['font.sans-serif']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 폰트 매니저에 직접 등록
            try:
                font_files = [f.fname for f in fm.fontManager.ttflist if f.name == selected_font]
                if font_files:
                    # 폰트 매니저에 폰트 추가
                    font_prop = fm.FontProperties(fname=font_files[0])
                    plt.rcParams['font.family'] = font_prop.get_name()
                    self.font_prop = font_prop
                    logger.info(f"시스템 한글 폰트 설정 완료: {selected_font}")
                else:
                    logger.warning(f"폰트 파일을 찾을 수 없습니다: {selected_font}")
            except Exception as e:
                logger.warning(f"폰트 등록 실패: {e}")
        else:
            # 기본 설정 사용
            plt.rcParams['font.family'] = 'sans-serif'
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            self.font_prop = None
            logger.warning("사용 가능한 한글 폰트를 찾을 수 없습니다. 기본 폰트를 사용합니다.")
    
    def create_yearly_trend_plot(self, yearly_data: pd.DataFrame) -> str:
        """연도별 트렌드 그래프를 생성합니다."""
        logger.info("연도별 트렌드 그래프 생성 시작")
        
        fig, ax1 = plt.subplots(figsize=self.plot_config['figure_size'])
        
        # 막대 그래프 (리뷰 수)
        bars = ax1.bar(yearly_data.index, yearly_data['리뷰_수'], 
                      color=self.colors['primary'], alpha=0.7, label='리뷰 수')
        ax1.set_xlabel('연도', fontproperties=self.font_prop)
        ax1.set_ylabel('리뷰 수', color=self.colors['primary'], fontproperties=self.font_prop)
        ax1.tick_params(axis='y', labelcolor=self.colors['primary'])
        
        # 라인 그래프 (평균 평점) - twin axis
        ax2 = ax1.twinx()
        line = ax2.plot(yearly_data.index, yearly_data['평균_평점'], 
                       color=self.colors['negative'], marker='o', linewidth=2, 
                       label='평균 평점')
        ax2.set_ylabel('평균 평점', color=self.colors['negative'], fontproperties=self.font_prop)
        ax2.tick_params(axis='y', labelcolor=self.colors['negative'])
        ax2.set_ylim(0, 10)
        
        # 제목 및 범례
        plt.title('연도별 리뷰 수 및 평균 평점 트렌드', fontsize=18, pad=20, fontproperties=self.font_prop)
        
        # 범례 통합
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', prop=self.font_prop)
        
        plt.tight_layout()
        
        # 저장
        filename = self.figures_dir / 'yearly_trend.png'
        plt.savefig(filename, dpi=self.plot_config['dpi'], bbox_inches='tight')
        plt.close()
        
        logger.info(f"연도별 트렌드 그래프 저장 완료: {filename}")
        return str(filename)
    
    def create_sentiment_pie_chart(self, sentiment_data: Dict[str, int]) -> str:
        """감정 분포 파이 차트를 생성합니다."""
        logger.info("감정 분포 파이 차트 생성 시작")
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # 데이터 준비 - 한글 라벨 사용
        labels = list(sentiment_data.keys())
        sizes = list(sentiment_data.values())
        colors_list = [self.colors['positive'], self.colors['negative'], self.colors['neutral']]
        
        # 파이 차트 생성 (크기를 90%로 줄임)
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors_list, 
                                         autopct='%1.1f%%', startangle=90, textprops={'fontproperties': self.font_prop},
                                         radius=0.9)
        
        # 텍스트 스타일 설정
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        plt.title('감정 분포', fontsize=18, pad=20, fontproperties=self.font_prop)
        plt.axis('equal')
        
        # 저장
        filename = self.figures_dir / 'sentiment_distribution.png'
        plt.savefig(filename, dpi=self.plot_config['dpi'], bbox_inches='tight')
        plt.close()
        
        logger.info(f"감정 분포 파이 차트 저장 완료: {filename}")
        return str(filename)
    
    def create_negative_keywords_bar(self, keywords: List[Tuple[str, int]]) -> str:
        """부정 키워드 상위 N개 막대 그래프를 생성합니다."""
        logger.info("부정 키워드 막대 그래프 생성 시작")
        
        if not keywords:
            logger.warning("부정 키워드가 없습니다.")
            return ""
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # 데이터 준비
        words, counts = zip(*keywords)
        
        # 가로 막대 그래프
        bars = ax.barh(range(len(words)), counts, color=self.colors['negative'], alpha=0.7)
        
        # 축 설정
        ax.set_yticks(range(len(words)))
        ax.set_yticklabels(words, fontsize=12, fontproperties=self.font_prop)
        ax.set_xlabel('언급 횟수', fontsize=14, fontproperties=self.font_prop)
        ax.set_title('부정 키워드 상위 10개', fontsize=18, pad=20, fontproperties=self.font_prop)
        
        # 값 표시
        for i, (bar, count) in enumerate(zip(bars, counts)):
            ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                   str(count), ha='left', va='center')
        
        plt.tight_layout()
        
        # 저장
        filename = self.figures_dir / 'negative_keywords.png'
        plt.savefig(filename, dpi=self.plot_config['dpi'], bbox_inches='tight')
        plt.close()
        
        logger.info(f"부정 키워드 막대 그래프 저장 완료: {filename}")
        return str(filename)
    
    def create_aspect_sentiment_stacked_bar(self, aspect_data: pd.DataFrame) -> str:
        """Aspect별 감정 스택 막대 그래프를 생성합니다."""
        logger.info("Aspect별 감정 스택 막대 그래프 생성 시작")
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # 데이터 준비
        aspects = aspect_data['Aspect'].tolist()
        positive_ratios = aspect_data['긍정_비율'].tolist()
        negative_ratios = aspect_data['부정_비율'].tolist()
        neutral_ratios = aspect_data['중립_비율'].tolist()
        
        # 스택 막대 그래프
        x = range(len(aspects))
        bars1 = ax.bar(x, positive_ratios, label='긍정', color=self.colors['positive'], alpha=0.8)
        bars2 = ax.bar(x, negative_ratios, bottom=positive_ratios, label='부정', 
                      color=self.colors['negative'], alpha=0.8)
        bars3 = ax.bar(x, neutral_ratios, 
                      bottom=[p + n for p, n in zip(positive_ratios, negative_ratios)], 
                      label='중립', color=self.colors['neutral'], alpha=0.8)
        
        # 축 설정
        ax.set_xlabel('Aspect', fontsize=14, fontproperties=self.font_prop)
        ax.set_ylabel('비율 (%)', fontsize=14, fontproperties=self.font_prop)
        ax.set_title('Aspect별 감정 분포', fontsize=18, pad=20, fontproperties=self.font_prop)
        ax.set_xticks(x)
        ax.set_xticklabels(aspects, rotation=45, ha='right', fontsize=12, fontproperties=self.font_prop)
        ax.set_ylim(0, 100)
        ax.legend(prop=self.font_prop)
        
        # 값 표시
        for i, (p, n, neu) in enumerate(zip(positive_ratios, negative_ratios, neutral_ratios)):
            if p > 5:  # 5% 이상일 때만 표시
                ax.text(i, p/2, f'{p:.1f}%', ha='center', va='center', fontweight='bold')
            if n > 5:
                ax.text(i, p + n/2, f'{n:.1f}%', ha='center', va='center', fontweight='bold')
            if neu > 5:
                ax.text(i, p + n + neu/2, f'{neu:.1f}%', ha='center', va='center', fontweight='bold')
        
        plt.tight_layout()
        
        # 저장
        filename = self.figures_dir / 'aspect_sentiment.png'
        plt.savefig(filename, dpi=self.plot_config['dpi'], bbox_inches='tight')
        plt.close()
        
        logger.info(f"Aspect별 감정 스택 막대 그래프 저장 완료: {filename}")
        return str(filename)
    
    def create_priority_scores_bar(self, priority_data: Dict[str, Any]) -> str:
        """우선순위 점수 막대 그래프를 생성합니다."""
        logger.info("우선순위 점수 막대 그래프 생성 시작")
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # 데이터 준비 - 우선순위 데이터 구조에 맞게 수정
        if '상위_3개' in priority_data and priority_data['상위_3개']:
            priority_list = priority_data['상위_3개']
            aspects = [item['Aspect'] for item in priority_list]
            scores = [item['우선순위_점수'] for item in priority_list]
        else:
            # 빈 데이터 처리
            aspects = []
            scores = []
        
        # 빈 데이터 처리
        if not aspects:
            ax.text(0.5, 0.5, '우선순위 데이터가 없습니다', 
                   ha='center', va='center', transform=ax.transAxes,
                   fontsize=14, fontproperties=self.font_prop)
            ax.set_title('개선사항 우선순위 점수', fontsize=18, pad=20, fontproperties=self.font_prop)
        else:
            # 막대 그래프
            bars = ax.bar(range(len(aspects)), scores, color=self.colors['secondary'], alpha=0.7)
            
            # 축 설정
            ax.set_xlabel('Aspect', fontsize=14, fontproperties=self.font_prop)
            ax.set_ylabel('우선순위 점수', fontsize=14, fontproperties=self.font_prop)
            ax.set_title('개선사항 우선순위 점수', fontsize=18, pad=20, fontproperties=self.font_prop)
            ax.set_xticks(range(len(aspects)))
            ax.set_xticklabels(aspects, rotation=45, ha='right', fontsize=12, fontproperties=self.font_prop)
            
            # 값 표시
            for i, (bar, score) in enumerate(zip(bars, scores)):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                       f'{score:.1f}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        
        # 저장
        filename = self.figures_dir / 'priority_scores.png'
        plt.savefig(filename, dpi=self.plot_config['dpi'], bbox_inches='tight')
        plt.close()
        
        logger.info(f"우선순위 점수 막대 그래프 저장 완료: {filename}")
        return str(filename)
    
    def create_quarterly_trend_plot(self, quarterly_data: pd.DataFrame) -> str:
        """분기별 트렌드 그래프를 생성합니다."""
        logger.info("분기별 트렌드 그래프 생성 시작")
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # 분기별 리뷰 수
        quarterly_pivot = quarterly_data.pivot(index='연도', columns='분기', values='리뷰_수')
        quarterly_pivot.plot(kind='bar', ax=ax1, color=[self.colors['primary'], 
                                                       self.colors['secondary'], 
                                                       self.colors['positive'], 
                                                       self.colors['negative']])
        ax1.set_title('분기별 리뷰 수', fontsize=18, fontproperties=self.font_prop)
        ax1.set_ylabel('리뷰 수', fontsize=18, fontproperties=self.font_prop)
        ax1.set_xlabel('연도', fontsize=18, fontproperties=self.font_prop)
        ax1.tick_params(axis='both', labelsize=16)
        ax1.legend(title='분기', prop=self.font_prop, fontsize=16)
        
        # 분기별 평균 평점
        quarterly_rating_pivot = quarterly_data.pivot(index='연도', columns='분기', values='평균_평점')
        quarterly_rating_pivot.plot(kind='line', ax=ax2, marker='o', linewidth=2)
        ax2.set_title('분기별 평균 평점', fontsize=18, fontproperties=self.font_prop)
        ax2.set_ylabel('평균 평점', fontsize=18, fontproperties=self.font_prop)
        ax2.set_xlabel('연도', fontsize=18, fontproperties=self.font_prop)
        ax2.set_ylim(0, 10)
        ax2.tick_params(axis='both', labelsize=16)
        ax2.legend(title='분기', prop=self.font_prop, fontsize=16)
        
        plt.tight_layout()
        
        # 저장
        filename = self.figures_dir / 'quarterly_trend.png'
        plt.savefig(filename, dpi=self.plot_config['dpi'], bbox_inches='tight')
        plt.close()
        
        logger.info(f"분기별 트렌드 그래프 저장 완료: {filename}")
        return str(filename)
    
    def create_segment_analysis_plot(self, segment_data: Dict[str, Any]) -> str:
        """세그먼트 분석 그래프를 생성합니다."""
        logger.info("세그먼트 분석 그래프 생성 시작")
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # 세그먼트별 리뷰 수
        segments = list(segment_data.keys())
        review_counts = [segment_data[seg]['매칭_리뷰_수'] for seg in segments]
        
        bars1 = ax1.bar(segments, review_counts, color=self.colors['primary'], alpha=0.7)
        ax1.set_title('세그먼트별 리뷰 수', fontsize=18, fontproperties=self.font_prop)
        ax1.set_ylabel('리뷰 수', fontproperties=self.font_prop)
        ax1.set_xticks(range(len(segments)))
        ax1.set_xticklabels(segments, fontproperties=self.font_prop)
        
        # 값 표시
        for bar, count in zip(bars1, review_counts):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(count), ha='center', va='bottom', fontweight='bold')
        
        # 세그먼트별 평균 평점
        avg_ratings = [segment_data[seg]['평균_평점'] for seg in segments]
        
        bars2 = ax2.bar(segments, avg_ratings, color=self.colors['positive'], alpha=0.7)
        ax2.set_title('세그먼트별 평균 평점', fontsize=18, fontproperties=self.font_prop)
        ax2.set_ylabel('평균 평점', fontproperties=self.font_prop)
        ax2.set_ylim(0, 10)
        ax2.set_xticks(range(len(segments)))
        ax2.set_xticklabels(segments, fontproperties=self.font_prop)
        
        # 값 표시
        for bar, rating in zip(bars2, avg_ratings):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    f'{rating:.1f}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        
        # 저장
        filename = self.figures_dir / 'segment_analysis.png'
        plt.savefig(filename, dpi=self.plot_config['dpi'], bbox_inches='tight')
        plt.close()
        
        logger.info(f"세그먼트 분석 그래프 저장 완료: {filename}")
        return str(filename)
    
    def create_shap_feature_importance_plot(self, shap_analysis: Dict[str, Any]) -> str:
        """SHAP 특성 중요도 그래프를 생성합니다."""
        logger.info("SHAP 특성 중요도 그래프 생성 시작")
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # 상위 특성 추출
        top_features = shap_analysis['top_features']
        feature_names = [name for name, _ in top_features]
        importance_values = [value for _, value in top_features]
        
        # 가로 막대 그래프
        bars = ax.barh(range(len(feature_names)), importance_values, 
                      color=self.colors['primary'], alpha=0.7)
        
        # 축 설정
        ax.set_yticks(range(len(feature_names)))
        ax.set_yticklabels(feature_names, fontproperties=self.font_prop)
        ax.set_xlabel('특성 중요도', fontproperties=self.font_prop)
        ax.set_title('SHAP 특성 중요도 상위 10개', fontsize=16, pad=20, fontproperties=self.font_prop)
        
        # 값 표시
        for i, (bar, value) in enumerate(zip(bars, importance_values)):
            ax.text(bar.get_width() + 0.001, bar.get_y() + bar.get_height()/2, 
                   f'{value:.3f}', ha='left', va='center', fontweight='bold')
        
        plt.tight_layout()
        
        # 저장
        filename = self.figures_dir / 'shap_feature_importance.png'
        plt.savefig(filename, dpi=self.plot_config['dpi'], bbox_inches='tight')
        plt.close()
        
        logger.info(f"SHAP 특성 중요도 그래프 저장 완료: {filename}")
        return str(filename)
    
    def create_topic_distribution_plot(self, topic_modeling: Dict[str, Any]) -> str:
        """토픽 분포 그래프를 생성합니다."""
        logger.info("토픽 분포 그래프 생성 시작")
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
        
        # 1. 토픽별 주요 키워드
        topics = topic_modeling['topics']
        topic_ids = [topic['topic_id'] for topic in topics]
        top_words_list = [', '.join(topic['top_words'][:5]) for topic in topics]
        
        # 토픽별 키워드 표시
        for i, (topic_id, words) in enumerate(zip(topic_ids, top_words_list)):
            ax1.text(0.1, 0.9 - i*0.1, f'토픽 {topic_id}: {words}', 
                    fontsize=12, fontproperties=self.font_prop,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.7))
        
        ax1.set_xlim(0, 1)
        ax1.set_ylim(0, 1)
        ax1.set_title('토픽별 주요 키워드', fontsize=16, pad=20, fontproperties=self.font_prop)
        ax1.axis('off')
        
        # 2. 연도별 토픽 비중 변화
        yearly_dist = topic_modeling['yearly_distribution']
        years = yearly_dist['연도'].values
        topic_columns = [col for col in yearly_dist.columns if col.startswith('토픽_')]
        
        # 스택 영역 그래프
        topic_data = yearly_dist[topic_columns].values.T
        ax2.stackplot(years, topic_data, labels=[f'토픽 {i+1}' for i in range(len(topic_columns))])
        
        ax2.set_xlabel('연도', fontproperties=self.font_prop)
        ax2.set_ylabel('토픽 비중', fontproperties=self.font_prop)
        ax2.set_title('연도별 토픽 비중 변화', fontsize=16, pad=20, fontproperties=self.font_prop)
        ax2.legend(prop=self.font_prop, loc='upper left')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 저장
        filename = self.figures_dir / 'topic_distribution.png'
        plt.savefig(filename, dpi=self.plot_config['dpi'], bbox_inches='tight')
        plt.close()
        
        logger.info(f"토픽 분포 그래프 저장 완료: {filename}")
        return str(filename)
    
    def create_change_point_plot(self, change_point_analysis: Dict[str, Any]) -> str:
        """변화점 탐지 그래프를 생성합니다."""
        logger.info("변화점 탐지 그래프 생성 시작")
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # 연도별 평균 평점
        yearly_ratings = change_point_analysis['yearly_ratings']
        years = yearly_ratings['연도'].values
        ratings = yearly_ratings['평점'].values
        
        # 평균 평점 라인 그래프
        ax.plot(years, ratings, 'o-', linewidth=2, markersize=8, 
               color=self.colors['primary'], label='연도별 평균 평점')
        
        # 변화점 표시
        change_points = change_point_analysis['change_points']
        for cp in change_points:
            year = cp['year']
            rating = cp['rating_after']
            change = cp['change']
            change_type = cp['change_type']
            
            # 변화점 마커
            color = 'red' if change < 0 else 'green'
            ax.scatter(year, rating, s=200, c=color, marker='*', 
                      edgecolors='black', linewidth=2, zorder=5)
            
            # 변화점 주석
            ax.annotate(f'{change_type}\n({change:+.2f})', 
                       xy=(year, rating), xytext=(10, 10),
                       textcoords='offset points', fontsize=10,
                       fontproperties=self.font_prop,
                       bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7),
                       arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"))
        
        ax.set_xlabel('연도', fontproperties=self.font_prop)
        ax.set_ylabel('평균 평점', fontproperties=self.font_prop)
        ax.set_title('연도별 평균 평점 변화점 탐지', fontsize=16, pad=20, fontproperties=self.font_prop)
        ax.grid(True, alpha=0.3)
        ax.legend(prop=self.font_prop)
        
        plt.tight_layout()
        
        # 저장
        filename = self.figures_dir / 'change_point_detection.png'
        plt.savefig(filename, dpi=self.plot_config['dpi'], bbox_inches='tight')
        plt.close()
        
        logger.info(f"변화점 탐지 그래프 저장 완료: {filename}")
        return str(filename)
    
    def create_model_performance_plot(self, rating_prediction: Dict[str, Any]) -> str:
        """모델 성능 비교 그래프를 생성합니다."""
        logger.info("모델 성능 비교 그래프 생성 시작")
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # 모델별 성능 비교
        models = []
        r2_scores = []
        mse_scores = []
        
        for name, result in rating_prediction.items():
            if name != 'SHAP_Analysis':
                models.append(name)
                r2_scores.append(result['r2'])
                mse_scores.append(result['mse'])
        
        # R² 점수 비교
        bars1 = ax1.bar(models, r2_scores, color=self.colors['positive'], alpha=0.7)
        ax1.set_title('모델별 R² 점수 비교', fontsize=14, fontproperties=self.font_prop)
        ax1.set_ylabel('R² 점수', fontproperties=self.font_prop)
        ax1.set_ylim(0, 1)
        
        # 값 표시
        for bar, score in zip(bars1, r2_scores):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                    f'{score:.3f}', ha='center', va='bottom', fontweight='bold')
        
        # MSE 점수 비교
        bars2 = ax2.bar(models, mse_scores, color=self.colors['negative'], alpha=0.7)
        ax2.set_title('모델별 MSE 점수 비교', fontsize=14, fontproperties=self.font_prop)
        ax2.set_ylabel('MSE 점수', fontproperties=self.font_prop)
        
        # 값 표시
        for bar, score in zip(bars2, mse_scores):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                    f'{score:.3f}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        
        # 저장
        filename = self.figures_dir / 'model_performance.png'
        plt.savefig(filename, dpi=self.plot_config['dpi'], bbox_inches='tight')
        plt.close()
        
        logger.info(f"모델 성능 비교 그래프 저장 완료: {filename}")
        return str(filename)
    
    def generate_all_plots(self, analysis_results: Dict[str, Any]) -> Dict[str, Path]:
        """모든 그래프를 생성하고 파일 경로를 반환합니다."""
        logger.info("모든 그래프 생성 시작")
        
        # figures 디렉토리 생성
        figures_dir = self.figures_dir / 'figures'
        figures_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"그래프 저장 디렉토리: {figures_dir}")
        
        # 임시로 figures_dir을 self.figures_dir로 설정
        original_figures_dir = self.figures_dir
        self.figures_dir = figures_dir
        
        plot_files = {}
        
        try:
            # 기본 분석 그래프
            # 1. 연도별 트렌드
            if '트렌드' in analysis_results and '연도별' in analysis_results['트렌드']:
                plot_files['yearly_trend'] = self.create_yearly_trend_plot(
                    analysis_results['트렌드']['연도별']
                )
            
            # 2. 감정 분포 파이 차트
            if '감정분석' in analysis_results and '감정_분포' in analysis_results['감정분석']:
                plot_files['sentiment_distribution'] = self.create_sentiment_pie_chart(
                    analysis_results['감정분석']['감정_분포']
                )
            
            # 3. 부정 키워드 막대 그래프
            if '부정키워드' in analysis_results:
                plot_files['negative_keywords'] = self.create_negative_keywords_bar(
                    analysis_results['부정키워드']
                )
            
            # 4. Aspect별 감정 스택 막대 그래프
            if 'Aspect분석' in analysis_results and 'aspect_요약' in analysis_results['Aspect분석']:
                plot_files['aspect_sentiment'] = self.create_aspect_sentiment_stacked_bar(
                    analysis_results['Aspect분석']['aspect_요약']
                )
            
            # 5. 우선순위 점수 막대 그래프
            if '우선순위' in analysis_results:
                plot_files['priority_scores'] = self.create_priority_scores_bar(
                    analysis_results['우선순위']
                )
            
            # 6. 분기별 트렌드
            if '트렌드' in analysis_results and '분기별' in analysis_results['트렌드']:
                plot_files['quarterly_trend'] = self.create_quarterly_trend_plot(
                    analysis_results['트렌드']['분기별']
                )
            
            # 7. 세그먼트 분석
            if '세그먼트분석' in analysis_results:
                plot_files['segment_analysis'] = self.create_segment_analysis_plot(
                    analysis_results['세그먼트분석']
                )
            
            # 고급 분석 그래프
            # 8. SHAP 특성 중요도
            if '고급분석' in analysis_results and 'rating_prediction' in analysis_results['고급분석']:
                rating_prediction = analysis_results['고급분석']['rating_prediction']
                if 'SHAP_Analysis' in rating_prediction:
                    plot_files['shap_feature_importance'] = self.create_shap_feature_importance_plot(
                        rating_prediction['SHAP_Analysis']
                    )
                    plot_files['model_performance'] = self.create_model_performance_plot(rating_prediction)
            
            # 9. 토픽 분포
            if '고급분석' in analysis_results and 'topic_modeling' in analysis_results['고급분석']:
                plot_files['topic_distribution'] = self.create_topic_distribution_plot(
                    analysis_results['고급분석']['topic_modeling']
                )
            
            # 10. 변화점 탐지
            if '고급분석' in analysis_results and 'change_point_detection' in analysis_results['고급분석']:
                plot_files['change_point_detection'] = self.create_change_point_plot(
                    analysis_results['고급분석']['change_point_detection']
                )
            
            logger.info(f"모든 그래프 생성 완료: {len(plot_files)}개")
            
        except Exception as e:
            logger.error(f"그래프 생성 중 오류 발생: {e}")
            raise
        finally:
            # 원래 figures_dir 복원
            self.figures_dir = original_figures_dir
        
        # Path 객체로 변환
        plot_files_with_paths = {}
        for key, value in plot_files.items():
            if isinstance(value, str):
                plot_files_with_paths[key] = Path(value)
            else:
                plot_files_with_paths[key] = value
        
        return plot_files_with_paths
