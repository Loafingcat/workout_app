# src/workout_importer/models.py
from datetime import date
from typing import Optional, Dict, Any

# 1RM 추정 공식 (예: Epley) - 정수형 1RM 반환
def estimate_1rm_epley(weight: Optional[int], reps: Optional[int]) -> Optional[int]:
    """Epley 공식을 사용하여 추정 1RM을 계산하고 정수형으로 반환합니다."""
    # 중량이나 횟수가 유효하지 않으면 None 반환
    if weight is None or reps is None or weight <= 0 or reps < 0:
        return None
    # Epley 공식 계산 후 정수로 반올림
    estimated_1rm = round(weight * (1 + reps / 30))
    return int(estimated_1rm)

class WorkoutRecord:
    """하나의 운동 세트 기록을 나타냅니다."""
    def __init__(self,
                 record_date: date,
                 exercise_type: str,
                 weight: Optional[int],
                 reps: Optional[int],
                 sets: Optional[int],
                 estimated_1rm: Optional[int] = None):
        self.record_date = record_date
        self.exercise_type = exercise_type
        self.weight = weight
        self.reps = reps
        self.sets = sets
        # estimated_1rm이 None이면 자동으로 계산하여 할당
        self.estimated_1rm = estimated_1rm if estimated_1rm is not None else estimate_1rm_epley(self.weight, self.reps)

    def __repr__(self) -> str:
        # 객체를 문자열로 표현할 때 사용
        return (f"WorkoutRecord(date={self.record_date}, exercise='{self.exercise_type}', "
                f"weight={self.weight}, reps={self.reps}, sets={self.sets}, 1RM={self.estimated_1rm})")

    def to_dict(self) -> Dict[str, Any]:
        """기록을 딕셔너리 형태로 변환합니다."""
        return {
            "record_date": self.record_date,
            "exercise_type": self.exercise_type,
            "weight": self.weight,
            "reps": self.reps,
            "sets": self.sets,
            "estimated_1rm": self.estimated_1rm
        }

    def to_tuple(self) -> tuple:
        """데이터베이스 삽입을 위해 기록을 튜플 형태로 변환합니다."""
        return (self.record_date, self.exercise_type, self.weight, self.reps, self.sets, self.estimated_1rm)