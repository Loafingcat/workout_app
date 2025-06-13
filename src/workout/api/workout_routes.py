# src/workout_importer/api/workout_routes.py
from flask import Blueprint, request, jsonify, current_app, g # current_app, g 임포트
from datetime import datetime, date
from typing import Optional, Dict, Any, List

# 상위 패키지에서 필요한 클래스 및 함수 임포트
from ..models import WorkoutRecord # WorkoutRecord 객체 생성 및 사용
# DatabaseManager 구현체는 직접 임포트하지 않고 추상 타입만 사용
# from ..database.postgres_manager import PostgreSQLDatabaseManager
from ..abstracts import AbstractDatabaseManager # 추상 DB 관리자 타입 힌트용

# app.py 모듈에서 get_db_manager 함수 임포트
# from .app import get_db_manager # <-- 순환 임포트 방지를 위해 이 라인은 제거되었습니다.

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
    # 1. 클라이언트로부터 JSON 데이터 받기
    data = request.get_json()

    # 2. 필수 입력값 확인
    required_fields = ['exercise_type', 'weight', 'reps', 'sets']
    if not data or not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    # 3. 입력 데이터 추출 및 유효성 검사
    exercise_type = data.get('exercise_type')
    weight = data.get('weight')
    reps = data.get('reps')
    sets = data.get('sets')

    # --- 운동 종목 유효성 검사 및 표준화 ---
    # 받은 exercise_type이 문자열인지 확인하고 앞뒤 공백을 제거하여 표준화합니다. <-- 이 부분 수정
    if isinstance(exercise_type, str):
        exercise_type = exercise_type.strip()
    else:
        # 문자열이 아닌 경우 오류 처리 (예: None이거나 숫자인 경우)
        return jsonify({"message": "Invalid data type for exercise_type. Must be a string."}), 400

    # 표준화된 exercise_type이 허용된 목록에 있는지 확인
    if exercise_type not in ALLOWED_EXERCISE_TYPES:
         # 오류 메시지에 표준화된 exercise_type 값을 따옴표로 묶어 포함하여 디버깅에 도움
         return jsonify({"message": f"Invalid exercise type: '{exercise_type}'. Allowed types are: {', '.join(ALLOWED_EXERCISE_TYPES)}"}), 400

    # --- 숫자 타입 변환 및 유효성 검사 ---
    try:
        # 입력 값이 None일 경우 int() 변환 시 TypeError 발생하므로 미리 체크
        if weight is None or reps is None or sets is None:
             raise TypeError("Weight, reps, or sets is None")

        weight = int(weight)
        reps = int(reps)
        sets = int(sets)

        if weight < 0 or reps < 0 or sets <= 0:
             return jsonify({"message": "Weight, reps must be non-negative, sets must be positive"}), 400
    except (ValueError, TypeError) as e:
         # ValueError: int() 변환 실패 (예: "abc")
         # TypeError: data.get() 결과가 None일 때 int() 시도
         print(f"Validation Error: {e}") # 서버 로그에 오류 출력
         return jsonify({"message": "Invalid data type for weight, reps, or sets. Must be integers."}), 400
    except Exception as e:
         # 예상치 못한 다른 오류
         print(f"Unexpected Validation Error: {e}")
         return jsonify({"message": "An unexpected error occurred during validation."}), 500


    # 4. 기록 날짜 설정 (데이터가 입력된 당시 날짜 기준)
    record_date = date.today() # datetime.date 객체 사용

    # 5. WorkoutRecord 객체 생성 (1RM 자동 계산 포함)
    # estimated_1rm은 WorkoutRecord 생성자에서 weight, reps로 자동 계산됨
    try:
        new_record = WorkoutRecord(
            record_date=record_date,
            exercise_type=exercise_type, # 표준화된 exercise_type 사용
            weight=weight,
            reps=reps,
            sets=sets
        )
    except Exception as e:
        print(f"Error creating WorkoutRecord: {e}") # 서버 로그에 오류 출력
        return jsonify({"message": "Error processing record data"}), 500 # 500 Internal Server Error

    # 6. 데이터베이스에 저장
    # DatabaseManager 인스턴스 가져오기 (app.py에서 등록된 함수 사용)
    # app.py에서 get_db_manager 함수가 앱 객체에 바인딩되었으므로 current_app을 통해 접근 가능
    db_manager: AbstractDatabaseManager = current_app.get_db_manager()

    records_to_insert: List[WorkoutRecord] = [new_record]

    try:
        inserted_count = db_manager.insert_records(records_to_insert)

        if inserted_count > 0:
            # 성공 응답
            # 삽입된 레코드의 ID를 반환하려면 insert_records 메서드 수정 필요
            return jsonify({
                "message": "Workout record saved successfully",
                "estimated_1rm_for_set": new_record.estimated_1rm # 해당 세트의 추정 1RM 포함
            }), 201 # 201 Created 상태 코드 사용
        else:
            # 삽입 실패 응답 (DB 연결 오류, 제약 조건 위반 등 insert_records 내부 오류)
            # insert_records 내부에서 오류 로깅이 이루어져야 함
            print("Database insert failed with no specific exception caught in route.") # 로그 추가
            return jsonify({"message": "Failed to save workout record to database"}), 500 # 500 Internal Server Error

    except Exception as e:
        # 데이터베이스 삽입 과정 중 예상치 못한 예외 발생 시
        print(f"Unexpected error during database insert: {e}") # 서버 로그에 오류 출력
        return jsonify({"message": "An unexpected error occurred while saving to database."}), 500 # 500 Internal Server Error


