# src/workout_importer/config.py

import os
from dotenv import load_dotenv

# .env 파일 로드 (프로젝트 루트 또는 상위 디렉토리)
# 이 파일에서 환경 변수를 로드하므로 app.py에서는 load_dotenv()를 삭제합니다.
load_dotenv()

class BaseConfig:

    DB_NAME = os.environ.get("DB_NAME", "workout_db")
    DB_USER = os.environ.get("DB_USER", "postgres")
    DB_PASSWORD = os.environ.get("DB_PASSWORD")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "5432")

    # Flask 설정 객체에 저장될 DB_PARAMS 딕셔너리
    DB_PARAMS = {
        "database": DB_NAME,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "host": DB_HOST,
        "port": DB_PORT,
    }

    # 필수 DB 설정 값 누락 확인 (설정 로드 시 오류 발생)
    REQUIRED_DB_PARAMS = ["database", "user", "password", "host", "port"]
    if not all(DB_PARAMS.get(key) for key in REQUIRED_DB_PARAMS):
         # raise EnvironmentError("Database configuration environment variables not set.")
         print("경고: 데이터베이스 연결 설정 환경 변수가 누락되었습니다!")
