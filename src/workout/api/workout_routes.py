# src/workout_importer/api/workout_routes.py
from flask import Blueprint, request, jsonify, current_app, g # current_app, g 임포트
from datetime import datetime, date
from typing import Optional, Dict, Any, List

# 상위 패키지에서 필요한 클래스 및 함수 임포트
from ..models import WorkoutRecord # WorkoutRecord 객체 생성 및 사용
# DatabaseManager 구현체는 직접 임포트하지 않고 추상 타입만 사용
# from ..database.postgres_manager import PostgreSQLDatabaseManager
from ..abstracts import AbstractDatabaseManager # 추상 DB 관리자 타입 힌트용

# app.py 모듈에서 get_db_manager 함수를 직접 임포트하지 않습니다.
# from .app import get_db_manager # <-- 이 라인을 제거

# 블루프린트 객체 생성
workout_bp = Blueprint('workout_api', __name__, url_prefix='/workouts')

# 데이터베이스 CHECK 제약 조건에 있는 허용된 운동 종목 목록
# models.py 또는 parsers.py에서 임포트하여 사용하는 것이 더 좋지만,
# 여기서는 예시로 직접 정의합니다.
ALLOWED_EXERCISE_TYPES = ['벤치프레스', '데드리프트', '스쿼트']

# --- API 엔드포인트 정의 ---

# POST /workouts/ : 새로운 운동 기록 추가
@workout_bp.route('/', methods=['POST'])
def add_workout_record():
    """
    앱으로부터 운동 기록 데이터를 받아 데이터베이스에 저장합니다.
    요청 본문은 JSON 형식이어야 합니다.
    예상 요청 본문:

    # 날짜는 서버에서 자동 생성
    {
        "exercise_type": "벤치프레스",
        "weight": 100,
        "reps": 5,
        "sets": 1
    }
    """
    # ... (이전 코드 - JSON 데이터 받기, 필수 필드 확인, 유효성 검사, 날짜 설정, WorkoutRecord 생성) ...
    data = request.get_json()

    required_fields = ['exercise_type', 'weight', 'reps', 'sets']
    if not data or not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    exercise_type = data.get('exercise_type')
    weight = data.get('weight')
    reps = data.get('reps')
    sets = data.get('sets')

    if exercise_type not in ALLOWED_EXERCISE_TYPES:
         return jsonify({"message": f"Invalid exercise type: {exercise_type}. Allowed types are: {', '.join(ALLOWED_EXERCISE_TYPES)}"}), 400

    try:
        if weight is None or reps is None or sets is None:
             raise TypeError("Weight, reps, or sets is None")
        weight = int(weight)
        reps = int(reps)
        sets = int(sets)
        if weight < 0 or reps < 0 or sets <= 0:
             return jsonify({"message": "Weight, reps must be non-negative, sets must be positive"}), 400
    except (ValueError, TypeError) as e:
         print(f"Validation Error: {e}")
         return jsonify({"message": "Invalid data type for weight, reps, or sets. Must be integers."}), 400
    except Exception as e:
         print(f"Unexpected Validation Error: {e}")
         return jsonify({"message": "An unexpected error occurred during validation."}), 500

    record_date = date.today()

    try:
        new_record = WorkoutRecord(
            record_date=record_date,
            exercise_type=exercise_type,
            weight=weight,
            reps=reps,
            sets=sets
        )
    except Exception as e:
        print(f"Error creating WorkoutRecord: {e}")
        return jsonify({"message": "Error processing record data"}), 500

    # 6. 데이터베이스에 저장
    # DatabaseManager 인스턴스 가져오기 (current_app.get_db_manager() 호출)
    # app.py에서 get_db_manager 함수가 앱 객체에 바인딩되었으므로 current_app을 통해 접근 가능
    db_manager: AbstractDatabaseManager = current_app.get_db_manager() # <-- 이 부분을 수정

    records_to_insert: List[WorkoutRecord] = [new_record]

    try:
        inserted_count = db_manager.insert_records(records_to_insert)

        if inserted_count > 0:
            return jsonify({
                "message": "Workout record saved successfully",
                "estimated_1rm_for_set": new_record.estimated_1rm
            }), 201
        else:
            print("Database insert failed with no specific exception caught in route.")
            return jsonify({"message": "Failed to save workout record to database"}), 500

    except Exception as e:
        print(f"Unexpected error during database insert: {e}")
        return jsonify({"message": "An unexpected error occurred while saving to database."}), 500


# GET /workouts/ : 전체 운동 기록 조회
@workout_bp.route('/', methods=['GET'])
def get_workout_records():
    """데이터베이스에 저장된 모든 운동 기록 목록을 조회합니다."""
    # DatabaseManager 인스턴스 가져오기 (current_app.get_db_manager() 호출)
    db_manager: AbstractDatabaseManager = current_app.get_db_manager() # <-- 이 부분을 수정

    query = "SELECT * FROM records ORDER BY record_date DESC, sets ASC"
    records_data = db_manager.fetch_records(query)

    # 날짜 객체 JSON 직렬화 문제 고려 (위 GET /workouts/ 와 동일)
    # fetch_records에서 이미 딕셔너리 형태로 반환되지만, 날짜가 date 객체일 수 있으므로
    # JSON 직렬화 가능한 형태로 변환하는 과정이 필요할 수 있습니다.
    # psycopg2의 기본 설정에 따라 date 객체가 문자열로 변환될 수도 있습니다.
    # 만약 date 객체 그대로 반환된다면, 각 레코드의 날짜를 문자열로 변환하는 로직 추가 필요
    # 예: for record in records_data: record['record_date'] = record['record_date'].isoformat() if isinstance(record['record_date'], date) else record['record_date']


    return jsonify(records_data), 200