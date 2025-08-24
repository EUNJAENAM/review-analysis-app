#!/usr/bin/env python3
"""
폰트 테스트 스크립트
"""
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathlib import Path

def test_font():
    """폰트 테스트"""
    # 폰트 파일 경로
    font_path = Path('assets/NanumBarunGothic.ttf')
    
    if not font_path.exists():
        print("폰트 파일을 찾을 수 없습니다!")
        return
    
    # 폰트 등록
    fm.fontManager.addfont(str(font_path))
    font_prop = fm.FontProperties(fname=str(font_path))
    
    print(f"폰트 이름: {font_prop.get_name()}")
    print(f"폰트 패밀리: {font_prop.get_family()}")
    
    # matplotlib 설정
    plt.rcParams['font.family'] = font_prop.get_name()
    plt.rcParams['font.sans-serif'] = [font_prop.get_name()]
    plt.rcParams['axes.unicode_minus'] = False
    
    # 테스트 그래프 생성
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 한글 텍스트 테스트
    ax.text(0.1, 0.8, '오색그린야드호텔', fontsize=20, fontproperties=font_prop)
    ax.text(0.1, 0.6, '리뷰 분석 결과', fontsize=16, fontproperties=font_prop)
    ax.text(0.1, 0.4, '청결, 시설, 직원응대, 가격, 온천수', fontsize=14, fontproperties=font_prop)
    ax.text(0.1, 0.2, '긍정, 부정, 중립', fontsize=12, fontproperties=font_prop)
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title('한글 폰트 테스트', fontsize=18, fontproperties=font_prop)
    
    plt.tight_layout()
    plt.savefig('font_test.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print("폰트 테스트 완료! font_test.png 파일을 확인하세요.")

if __name__ == "__main__":
    test_font()
