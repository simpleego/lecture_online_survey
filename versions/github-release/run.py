"""배포 서버 실행: python run.py (기본 포트 8080)."""
import os
import uvicorn

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
