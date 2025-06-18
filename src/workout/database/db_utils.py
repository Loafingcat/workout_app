from flask import g, current_app
from .postgres_manager import PostgreSQLDatabaseManager
from ..abstracts import AbstractDatabaseManager


def get_db_manager() -> AbstractDatabaseManager:
    
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
   
    db_manager = g.pop('db_manager', None)
    if db_manager is not None:
        db_manager.close()