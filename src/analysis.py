"""
리뷰 분석 모듈 - KPI, 감정분석, Aspect 분석, 우선순위 산정 (성능 최적화 버전)
"""
import pandas as pd
import numpy as np
import re
from typing import Dict, List, Tuple, Any
import logging
from collections import Counter

from .config import (
    ANALYSIS_OPTIONS, ASPECT_KEYWORDS, NEGATIVE_KEYWORDS, 
    SEGMENT_RULES
)
from .advanced_analysis import AdvancedAnalyzer

logger = logging.getLogger(__name__)

class ReviewAnalyzer:
    """리뷰 분석 클래스 (성능 최적화 버전)"""
    
    def __init__(self, df: pd.DataFrame, options: Dict[str, Any] = None):
        self.df = df.copy()
        self.options = options or ANALYSIS_OPTIONS
        self.sentiment_thresholds = self.options['sentiment_thresholds']
        
        # 성능 최적화: 한 번만 전처리
        self._preprocess_for_analysis()
        
    def _preprocess_for_analysis(self):
        """분석을 위한 데이터 전처리를 한 번만 수행"""
        logger.info("분석용 데이터 전처리 시작")
        
        # 1. 감정 라벨링 (한 번만 수행)
        self.df['감정'] = self.df['평점'].apply(self._label_sentiment)
        
        # 2. 통합 텍스트 생성 (한 번만 수행)
        self.df['통합_텍스트'] = (
            self.df['제목'].astype(str) + ' ' + 
            self.df['내용'].astype(str) + ' ' + 
            self.df['평가'].astype(str)
        )
        
        # 3. 키워드 매칭 결과를 미리 계산 (벡터화된 방식)
        self._precompute_keyword_matches()
        
        logger.info("분석용 데이터 전처리 완료")
    
    def _precompute_keyword_matches(self):
        """모든 키워드 매칭을 미리 계산하여 성능 향상"""
        # Aspect 키워드 매칭
        self.aspect_matches = {}
        for aspect_name, keywords in ASPECT_KEYWORDS.items():
            # 벡터화된 매칭: 각 키워드가 텍스트에 포함되는지 확인
            matches = self.df['통합_텍스트'].apply(
                lambda text: any(keyword in text for keyword in keywords)
            )
            self.aspect_matches[aspect_name] = matches
        
        # 세그먼트 키워드 매칭
        self.segment_matches = {}
        for segment_name, keywords in SEGMENT_RULES.items():
            matches = self.df['통합_텍스트'].apply(
                lambda text: any(keyword in text for keyword in keywords)
            )
            self.segment_matches[segment_name] = matches
        
        # 부정 키워드 매칭 (카운팅용)
        self.negative_keyword_counts = Counter()
        negative_reviews = self.df[self.df['평점'] <= self.sentiment_thresholds['negative']]
        
        if len(negative_reviews) > 0:
            all_negative_text = ' '.join(negative_reviews['통합_텍스트'])
            for keyword in NEGATIVE_KEYWORDS:
                count = len(re.findall(keyword, all_negative_text))
                if count > 0:
                    self.negative_keyword_counts[keyword] = count
    
    def calculate_kpis(self) -> Dict[str, Any]:
        """핵심 성과지표(KPI)를 계산합니다."""
        logger.info("KPI 계산 시작")
        
        kpis = {
            "총_리뷰_수": len(self.df),
            "평균_평점": round(self.df['평점'].mean(), 2),
            "최저_평점": self.df['평점'].min(),
            "최고_평점": self.df['평점'].max(),
            "최신_리뷰일": self.df['작성일자'].max().strftime('%Y-%m-%d'),
            "데이터_기간": {
                "시작일": self.df['작성일자'].min().strftime('%Y-%m-%d'),
                "종료일": self.df['작성일자'].max().strftime('%Y-%m-%d')
            }
        }
        
        # 감정 분포 계산 (이미 계산된 감정 컬럼 사용)
        sentiment_dist = self._calculate_sentiment_distribution()
        kpis.update(sentiment_dist)
        
        logger.info("KPI 계산 완료")
        return kpis
    
    def _calculate_sentiment_distribution(self) -> Dict[str, Any]:
        """감정 분포를 계산합니다."""
        sentiment_counts = self.df['감정'].value_counts()
        
        positive_count = sentiment_counts.get('긍정', 0)
        negative_count = sentiment_counts.get('부정', 0)
        neutral_count = sentiment_counts.get('중립', 0)
        
        total = len(self.df)
        
        return {
            "긍정_리뷰_수": positive_count,
            "부정_리뷰_수": negative_count,
            "중립_리뷰_수": neutral_count,
            "긍정_비율": positive_count / total,
            "부정_비율": negative_count / total,
            "중립_비율": neutral_count / total
        }
    
    def analyze_trends(self) -> Dict[str, pd.DataFrame]:
        """연도별, 분기별 트렌드를 분석합니다."""
        logger.info("트렌드 분석 시작")
        
        # 연도별 분석
        yearly_stats = self.df.groupby('연도').agg({
            '평점': ['count', 'mean'],
            '작성일자': 'max'
        }).round(2)
        yearly_stats.columns = ['리뷰_수', '평균_평점', '최신_리뷰일']
        
        # 분기별 분석
        quarterly_stats = self.df.groupby(['연도', '분기']).agg({
            '평점': ['count', 'mean']
        }).round(2)
        quarterly_stats.columns = ['리뷰_수', '평균_평점']
        quarterly_stats = quarterly_stats.reset_index()
        
        # 월별 분석
        monthly_stats = self.df.groupby(['연도', '월']).agg({
            '평점': ['count', 'mean']
        }).round(2)
        monthly_stats.columns = ['리뷰_수', '평균_평점']
        monthly_stats = monthly_stats.reset_index()
        
        logger.info("트렌드 분석 완료")
        return {
            "연도별": yearly_stats,
            "분기별": quarterly_stats,
            "월별": monthly_stats
        }
    
    def analyze_sentiment(self) -> Dict[str, Any]:
        """감정 분석을 수행합니다."""
        logger.info("감정 분석 시작")
        
        # 감정별 통계 (이미 계산된 감정 컬럼 사용)
        sentiment_stats = self.df['감정'].value_counts().to_dict()
        sentiment_ratio = (self.df['감정'].value_counts(normalize=True) * 100).round(1).to_dict()
        
        # 감정 변화 추이 (연도별)
        sentiment_trend = self.df.groupby(['연도', '감정']).size().unstack(fill_value=0)
        
        logger.info("감정 분석 완료")
        return {
            "감정_분포": sentiment_stats,
            "감정_비율": sentiment_ratio,
            "감정_변화_추이": sentiment_trend
        }
    
    def _label_sentiment(self, rating: float) -> str:
        """평점을 기반으로 감정을 라벨링합니다."""
        if rating >= self.sentiment_thresholds['positive']:
            return '긍정'
        elif rating <= self.sentiment_thresholds['negative']:
            return '부정'
        else:
            return '중립'
    
    def analyze_aspects(self) -> Dict[str, Any]:
        """Aspect 분석을 수행합니다."""
        logger.info("Aspect 분석 시작")
        
        aspect_results = {}
        
        # 미리 계산된 매칭 결과 사용
        for aspect_name in ASPECT_KEYWORDS.keys():
            aspect_results[aspect_name] = self._analyze_single_aspect_optimized(aspect_name)
        
        # 전체 Aspect 요약
        aspect_summary = self._summarize_aspects(aspect_results)
        
        logger.info("Aspect 분석 완료")
        return {
            "aspect_상세": aspect_results,
            "aspect_요약": aspect_summary
        }
    
    def _analyze_single_aspect_optimized(self, aspect_name: str) -> Dict[str, Any]:
        """단일 Aspect를 분석합니다 (최적화 버전)."""
        # 미리 계산된 매칭 결과 사용
        matched_mask = self.aspect_matches[aspect_name]
        matched_reviews = self.df[matched_mask]
        
        if len(matched_reviews) == 0:
            return {
                "매칭_리뷰_수": 0,
                "긍정_수": 0,
                "부정_수": 0,
                "중립_수": 0,
                "긍정_비율": 0,
                "부정_비율": 0,
                "중립_비율": 0,
                "평균_평점": 0
            }
        
        # 감정별 분류 (이미 계산된 감정 컬럼 사용)
        sentiment_counts = matched_reviews['감정'].value_counts()
        
        positive_count = sentiment_counts.get('긍정', 0)
        negative_count = sentiment_counts.get('부정', 0)
        neutral_count = sentiment_counts.get('중립', 0)
        total_count = len(matched_reviews)
        
        return {
            "매칭_리뷰_수": total_count,
            "긍정_수": positive_count,
            "부정_수": negative_count,
            "중립_수": neutral_count,
            "긍정_비율": round(positive_count / total_count * 100, 1) if total_count > 0 else 0,
            "부정_비율": round(negative_count / total_count * 100, 1) if total_count > 0 else 0,
            "중립_비율": round(neutral_count / total_count * 100, 1) if total_count > 0 else 0,
            "평균_평점": round(matched_reviews['평점'].mean(), 2)
        }
    
    def _summarize_aspects(self, aspect_results: Dict[str, Any]) -> pd.DataFrame:
        """Aspect 분석 결과를 요약합니다."""
        summary_data = []
        for aspect_name, result in aspect_results.items():
            summary_data.append({
                'Aspect': aspect_name,
                '매칭_리뷰_수': result['매칭_리뷰_수'],
                '긍정_비율': result['긍정_비율'],
                '부정_비율': result['부정_비율'],
                '중립_비율': result['중립_비율'],
                '평균_평점': result['평균_평점']
            })
        
        return pd.DataFrame(summary_data)
    
    def extract_negative_keywords(self, top_n: int = None) -> List[Tuple[str, int]]:
        """부정 키워드를 추출합니다."""
        if top_n is None:
            top_n = ANALYSIS_OPTIONS['top_negative_keywords']
        
        logger.info(f"부정 키워드 추출 시작 (상위 {top_n}개)")
        
        # 미리 계산된 결과 사용
        top_keywords = self.negative_keyword_counts.most_common(top_n)
        
        logger.info(f"부정 키워드 추출 완료: {len(top_keywords)}개")
        return top_keywords
    
    def analyze_segments(self) -> Dict[str, Any]:
        """세그먼트 분석을 수행합니다."""
        logger.info("세그먼트 분석 시작")
        
        segment_results = {}
        
        # 미리 계산된 매칭 결과 사용
        for segment_name in SEGMENT_RULES.keys():
            segment_results[segment_name] = self._analyze_single_segment_optimized(segment_name)
        
        logger.info("세그먼트 분석 완료")
        return segment_results
    
    def _analyze_single_segment_optimized(self, segment_name: str) -> Dict[str, Any]:
        """단일 세그먼트를 분석합니다 (최적화 버전)."""
        # 미리 계산된 매칭 결과 사용
        matched_mask = self.segment_matches[segment_name]
        matched_reviews = self.df[matched_mask]
        
        if len(matched_reviews) == 0:
            return {
                "매칭_리뷰_수": 0,
                "평균_평점": 0,
                "긍정_비율": 0,
                "부정_비율": 0
            }
        
        # 통계 계산 (이미 계산된 감정 컬럼 사용)
        sentiment_counts = matched_reviews['감정'].value_counts()
        
        positive_count = sentiment_counts.get('긍정', 0)
        negative_count = sentiment_counts.get('부정', 0)
        total_count = len(matched_reviews)
        
        return {
            "매칭_리뷰_수": total_count,
            "평균_평점": round(matched_reviews['평점'].mean(), 2),
            "긍정_비율": round(positive_count / total_count * 100, 1),
            "부정_비율": round(negative_count / total_count * 100, 1)
        }
    
    def calculate_priority_scores(self) -> pd.DataFrame:
        """개선사항 우선순위를 계산합니다."""
        logger.info("우선순위 점수 계산 시작")
        
        # Aspect 분석 결과 가져오기
        aspect_analysis = self.analyze_aspects()
        aspect_summary = aspect_analysis['aspect_요약']
        
        # 우선순위 점수 계산
        priority_scores = []
        for _, row in aspect_summary.iterrows():
            if row['매칭_리뷰_수'] > 0:  # 매칭된 리뷰가 있는 경우만
                # 부정 비율과 언급 빈도를 가중 평균
                negative_ratio_score = row['부정_비율'] / 100
                mention_frequency_score = row['매칭_리뷰_수'] / len(self.df)
                
                weights = self.options['priority_score_weight']
                priority_score = (
                    negative_ratio_score * weights['negative_ratio'] +
                    mention_frequency_score * weights['mention_frequency']
                )
                
                priority_scores.append({
                    'Aspect': row['Aspect'],
                    '부정_비율': row['부정_비율'],
                    '언급_빈도': round(mention_frequency_score * 100, 1),
                    '우선순위_점수': round(priority_score * 100, 2),
                    '매칭_리뷰_수': row['매칭_리뷰_수']
                })
        
        # 점수 기준으로 정렬
        priority_df = pd.DataFrame(priority_scores)
        priority_df = priority_df.sort_values('우선순위_점수', ascending=False)
        
        logger.info("우선순위 점수 계산 완료")
        return priority_df
    
    def analyze_all(self) -> Dict[str, Any]:
        """전체 분석을 수행하고 결과를 반환합니다."""
        logger.info("전체 분석 시작")
        
        # 각 분석 수행
        kpis = self.calculate_kpis()
        trends = self.analyze_trends()
        sentiment = self.analyze_sentiment()
        aspects = self.analyze_aspects()
        segments = self.analyze_segments()
        negative_keywords = self.extract_negative_keywords()
        priority_scores = self.calculate_priority_scores()
        
        # 우선순위 상위 3개 추출
        top_3_priority = []
        if not priority_scores.empty:
            top_3_priority = priority_scores.head(3).to_dict('records')
        
        summary = {
            "KPI": kpis,
            "트렌드": trends,
            "감정분석": sentiment,
            "Aspect분석": aspects,
            "세그먼트분석": segments,
            "부정키워드": negative_keywords,
            "우선순위": {
                "전체": priority_scores,
                "상위_3개": top_3_priority
            }
        }
        
        # 고급 분석 수행
        if self.options.get('enable_advanced_analysis', False):
            logger.info("고급 분석 시작")
            try:
                advanced_analyzer = AdvancedAnalyzer(self.df)
                advanced_results = advanced_analyzer.run_advanced_analysis()
                summary["고급분석"] = advanced_results
                logger.info("고급 분석 완료")
            except Exception as e:
                logger.error(f"고급 분석 중 오류 발생: {e}")
                summary["고급분석"] = {}
        
        logger.info("전체 분석 완료")
        return summary
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """전체 분석 결과를 요약합니다."""
        return self.analyze_all()
