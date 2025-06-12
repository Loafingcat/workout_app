# run_import.py
import os
from typing import List

# src 패키지에서 필요한 클래스들을 임포트합니다.
# run_import.py는 프로젝트 루트 디렉토리에서 실행될 것을 가정합니다.
# 따라서 src 디렉토리를 기준으로 임포트 경로를 지정합니다.
from src.workout.abstracts import AbstractWorkoutParser, AbstractDatabaseManager
from src.workout.parsers.text_parser import TextFileWorkoutParser
from src.workout.database.postgres_manager import PostgreSQLDatabaseManager
from src.workout.models import WorkoutRecord # 타입 힌트용

# 데이터베이스 연결 정보
# 실제 비밀번호는 환경 변수 등으로 관리하는 것이 좋습니다.
db_params = {
    "database": "workout_db",
    "user": "postgres",
    "password": "1234", # 여기에 실제 PostgreSQL 비밀번호 입력
    "host": "localhost",
    "port": "5432",
}

# 텍스트 파일 경로 (run_import.py 스크립트와 같은 디렉토리에 있다고 가정)
# 또는 절대 경로 지정: '/home/loafingcat/flask-app/B2M.txt'
txt_file_path = 'B2M.txt' # run_import.py와 같은 디렉토리에 있다면 상대 경로 사용 가능

def main():
    """파일을 파싱하고 추상 타입을 사용하여 DB에 데이터를 삽입하는 메인 함수입니다."""

    print("--- 운동 기록 데이터 가져오기 프로세스 시작 ---")

    # --- 클라이언트 코드 ---
    # 1. 파서 선택 및 인스턴스 생성 (구체 클래스 사용)
    # 하지만 변수 타입 힌트는 추상 클래스로 지정 (Code to an interface)
    parser: AbstractWorkoutParser = TextFileWorkoutParser()

    # 2. 데이터 파싱 (추상 메서드 호출)
    # parse 메서드는 WorkoutRecord 객체 리스트를 반환합니다.
    parsed_records: List[WorkoutRecord] = parser.parse(txt_file_path)

    if not parsed_records:
        print("파싱된 데이터가 없어 데이터베이스 삽입을 건너뜁니다.")
        print("--- 운동 기록 데이터 가져오기 프로세스 완료 (데이터 없음) ---")
        return

    # 3. 데이터베이스 관리자 선택 및 인스턴스 생성 (구체 클래스 사용)
    # 하지만 변수 타입 힌트는 추상 클래스로 지정
    db_manager: AbstractDatabaseManager = PostgreSQLDatabaseManager(db_params)

    # 4. 데이터베이스 연결 (추상 메서드 호출)
    if not db_manager.connect():
        print("데이터베이스 연결 실패. 프로그램 종료.")
        print("--- 운동 기록 데이터 가져오기 프로세스 실패 ---")
        return

    # 5. 데이터베이스 삽입 (추상 메서드 호출)
    # insert_records 메서드는 WorkoutRecord 객체 리스트를 받습니다.
    inserted_count = db_manager.insert_records(parsed_records)
    print(f"총 {inserted_count}개의 레코드가 데이터베이스에 삽입 시도되었습니다.")

    # 6. 데이터베이스 연결 닫기 (추상 메서드 호출)
    db_manager.close()

    print("--- 운동 기록 데이터 가져오기 프로세스 완료 ---")


if __name__ == "__main__":
    # 중요: 이 스크립트를 실행하기 전에 PostgreSQL 서버가 실행 중이고,
    # 'workout_db' 데이터베이스에 올바른 스키마와 CHECK 제약 조건을 가진
    # 'records' 테이블이 존재하는지 확인.
    # 테이블 스키마를 수정했다면, 스크립트 실행 전에 psql에서 테이블을 삭제하고 재생성.

    # python run_import.py
    # 또는 부모 디렉토리에서 실행하는 방법:
    # python -m src.workout.run_import # __init__.py
    # (src 디렉토리를 PYTHONPATH에 추가하거나 모듈로 실행해야 함)

    main()