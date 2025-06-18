from flask import Blueprint, request, jsonify, current_app, g
from ..services.workout_service import WorkoutService, ValidationError, DatabaseServiceError 

workout_bp = Blueprint('workout_api', __name__, url_prefix='/workouts')

# POST /workouts/ : 새로운 운동 기록 추가
@workout_bp.route('/', methods=['POST'])
def add_workout_record():
    raw_data = request.get_json()
    db_manager = current_app.get_db_manager()
    workout_service = WorkoutService(db_manager)

    try:
        new_record = workout_service.add_record(raw_data)
        return jsonify({
            "message": "Workout record saved successfully",
            "estimated_1rm_for_set": new_record.estimated_1rm
        }), 201
    
    except Exception as e:
        # 서비스 호출 중 예상치 못한 다른 예외 발생 시
        print(f"Unexpected Error in route (before service handler): {e}")
        return jsonify({"message": "An unexpected error occurred."}), 500


# GET /workouts/ : 전체 운동 기록 조회
@workout_bp.route('/', methods=['GET'])
def get_workout_records():
    db_manager = current_app.get_db_manager()
    workout_service = WorkoutService(db_manager)

    try:
        records_data = workout_service.get_all_records()
        return jsonify(records_data), 200

    except Exception as e:
        # 서비스 호출 중 예상치 못한 다른 예외 발생 시
        print(f"Unexpected Error in route (before service handler): {e}")
        return jsonify({"message": "An unexpected error occurred."}), 500

