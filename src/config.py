"""
오색그린야드호텔 리뷰 분석 프로젝트 설정 파일
"""
import os
from pathlib import Path
from typing import Dict, List, Any

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent

# 데이터 경로
DATA_PATH = PROJECT_ROOT / "data" / "오색그린야드호텔_리뷰정보.csv"
FONT_PATH = PROJECT_ROOT / "assets" / "NanumBarunGothic.ttf"

# 출력 경로
OUTPUT_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUT_DIR / "figures"
REPORT_DIR = OUTPUT_DIR / "report"

# 템플릿 경로
TEMPLATE_DIR = PROJECT_ROOT / "templates"

# 분석 옵션 (성능 최적화)
ANALYSIS_OPTIONS = {
    "enable_advanced_analysis": False,  # 기본적으로 고급 분석 비활성화 (성능 향상)
    "sentiment_thresholds": {
        "positive": 8,  # 평점 8 이상 = 긍정
        "negative": 6,  # 평점 6 이하 = 부정
        "neutral": (6, 8)  # 평점 6-8 = 중립
    },
    "top_negative_keywords": 10,  # 부정 키워드 상위 N개
    "priority_score_weight": {
        "negative_ratio": 0.7,  # 부정 비율 가중치
        "mention_frequency": 0.3  # 언급 빈도 가중치
    },
    # 고급 분석 옵션 (성능 최적화)
    "advanced_analysis": {
        "enable_rating_prediction": False,  # 평점 예측 모델 (기본 비활성화)
        "enable_topic_modeling": False,     # 토픽 모델링 (기본 비활성화)
        "enable_change_point_detection": False,  # 변화점 탐지 (기본 비활성화)
        "shap_top_features": 5,            # SHAP 상위 특성 수 (줄임)
        "topic_count": 5,                  # 토픽 개수 (줄임)
        "min_topic_size": 10,              # 최소 토픽 크기 (늘림)
        "change_point_penalty": 5          # 변화점 탐지 페널티 (줄임)
    }
}

# Aspect 분석 키워드 사전
ASPECT_KEYWORDS = {
    "청결": [
        "청결", "깨끗", "더럽", "지저분", "먼지", "바닥", "청소", "깔끔", "위생"
    ],
    "시설/온수": [
        "시설", "온수", "샤워", "온도", "따뜻", "차갑", "잠금장치", "리모델링", 
        "노후", "낡", "시설", "객실", "침대", "TV", "난방", "에어컨"
    ],
    "직원응대": [
        "직원", "응대", "서비스", "친절", "불친절", "태도", "안내", "프론트", 
        "매니저", "부장", "고문", "격양", "말문막힘"
    ],
    "가격": [
        "가격", "비싸", "저렴", "가성비", "요금", "비용", "패키지", "강정", 
        "조식", "식사", "음식", "맛있", "맛없"
    ],
    "온천수": [
        "온천", "탄산", "온천수", "탕", "사우나", "찜질방", "목욕", "온천욕", 
        "온천물", "효능", "피로", "힐링", "선녀탕", "노천탕"
    ]
}

# 부정 키워드 사전 (간단 정규식 기반)
NEGATIVE_KEYWORDS = [
    "아쉽", "실망", "별로", "안좋", "나쁘", "불편", "문제", "결함", "고장",
    "부족", "떨어지", "낮", "안되", "못하", "싫", "짜증", "화나", "불쾌",
    "실종", "허", "늘어지", "떨어지", "낡", "오래", "노후", "지저분", "더럽",
    "차갑", "춥", "시끄럽", "소음", "비싸", "바가지", "불친절", "무시",
    "격양", "말문막힘", "아쉬워", "후회", "다시안갈", "추천안함"
]

# 세그먼트 분석 규칙
SEGMENT_RULES = {
    "가족": ["가족", "부모님", "아이", "애", "어린이", "자녀"],
    "등산": ["등산", "트레킹", "산행", "설악산", "주전골", "선녀탕", "만경대"],
    "장기고객": ["자주", "많이", "오래", "정기", "단골", "매년", "분기마다"]
}

# 그래프 설정
PLOT_CONFIG = {
    "figure_size": (12, 8),
    "dpi": 300,
    "style": "default",
    "colors": {
        "positive": "#2E8B57",  # Sea Green
        "negative": "#DC143C",  # Crimson
        "neutral": "#FFD700",   # Gold
        "primary": "#4682B4",   # Steel Blue
        "secondary": "#DDA0DD"  # Plum
    }
}

# 리포트 설정
REPORT_CONFIG = {
    "title": "오색그린야드호텔 리뷰 분석 리포트",
    "version": "1.0.0",
    "generated_date": None,  # 실행 시 설정
    "data_range": None,      # 실행 시 설정
    "reproduction_command": "python run.py"
}

# 리포트 메타데이터
REPORT_METADATA = {
    "hotel_name": "오색그린야드호텔",
    "analysis_type": "고객 리뷰 분석",
    "version": "1.0.0",
    "author": "리뷰 분석 시스템",
    "description": "고객 리뷰 데이터를 기반으로 한 종합적인 호텔 성과 분석 리포트"
}

def ensure_directories() -> None:
    """필요한 디렉터리들을 생성합니다."""
    directories = [OUTPUT_DIR, FIGURES_DIR, REPORT_DIR, TEMPLATE_DIR]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

def get_font_properties() -> Dict[str, Any]:
    """폰트 설정을 반환합니다."""
    if FONT_PATH.exists():
        return {
            "font.family": "NanumBarunGothic",
            "font.sans-serif": ["NanumBarunGothic", "DejaVu Sans"],
            "axes.unicode_minus": False
        }
    else:
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
        
        return {
            "font.family": "sans-serif",
            "font.sans-serif": korean_fonts,
            "axes.unicode_minus": False
        }
