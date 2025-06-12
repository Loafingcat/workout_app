# src/workout_importer/abstracts.py
import abc # abc 모듈 임포트
from typing import List, Dict, Any

# AbstractWorkoutParser 클래스 정의 시 ABC 대신 abc.ABC 사용
class AbstractWorkoutParser(abc.ABC):
    """
    운동 데이터 파서의 추상 기본 클래스입니다.
    데이터 소스로부터 운동 데이터를 파싱하는 인터페이스를 정의합니다.
    """
    @abc.abstractmethod
    def parse(self, source: str) -> List[Any]:
        """
        주어진 소스로부터 운동 데이터를 파싱합니다.
        소스는 파일 경로, 문자열 내용 등이 될 수 있습니다.
        파싱된 운동 기록 목록(예: WorkoutRecord 객체 또는 딕셔너리)을 반환합니다.
        """
        pass

# AbstractDatabaseManager 클래스 정의 시 ABC 대신 abc.ABC 사용
class AbstractDatabaseManager(abc.ABC):
    """
    데이터베이스 관리자의 추상 기본 클래스입니다.
    데이터베이스 작업 인터페이스를 정의합니다.
    """
    @abc.abstractmethod
    def connect(self) -> bool:
        """데이터베이스 연결을 설정합니다. 성공 시 True, 실패 시 False를 반환합니다."""
        pass

    @abc.abstractmethod
    def close(self):
        """데이터베이스 연결을 닫습니다."""
        pass

    @abc.abstractmethod
    def insert_records(self, records_list: List[Any]) -> int:
        """
        데이터베이스에 기록 목록을 삽입합니다.
        삽입된 기록 수를 반환합니다.
        """
        pass

    @abc.abstractmethod
    def fetch_records(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        쿼리를 사용하여 데이터베이스에서 기록을 가져옵니다.
        딕셔너리 목록을 반환합니다.
        """
        pass