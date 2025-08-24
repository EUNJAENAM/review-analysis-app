#!/usr/bin/env python3
"""
웹 애플리케이션 실행 스크립트
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 환경 변수 설정
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '1'

if __name__ == '__main__':
    from app import app
    
    print("=" * 60)
    print("오색그린야드호텔 리뷰 분석 웹 애플리케이션")
    print("=" * 60)
    print(f"서버 시작: http://localhost:5000")
    print("종료하려면 Ctrl+C를 누르세요")
    print("=" * 60)
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n서버가 종료되었습니다.")
    except Exception as e:
        print(f"서버 실행 중 오류 발생: {e}")
        sys.exit(1)