# GET /workouts/ : 전체 운동 기록 조회
@workout_bp.route('/', methods=['GET'])
def get_workout_records():
    """데이터베이스에 저장된 모든 운동 기록 목록을 조회합니다."""
    # DatabaseManager 인스턴스 가져오기 (current_app.get_db_manager() 호출)
    db_manager: AbstractDatabaseManager = current_app.get_db_manager()

    query = "SELECT * FROM records ORDER BY record_date DESC, sets ASC"
    records_data = db_manager.fetch_records(query)

    # 날짜 객체 JSON 직렬화 문제 고려 (위 GET /workouts/ 와 동일)
    # fetch_records에서 이미 딕셔너리 형태로 반환되지만, 날짜가 date 객체일 수 있으므로
    # JSON 직렬화 가능한 형태로 변환하는 과정이 필요할 수 있습니다.
    # psycopg2의 기본 설정에 따라 date 객체가 문자열로 변환될 수도 있습니다.
    # 만약 date 객체 그대로 반환된다면, 각 레코드의 날짜를 문자열로 변환하는 로직 추가 필요
    # 예: for record in records_data: record['record_date'] = record['record_date'].isoformat() if isinstance(record['record_date'], date) else record['record_date']


    return jsonify(records_data), 200

# GET /workouts/<int:record_id> : 특정 ID의 운동 기록 조회
@workout_bp.route('/<int:record_id>', methods=['GET'])
def get_workout_record(record_id: int):
    """특정 ID의 운동 기록을 조회합니다."""
    # DatabaseManager 인스턴스 가져오기 (current_app.get_db_manager() 호출)
    db_manager: AbstractDatabaseManager = current_app.get_db_manager()

    query = "SELECT * FROM records WHERE id = %s"
    record_data = db_manager.fetch_records(query, (record_id,))

    if record_data:
        # 조회된 결과가 있으면 첫 번째 결과 (하나만 있을 것) 반환
        # 날짜 객체 JSON 직렬화 문제 고려 (위 GET /workouts/ 와 동일)
        # record = record_data[0]
        # record['record_date'] = record['record_date'].isoformat() if isinstance(record['record_date'], date) else record['record_date']
        # return jsonify(record), 200

        # WorkoutRecord 객체로 변환하여 to_dict() 사용하는 것도 방법
        # if record_data:
        #     # DB에서 가져온 딕셔너리로 WorkoutRecord 객체 생성 (필요시)
        #     # record_obj = WorkoutRecord(**record_data[0]) # 컬럼 이름과 생성자 인자 이름이 같아야 함
        #     # return jsonify(record_obj.to_dict()), 200
        # else:
        #     return jsonify({"message": f"Record with id {record_id} not found"}), 404

        # 간단하게 딕셔너리 그대로 반환 (날짜 직렬화는 psycopg2 설정에 따라 다름)
        return jsonify(record_data[0]), 200
    else:
        # 해당 ID의 기록이 없으면 404 Not Found 응답
        return jsonify({"message": f"Record with id {record_id} not found"}), 404
