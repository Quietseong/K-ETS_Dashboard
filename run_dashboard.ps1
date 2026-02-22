Write-Host "탄소배출권 대시보드 시작..." -ForegroundColor Green

# Streamlit 대시보드 실행 (포트 8501)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "streamlit run main.py --server.port 8501"

# 잠시 대기
Start-Sleep -Seconds 3

# FastAPI AI 보고서 서버 실행 (포트 8000)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python app_api.py"

Write-Host "대시보드가 시작되었습니다!" -ForegroundColor Yellow
Write-Host "Streamlit 대시보드: http://localhost:8501" -ForegroundColor Cyan
Write-Host "FastAPI 보고서 API: http://localhost:8000 (Swagger: http://localhost:8000/docs)" -ForegroundColor Cyan
