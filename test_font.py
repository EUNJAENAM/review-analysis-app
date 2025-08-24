#!/usr/bin/env python3
"""
한글 폰트 테스트 스크립트
"""
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathlib import Path

def test_korean_fonts():
    """한글 폰트 테스트"""
    print("=== 한글 폰트 테스트 ===")
    
    # 사용 가능한 폰트 목록 출력
    print("\n사용 가능한 폰트들:")
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    korean_fonts = [
        "Malgun Gothic", "NanumGothic", "NanumBarunGothic", 
        "Dotum", "Gulim", "Batang", "Gungsuh", "Arial Unicode MS"
    ]
    
    for font in korean_fonts:
        if font in available_fonts:
            print(f"✓ {font} - 사용 가능")
        else:
            print(f"✗ {font} - 사용 불가")
    
    # 한글 폰트 설정
    selected_font = None
    for font in korean_fonts:
        if font in available_fonts:
            selected_font = font
            break
    
    if selected_font:
        plt.rcParams['font.family'] = selected_font
        print(f"\n선택된 폰트: {selected_font}")
    else:
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
        print("\n기본 폰트 사용")
    
    plt.rcParams['axes.unicode_minus'] = False
    
    # 현재 설정된 폰트 확인
    print(f"현재 설정된 폰트: {plt.rcParams['font.family']}")
    
    # 테스트 그래프 생성
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 한글 텍스트 테스트
    ax.text(0.5, 0.8, '한글 테스트: 오색그린야드호텔', 
            fontsize=20, ha='center', va='center')
    ax.text(0.5, 0.6, '리뷰 분석 결과', 
            fontsize=16, ha='center', va='center')
    ax.text(0.5, 0.4, '긍정: 46.8%, 부정: 39.1%, 중립: 14.2%', 
            fontsize=14, ha='center', va='center')
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    # 저장
    test_file = Path('font_test.png')
    plt.savefig(test_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"\n테스트 이미지 저장: {test_file}")
    print("이미지를 확인하여 한글이 제대로 표시되는지 확인하세요.")

if __name__ == "__main__":
    test_korean_fonts()
