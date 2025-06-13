# src/workout_importer/api/app.py
from flask import Flask, current_app, g
import os
from dotenv import load_dotenv # python-dotenv 라이브러리 임포트
from flask_cors import CORS # Flask-CORS 임포트 <-- 이 라인 추가

# 필요한 클래스 임포트
from ..database.postgres_manager import PostgreSQLDatabaseManager
from ..abstracts import AbstractDatabaseManager

# 블루프린트 임포트 (이 임포트는 그대로 유지)
from .workout_routes import workout_bp

# .env 파일에서 환경 변수 로드 (프로젝트 루트에 .env 파일이 있다고 가정)
# load_dotenv() 함수는 기본적으로 스크립트가 실행되는 디렉토리 또는 그 상위 디렉토리에서 .env 파일을 찾습니다.
# run_import.py와 같은 레벨에 .env가 있다면 load_dotenv()만 호출해도 됩니다.
# 특정 경로의 .env 파일을 지정할 수도 있습니다: load_dotenv('/path/to/your/workout_importer/.env')
load_dotenv()


# DatabaseManager 인스턴스를 가져오는 함수 정의 (요청 컨텍스트 내에서 사용)
# 이 함수는 인자를 받지 않습니다.
def get_db_manager() -> AbstractDatabaseManager:
    """Gets the database manager instance for the current app context."""
    # g 객체는 요청 컨텍스트 동안 데이터를 저장하는 데 사용됩니다.
    # 'db_manager' 키로 g 객체에 인스턴스가 없으면 새로 생성하여 저장
    if 'db_manager' not in g:
        # 설정에서 DB params 가져와 인스턴스 생성
        db_params = current_app.config.get('DB_PARAMS')
        if not db_params:
             raise RuntimeError("Database configuration not loaded.")

        # PostgreSQLDatabaseManager 인스턴스 생성 및 g 객체에 저장
        g.db_manager = PostgreSQLDatabaseManager(db_params)

        # TODO: 연결 풀링 등을 사용한다면 여기서 설정

    # g 객체에 저장된 DatabaseManager 인스턴스 반환
    return g.db_manager

# 요청 컨텍스트 종료 시 데이터베이스 연결을 닫는 함수 정의
def close_db_manager(e=None):
    """Closes the database connection at the end of the app context."""
    # g 객체에서 'db_manager' 인스턴스를 가져오기 (없으면 None 반환)
    db_manager = g.pop('db_manager', None)
    if db_manager is not None:
        # DatabaseManager의 close 메서드 호출
        db_manager.close()


def create_app():
    """Flask 애플리케이션 팩토리 함수."""
    app = Flask(__name__) # <-- 여기서 app 인스턴스가 생성됩니다.

    # TODO: 실제 운영 환경에서는 설정 파일 등을 사용하여 SECRET_KEY 설정 필요
    # app.config['SECRET_KEY'] = 'your_secret_key'

    # 1. 설정 로드 (환경 변수에서 읽어오는 예시)
    db_params = {
        "database": os.environ.get("DB_NAME", "workout_db"),
        "user": os.environ.get("DB_USER", "postgres"),
        "password": os.environ.get("DB_PASSWORD"), # 환경 변수에서 읽기
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": os.environ.get("DB_PORT", "5432"),
    }
    # 필수 DB 설정 값이 누락되었는지 확인하는 로직 추가 권장
    if not all([db_params.get("database"), db_params.get("user"), db_params.get("password"), db_params.get("host"), db_params.get("port")]):
         print("경고: 데이터베이스 연결 설정 환경 변수가 누락되었습니다!")
         # 실제 운영 환경에서는 여기서 앱 시작을 중단하거나 오류를 발생시켜야 합니다.
         # raise EnvironmentError("Database configuration environment variables not set.")


    app.config['DB_PARAMS'] = db_params # Flask 설정 객체에 저장

    # 2. CORS 적용 <-- 이 부분 추가
    # 개발 환경에서는 모든 출처(*)를 허용하도록 설정
    # 실제 운영 환경에서는 앱이 배포될 특정 출처만 허용하도록 변경해야 합니다.
    CORS(app) # 모든 라우트에 대해 CORS 허용

    # 특정 블루프린트나 라우트에만 적용할 수도 있습니다.
    # CORS(app, resources={r"/api/*": {"origins": "*"}}) # 예시: /api/ 로 시작하는 라우트에만 적용

    # 3. DatabaseManager 인스턴스 관리 함수를 앱 객체에 바인딩 (이전 수정 내용)
    # 블루프린트에서 current_app.get_db_manager()로 접근할 수 있게 됩니다.
    app.get_db_manager = get_db_manager # <-- 이 라인을 추가/수정 (이전 오류 해결을 위해 다시 추가)

    # 4. 블루프린트 등록
    app.register_blueprint(workout_bp)
    # TODO: 다른 기능(예: 사용자 관리, 모델 예측)에 대한 블루프rint도 여기에 임포트하고 등록

    # 5. 요청 컨텍스트 종료 시 실행될 함수 등록
    app.teardown_appcontext(close_db_manager)

    return app

# 이 파일을 직접 실행했을 때 (개발 서버 시작)
if __name__ == '__main__':
    # 팩토리 함수를 호출하여 앱 인스턴스 생성
    app = create_app()
    # 개발 서버 실행
    app.run(debug=True, host='0.0.0.0', port=5000)
