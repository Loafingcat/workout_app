# src/workout_importer/services/workout_service.py

from typing import Dict, Any, List
from datetime import date
# 필요한 클래스 임포트 (workout_routes.py에서 이동)
from ..models import WorkoutRecord
from ..abstracts import AbstractDatabaseManager

# 유효성 검사 관련 상수 (workout_routes.py에서 이동)
ALLOWED_EXERCISE_TYPES = ['벤치프레스', '데드리프트', '스쿼트']

# 서비스 계층에서 발생할 수 있는 커스텀 예외 정의 (선택 사항, 오류 처리를 더 명확하게 함)
class ValidationError(Exception):
    """입력 데이터 유효성 검사 실패 시 발생하는 예외"""
    pass

class DatabaseServiceError(Exception):
    """서비스 계층에서 데이터베이스 관련 오류 발생 시 발생하는 예외"""
    pass


# 운동 기록 관련 비즈니스 로직을 처리하는 서비스 클래스
class WorkoutService:
    def __init__(self, db_manager: AbstractDatabaseManager):
        # 서비스는 데이터베이스 관리자 인스턴스를 의존성으로 주입받습니다.
        self.db_manager = db_manager

    def validate_workout_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """입력 데이터를 검증하고 정제합니다."""
        required_fields = ['exercise_type', 'weight', 'reps', 'sets']
        if not data or not all(field in data for field in required_fields):
            raise ValidationError("Missing required fields")

        exercise_type = data.get('exercise_type')
        weight = data.get('weight')
        reps = data.get('reps')
        sets = data.get('sets')

        # 운동 종목 유효성 검사 및 표준화
        if not isinstance(exercise_type, str):
             raise ValidationError("Invalid data type for exercise_type. Must be a string.")
        exercise_type = exercise_type.strip()
        if exercise_type not in ALLOWED_EXERCISE_TYPES:
             raise ValidationError(f"Invalid exercise type: '{exercise_type}'. Allowed types are: {', '.join(ALLOWED_EXERCISE_TYPES)}")

        # 숫자 타입 변환 및 유효성 검사
        try:
            if weight is None or reps is None or sets is None:
                 raise TypeError("Weight, reps, or sets is None") # 이 경우는 required_fields 체크에서 걸릴 가능성 높음

            numeric_weight = int(weight)
            numeric_reps = int(reps)
            numeric_sets = int(sets)

            if numeric_weight < 0 or numeric_reps < 0 or numeric_sets <= 0:
                 raise ValidationError("Weight, reps must be non-negative, sets must be positive")

        except (ValueError, TypeError) as e:
             raise ValidationError(f"Invalid data type for weight, reps, or sets. Must be integers. Details: {e}")
        except Exception as e:
             raise DatabaseServiceError(f"An unexpected error occurred during validation. Details: {e}") # 예상치 못한 오류는 서비스 오류로 처리

        # 검증된 데이터 반환
        return {
            'exercise_type': exercise_type,
            'weight': numeric_weight,
            'reps': numeric_reps,
            'sets': numeric_sets,
            'record_date': date.today() # 서비스 계층에서 날짜 결정
        }


    def add_record(self, raw_data: Dict[str, Any]) -> WorkoutRecord:
        """새로운 운동 기록을 검증하고 데이터베이스에 저장합니다."""
        try:
            # 1. 데이터 유효성 검사 및 정제
            validated_data = self.validate_workout_data(raw_data)

            # 2. WorkoutRecord 객체 생성
            new_record = WorkoutRecord(
                record_date=validated_data['record_date'],
                exercise_type=validated_data['exercise_type'],
                weight=validated_data['weight'],
                reps=validated_data['reps'],
                sets=validated_data['sets']
            )

            # 3. 데이터베이스에 저장
            records_to_insert: List[WorkoutRecord] = [new_record]
            inserted_count = self.db_manager.insert_records(records_to_insert)

            if inserted_count == 0:
                # insert_records 내부에서 오류 로깅이 되었을 것이므로, 여기서는 서비스 오류 발생
                raise DatabaseServiceError("Failed to save workout record to database")

            # 4. 성공 시 저장된 레코드 객체 반환
            return new_record

        except ValidationError as e:
            # 유효성 검사 오류는 그대로 다시 발생시킵니다.
            raise e
        except Exception as e:
            # 유효성 검사 외 다른 오류는 서비스 오류로 처리
            raise DatabaseServiceError(f"An unexpected error occurred in service layer: {e}")


    def get_all_records(self) -> List[Dict[str, Any]]:
        """데이터베이스에 저장된 모든 운동 기록 목록을 조회합니다."""
        query = "SELECT * FROM records ORDER BY record_date DESC, sets ASC"
        # db_manager.fetch_records 내부에서 오류 처리 및 로깅이 이루어지므로, 여기서는 결과만 반환
        records_data = self.db_manager.fetch_records(query)
        return records_data

