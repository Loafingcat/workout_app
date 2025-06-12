# src/workout_importer/api/app.py (또는 create_app 함수 시작 부분)
import os
from dotenv import load_dotenv # python-dotenv 라이브러리 임포트

# .env 파일에서 환경 변수 로드
# load_dotenv() 함수는 기본적으로 스크립트가 실행되는 디렉토리 또는 그 상위 디렉토리에서 .env 파일을 찾습니다.
# 프로젝트 루트에 .env 파일이 있다면 load_dotenv()만 호출해도 됩니다.
# 특정 경로의 .env 파일을 지정할 수도 있습니다: load_dotenv('/path/to/your/workout_importer/.env')
load_dotenv()

# 이제 os.environ.get()으로 환경 변수 값을 읽어올 수 있습니다.
db_params = {
    "database": os.environ.get("DB_NAME", "workout_db"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD"), # .env 파일에서 읽어옴
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
}