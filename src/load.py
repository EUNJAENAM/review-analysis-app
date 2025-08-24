"""
데이터 로드 및 전처리 모듈
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Tuple, Optional
import logging
from pathlib import Path

from .config import DATA_PATH

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataLoader:
    """데이터 로드 및 전처리 클래스"""
    
    def __init__(self, data_path: Path = DATA_PATH):
        self.data_path = data_path
        self.df = None
        
    def load_data(self) -> pd.DataFrame:
        """CSV 파일을 로드합니다."""
        try:
            logger.info(f"데이터 로드 중: {self.data_path}")
            self.df = pd.read_csv(self.data_path, encoding='utf-8')
            logger.info(f"데이터 로드 완료: {len(self.df)} 행, {len(self.df.columns)} 컬럼")
            return self.df
        except FileNotFoundError:
            logger.error(f"데이터 파일을 찾을 수 없습니다: {self.data_path}")
            raise
        except Exception as e:
            logger.error(f"데이터 로드 중 오류 발생: {e}")
            raise
    
    def validate_schema(self) -> bool:
        """데이터 스키마를 검증합니다."""
        expected_columns = ['제목', '내용', '평점', '작성일자', '평가', '이용자', '구분']
        
        if self.df is None:
            logger.error("데이터가 로드되지 않았습니다.")
            return False
            
        missing_columns = set(expected_columns) - set(self.df.columns)
        if missing_columns:
            logger.error(f"필수 컬럼이 누락되었습니다: {missing_columns}")
            return False
            
        logger.info("스키마 검증 완료")
        return True
    
    def preprocess_data(self) -> pd.DataFrame:
        """데이터 전처리를 수행합니다."""
        if self.df is None:
            raise ValueError("데이터가 로드되지 않았습니다.")
            
        logger.info("데이터 전처리 시작")
        
        # 1. 평점 전처리
        self._preprocess_ratings()
        
        # 2. 날짜 전처리
        self._preprocess_dates()
        
        # 3. 결측치 처리
        self._handle_missing_values()
        
        # 4. 이상치 처리
        self._handle_outliers()
        
        # 5. 텍스트 데이터 정제
        self._clean_text_data()
        
        logger.info("데이터 전처리 완료")
        return self.df
    
    def _preprocess_ratings(self) -> None:
        """평점 데이터를 전처리합니다."""
        # 평점 컬럼에서 공백 제거 및 숫자 변환
        self.df['평점'] = self.df['평점'].astype(str).str.strip()
        
        # 숫자가 아닌 값 처리
        self.df['평점'] = pd.to_numeric(self.df['평점'], errors='coerce')
        
        # 평점 범위 검증 (1-10)
        invalid_ratings = self.df[(self.df['평점'] < 1) | (self.df['평점'] > 10)]
        if len(invalid_ratings) > 0:
            logger.warning(f"유효하지 않은 평점 {len(invalid_ratings)}개 발견")
            # 유효하지 않은 평점을 NaN으로 설정
            self.df.loc[invalid_ratings.index, '평점'] = np.nan
    
    def _preprocess_dates(self) -> None:
        """날짜 데이터를 전처리합니다."""
        # 작성일자를 datetime으로 변환
        self.df['작성일자'] = pd.to_datetime(self.df['작성일자'], errors='coerce')
        
        # 연도, 월, 분기 컬럼 추가
        self.df['연도'] = self.df['작성일자'].dt.year
        self.df['월'] = self.df['작성일자'].dt.month
        self.df['분기'] = self.df['작성일자'].dt.quarter
        
        # 유효하지 않은 날짜 처리
        invalid_dates = self.df[self.df['작성일자'].isna()]
        if len(invalid_dates) > 0:
            logger.warning(f"유효하지 않은 날짜 {len(invalid_dates)}개 발견")
    
    def _handle_missing_values(self) -> None:
        """결측치를 처리합니다."""
        # 결측치 현황 로깅
        missing_info = self.df.isnull().sum()
        if missing_info.sum() > 0:
            logger.info(f"결측치 현황:\n{missing_info[missing_info > 0]}")
        
        # 평점 결측치 처리 (중앙값으로 대체)
        if self.df['평점'].isnull().sum() > 0:
            median_rating = self.df['평점'].median()
            self.df['평점'].fillna(median_rating, inplace=True)
            logger.info(f"평점 결측치 {self.df['평점'].isnull().sum()}개를 중앙값({median_rating})으로 대체")
        
        # 텍스트 결측치 처리
        text_columns = ['제목', '내용', '평가']
        for col in text_columns:
            if col in self.df.columns:
                self.df[col].fillna('', inplace=True)
    
    def _handle_outliers(self) -> None:
        """이상치를 처리합니다."""
        # 평점 이상치 처리 (IQR 방법)
        Q1 = self.df['평점'].quantile(0.25)
        Q3 = self.df['평점'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = self.df[(self.df['평점'] < lower_bound) | (self.df['평점'] > upper_bound)]
        if len(outliers) > 0:
            logger.warning(f"평점 이상치 {len(outliers)}개 발견 (범위: {lower_bound:.2f} ~ {upper_bound:.2f})")
            # 이상치를 경계값으로 조정
            self.df.loc[self.df['평점'] < lower_bound, '평점'] = lower_bound
            self.df.loc[self.df['평점'] > upper_bound, '평점'] = upper_bound
    
    def _clean_text_data(self) -> None:
        """텍스트 데이터를 정제합니다."""
        # 텍스트 컬럼들의 공백 제거 및 정규화
        text_columns = ['제목', '내용', '평가']
        for col in text_columns:
            if col in self.df.columns:
                self.df[col] = self.df[col].astype(str).str.strip()
                # 빈 문자열을 NaN으로 변환 후 다시 빈 문자열로
                self.df[col] = self.df[col].replace('', np.nan).fillna('')
    
    def get_data_info(self) -> dict:
        """데이터 기본 정보를 반환합니다."""
        if self.df is None:
            return {}
            
        return {
            "총_리뷰_수": len(self.df),
            "평균_평점": self.df['평점'].mean(),
            "최저_평점": self.df['평점'].min(),
            "최고_평점": self.df['평점'].max(),
            "데이터_기간": {
                "시작일": self.df['작성일자'].min().strftime('%Y-%m-%d'),
                "종료일": self.df['작성일자'].max().strftime('%Y-%m-%d')
            },
            "구분_별_리뷰_수": self.df['구분'].value_counts().to_dict()
        }
    
    def get_clean_data(self) -> pd.DataFrame:
        """전처리가 완료된 깨끗한 데이터를 반환합니다."""
        if self.df is None:
            self.load_data()
            self.validate_schema()
            self.preprocess_data()
        
        return self.df.copy()

def load_and_preprocess_data() -> Tuple[pd.DataFrame, dict]:
    """데이터를 로드하고 전처리하여 반환합니다."""
    loader = DataLoader()
    df = loader.get_clean_data()
    info = loader.get_data_info()
    
    return df, info
