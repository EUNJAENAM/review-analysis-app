"""
고급 분석 모듈 - 평점 예측, 토픽 모델링, 변화점 탐지
"""
import pandas as pd
import numpy as np
import re
import logging
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path

# 머신러닝 라이브러리
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.decomposition import NMF, LatentDirichletAllocation
from sklearn.preprocessing import StandardScaler

# 고급 분석 라이브러리
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logging.warning("SHAP 라이브러리가 설치되지 않았습니다. SHAP 분석을 건너뜁니다.")

try:
    import ruptures
    RUPTURES_AVAILABLE = True
except ImportError:
    RUPTURES_AVAILABLE = False
    logging.warning("ruptures 라이브러리가 설치되지 않았습니다. 변화점 탐지를 건너뜁니다.")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("sentence-transformers 라이브러리가 설치되지 않았습니다. BERT 임베딩을 건너뜁니다.")

from .config import ANALYSIS_OPTIONS

logger = logging.getLogger(__name__)

class AdvancedAnalyzer:
    """고급 분석 클래스"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.advanced_options = ANALYSIS_OPTIONS.get('advanced_analysis', {})
        
    def create_features(self) -> pd.DataFrame:
        """평점 예측을 위한 특성을 생성합니다."""
        logger.info("평점 예측용 특성 생성 시작")
        
        # 기본 특성
        features_df = self.df.copy()
        
        # 텍스트 길이 특성
        features_df['제목_길이'] = features_df['제목'].astype(str).str.len()
        features_df['내용_길이'] = features_df['내용'].astype(str).str.len()
        features_df['평가_길이'] = features_df['평가'].astype(str).str.len()
        features_df['총_텍스트_길이'] = features_df['제목_길이'] + features_df['내용_길이'] + features_df['평가_길이']
        
        # 시간 관련 특성
        features_df['연도'] = features_df['작성일자'].dt.year
        features_df['월'] = features_df['작성일자'].dt.month
        features_df['분기'] = features_df['작성일자'].dt.quarter
        features_df['요일'] = features_df['작성일자'].dt.dayofweek
        
        # Aspect 키워드 특성
        aspect_keywords = {
            "청결": ["청결", "깨끗", "더럽", "지저분", "먼지", "바닥", "청소", "깔끔", "위생"],
            "시설": ["시설", "온수", "샤워", "온도", "따뜻", "차갑", "잠금장치", "리모델링", "노후", "낡"],
            "직원": ["직원", "응대", "서비스", "친절", "불친절", "태도", "안내", "프론트"],
            "가격": ["가격", "비싸", "저렴", "가성비", "요금", "비용", "패키지"],
            "온천": ["온천", "탄산", "온천수", "탕", "사우나", "찜질방", "목욕", "온천욕"]
        }
        
        for aspect, keywords in aspect_keywords.items():
            features_df[f'{aspect}_키워드_수'] = features_df['통합_텍스트'].apply(
                lambda text: sum(1 for keyword in keywords if keyword in text)
            )
        
        # 부정 키워드 특성
        negative_keywords = [
            "아쉽", "실망", "별로", "안좋", "나쁘", "불편", "문제", "결함", "고장",
            "부족", "떨어지", "낮", "안되", "못하", "싫", "짜증", "화나", "불쾌"
        ]
        features_df['부정_키워드_수'] = features_df['통합_텍스트'].apply(
            lambda text: sum(1 for keyword in negative_keywords if keyword in text)
        )
        
        # 긍정 키워드 특성
        positive_keywords = [
            "좋", "만족", "훌륭", "최고", "추천", "완벽", "완전", "대박", "최상",
            "감동", "감사", "사랑", "즐거", "행복", "편안", "안락", "훌륭"
        ]
        features_df['긍정_키워드_수'] = features_df['통합_텍스트'].apply(
            lambda text: sum(1 for keyword in positive_keywords if keyword in text)
        )
        
        # 감정 비율 특성
        features_df['긍정_비율'] = features_df['긍정_키워드_수'] / (features_df['긍정_키워드_수'] + features_df['부정_키워드_수'] + 1)
        features_df['부정_비율'] = features_df['부정_키워드_수'] / (features_df['긍정_키워드_수'] + features_df['부정_키워드_수'] + 1)
        
        logger.info("평점 예측용 특성 생성 완료")
        return features_df
    
    def train_rating_prediction_models(self, features_df: pd.DataFrame) -> Dict[str, Any]:
        """평점 예측 모델을 학습합니다."""
        logger.info("평점 예측 모델 학습 시작")
        
        # 특성 선택
        feature_columns = [
            '제목_길이', '내용_길이', '평가_길이', '총_텍스트_길이',
            '연도', '월', '분기', '요일',
            '청결_키워드_수', '시설_키워드_수', '직원_키워드_수', '가격_키워드_수', '온천_키워드_수',
            '부정_키워드_수', '긍정_키워드_수', '긍정_비율', '부정_비율'
        ]
        
        X = features_df[feature_columns].fillna(0)
        y = features_df['평점']
        
        # 데이터 분할
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # 모델 학습
        models = {
            'Linear Regression': LinearRegression(),
            'Ridge Regression': Ridge(alpha=1.0),
            'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42)
        }
        
        results = {}
        shap_values = None
        
        for name, model in models.items():
            logger.info(f"{name} 모델 학습 중...")
            
            # 모델 학습
            model.fit(X_train, y_train)
            
            # 예측
            y_pred = model.predict(X_test)
            
            # 성능 평가
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            cv_scores = cross_val_score(model, X, y, cv=5, scoring='r2')
            
            results[name] = {
                'model': model,
                'mse': mse,
                'r2': r2,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'feature_importance': None
            }
            
            # 특성 중요도 계산
            if hasattr(model, 'feature_importances_'):
                results[name]['feature_importance'] = dict(zip(feature_columns, model.feature_importances_))
            elif hasattr(model, 'coef_'):
                results[name]['feature_importance'] = dict(zip(feature_columns, np.abs(model.coef_)))
        
        # SHAP 분석 (Random Forest 모델에 대해)
        if SHAP_AVAILABLE and 'Random Forest' in results:
            logger.info("SHAP 분석 시작")
            rf_model = results['Random Forest']['model']
            explainer = shap.TreeExplainer(rf_model)
            shap_values = explainer.shap_values(X_test)
            
            # 상위 특성 추출
            feature_importance = results['Random Forest']['feature_importance']
            top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
            top_features = top_features[:self.advanced_options.get('shap_top_features', 10)]
            
            results['SHAP_Analysis'] = {
                'shap_values': shap_values,
                'top_features': top_features,
                'feature_names': feature_columns
            }
        
        logger.info("평점 예측 모델 학습 완료")
        return results
    
    def perform_topic_modeling(self) -> Dict[str, Any]:
        """토픽 모델링을 수행합니다."""
        logger.info("토픽 모델링 시작")
        
        # 텍스트 전처리
        texts = self.df['통합_텍스트'].fillna('').astype(str)
        
        # 불용어 정의
        stop_words = [
            '이', '그', '저', '것', '수', '등', '때', '곳', '말', '일', '년', '월', '일',
            '있다', '하다', '되다', '있다', '없다', '그렇다', '아니다', '이다',
            '있다', '있다', '있다', '있다', '있다', '있다', '있다', '있다'
        ]
        
        # TF-IDF 벡터화
        tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=stop_words,
            min_df=2,
            max_df=0.95,
            ngram_range=(1, 2)
        )
        
        tfidf_matrix = tfidf_vectorizer.fit_transform(texts)
        feature_names = tfidf_vectorizer.get_feature_names_out()
        
        # NMF 토픽 모델링
        n_topics = self.advanced_options.get('topic_count', 8)
        nmf = NMF(n_components=n_topics, random_state=42, max_iter=200)
        nmf.fit(tfidf_matrix)
        
        # 토픽 추출
        topics = []
        for topic_idx, topic in enumerate(nmf.components_):
            top_words_idx = topic.argsort()[-10:][::-1]
            top_words = [feature_names[i] for i in top_words_idx]
            topics.append({
                'topic_id': topic_idx + 1,
                'top_words': top_words,
                'weights': topic[top_words_idx]
            })
        
        # 문서별 토픽 분포
        doc_topics = nmf.transform(tfidf_matrix)
        
        # 연도별 토픽 비중 변화
        yearly_topic_distribution = self._calculate_yearly_topic_distribution(doc_topics)
        
        results = {
            'topics': topics,
            'doc_topics': doc_topics,
            'yearly_distribution': yearly_topic_distribution,
            'feature_names': feature_names,
            'tfidf_matrix': tfidf_matrix
        }
        
        logger.info("토픽 모델링 완료")
        return results
    
    def _calculate_yearly_topic_distribution(self, doc_topics: np.ndarray) -> pd.DataFrame:
        """연도별 토픽 분포를 계산합니다."""
        yearly_dist = []
        
        for year in sorted(self.df['연도'].unique()):
            year_mask = self.df['연도'] == year
            year_topics = doc_topics[year_mask]
            
            if len(year_topics) > 0:
                avg_topics = year_topics.mean(axis=0)
                yearly_dist.append([year] + avg_topics.tolist())
        
        columns = ['연도'] + [f'토픽_{i+1}' for i in range(doc_topics.shape[1])]
        return pd.DataFrame(yearly_dist, columns=columns)
    
    def detect_change_points(self) -> Dict[str, Any]:
        """연도별 평균 평점의 변화점을 탐지합니다."""
        logger.info("변화점 탐지 시작")
        
        if not RUPTURES_AVAILABLE:
            logger.warning("ruptures 라이브러리가 없어 변화점 탐지를 건너뜁니다.")
            return {}
        
        # 연도별 평균 평점 계산
        yearly_ratings = self.df.groupby('연도')['평점'].mean().reset_index()
        yearly_ratings = yearly_ratings.sort_values('연도')
        
        # 변화점 탐지
        signal = yearly_ratings['평점'].values
        years = yearly_ratings['연도'].values
        
        # Pelt 알고리즘 사용
        penalty = self.advanced_options.get('change_point_penalty', 10)
        algo = ruptures.Pelt(model="rbf").fit(signal)
        change_points = algo.predict(pen=penalty)
        
        # 변화점 정보 추출
        change_point_info = []
        for i, cp in enumerate(change_points[:-1]):  # 마지막 점은 제외
            if cp < len(years):
                year = years[cp]
                rating_before = signal[cp-1] if cp > 0 else signal[cp]
                rating_after = signal[cp] if cp < len(signal) else signal[cp-1]
                change = rating_after - rating_before
                
                change_point_info.append({
                    'year': int(year),
                    'rating_before': round(rating_before, 2),
                    'rating_after': round(rating_after, 2),
                    'change': round(change, 2),
                    'change_type': '상승' if change > 0 else '하락'
                })
        
        results = {
            'change_points': change_point_info,
            'yearly_ratings': yearly_ratings,
            'signal': signal,
            'years': years
        }
        
        logger.info("변화점 탐지 완료")
        return results
    
    def run_advanced_analysis(self) -> Dict[str, Any]:
        """모든 고급 분석을 실행합니다."""
        logger.info("고급 분석 시작")
        
        results = {}
        
        # 1. 평점 예측 모델
        if self.advanced_options.get('enable_rating_prediction', False):
            logger.info("평점 예측 모델 분석 시작")
            features_df = self.create_features()
            results['rating_prediction'] = self.train_rating_prediction_models(features_df)
        
        # 2. 토픽 모델링
        if self.advanced_options.get('enable_topic_modeling', False):
            logger.info("토픽 모델링 분석 시작")
            results['topic_modeling'] = self.perform_topic_modeling()
        
        # 3. 변화점 탐지
        if self.advanced_options.get('enable_change_point_detection', False):
            logger.info("변화점 탐지 분석 시작")
            results['change_point_detection'] = self.detect_change_points()
        
        logger.info("고급 분석 완료")
        return results
