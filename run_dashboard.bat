@echo off
chcp 65001 >nul
echo 탄소배출권 대시보드 시작...

REM Streamlit 대시보드 실행 (포트 8501)
start "메인 대시보드" cmd /k "streamlit run main.py --server.port 8501"

REM 잠시 대기
timeout /t 3

REM FastAPI AI 보고서 서버 실행 (포트 8000)
start "AI 보고서 API" cmd /k "python app_api.py"

echo 대시보드가 시작되었습니다!
echo Streamlit 대시보드: http://localhost:8501
echo FastAPI 보고서 API: http://localhost:8000 (Swagger: http://localhost:8000/docs)
pause
