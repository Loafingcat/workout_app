# src/workout_importer/abstracts.py
import abc
from typing import List, Dict, Any


# AbstractDatabaseManager 클래스 정의 시 ABC 대신 abc.ABC 사용
class AbstractDatabaseManager(abc.ABC):
    """
    데이터베이스 작업 인터페이스 정의
    """
    @abc.abstractmethod
    def connect(self) -> bool:
        """데이터베이스 연결을 설정 성공 시 True, 실패 시 False를 반환"""
        pass

    @abc.abstractmethod
    def close(self):
        """데이터베이스 연결을 닫기"""
        pass

    @abc.abstractmethod
    def insert_records(self, records_list: List[Any]) -> int:
        """
        데이터베이스에 기록 목록을 삽입.
        삽입된 기록 수 반환.
        """
        pass

    @abc.abstractmethod
    def fetch_records(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        쿼리를 사용하여 데이터베이스에서 기록 가져오기
        딕셔너리 목록을 반환
        """
        pass