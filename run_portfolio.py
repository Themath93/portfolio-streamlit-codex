#!/usr/bin/env python3
"""
Streamlit 포트폴리오 실행 스크립트
"""

import subprocess
import sys
import os

def check_streamlit():
    """Streamlit 설치 확인"""
    try:
        import streamlit
        print(f"✅ Streamlit {streamlit.__version__} 설치됨")
        return True
    except ImportError:
        print("❌ Streamlit이 설치되지 않았습니다.")
        return False

def install_streamlit():
    """Streamlit 설치 시도"""
    print("Streamlit 설치를 시도합니다...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
        print("✅ Streamlit 설치 완료")
        return True
    except subprocess.CalledProcessError:
        print("❌ Streamlit 설치 실패")
        return False

def run_app():
    """애플리케이션 실행"""
    app_file = "app_simple.py" if os.path.exists("app_simple.py") else "app.py"
    
    print(f"🚀 {app_file} 실행 중...")
    print("브라우저에서 http://localhost:8501 을 열어 확인하세요.")
    print("종료하려면 Ctrl+C를 누르세요.")
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", app_file])
    except KeyboardInterrupt:
        print("\n👋 애플리케이션이 종료되었습니다.")
    except FileNotFoundError:
        print(f"❌ {app_file} 파일을 찾을 수 없습니다.")

def main():
    """메인 함수"""
    print("=== Streamlit 포트폴리오 실행기 ===")
    
    if not check_streamlit():
        if input("Streamlit을 설치하시겠습니까? (y/n): ").lower() == 'y':
            if not install_streamlit():
                sys.exit(1)
        else:
            print("Streamlit이 필요합니다. 먼저 설치해주세요:")
            print("pip install streamlit")
            sys.exit(1)
    
    run_app()

if __name__ == "__main__":
    main()