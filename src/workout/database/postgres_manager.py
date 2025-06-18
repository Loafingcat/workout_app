# src/workout_importer/database/postgres_manager.py
import psycopg2
import os
from typing import List, Dict, Any, Optional
import psycopg2.extensions

# 상위 패키지에서 추상 클래스 및 모델 임포트
from ..abstracts import AbstractDatabaseManager
from ..models import WorkoutRecord

class PostgreSQLDatabaseManager(AbstractDatabaseManager):
    
    def __init__(self, db_params: Dict[str, Any]):
        self.db_params = db_params # 데이터베이스 연결 매개변수 저장
        self._conn: Optional[psycopg2.connection] = None # 연결 객체 (초기 None)
        self._cur: Optional[psycopg2.cursor] = None # 커서 객체 (초기 None)

    def connect(self) -> bool:
        """PostgreSQL 데이터베이스 연결을 설정합니다."""
        # 연결이 없거나 닫혀있으면 새로 연결 시도
        if self._conn is None or self._conn.closed != 0:
            try:
                print("PostgreSQL 데이터베이스 연결 중...")
                self._conn = psycopg2.connect(**self.db_params)
                print("PostgreSQL 데이터베이스 연결 성공.")
                return True # 연결 성공
            except psycopg2.OperationalError as e:
                print(f"PostgreSQL 연결 오류 발생: {e}")
                self._conn = None # 연결 실패 시 객체 초기화
                return False # 연결 실패
            except Exception as e:
                print(f"PostgreSQL 연결 중 알 수 없는 오류 발생: {e}")
                self._conn = None # 연결 실패 시 객체 초기화
                return False # 연결 실패
        else:
            print("기존 PostgreSQL 데이터베이스 연결 재사용.")
            return True # 기존 연결 재사용

    def close(self):
        """PostgreSQL 데이터베이스 커서와 연결을 닫습니다."""
        if self._cur:
            self._cur.close() # 커서 닫기
            self._cur = None
        if self._conn:
            self._conn.close() # 연결 닫기
            self._conn = None
            print("PostgreSQL 데이터베이스 연결 닫힘.")

    def _get_cursor(self) -> Optional[psycopg2.extensions.cursor]:
         """현재 연결로부터 커서를 가져옵니다."""
         # 연결이 활성화되어 있는지 확인
         if self._conn is None or self._conn.closed != 0:
             print("오류: 데이터베이스 연결이 활성화되어 있지 않습니다.")
             return None
         # 새로운 커서 객체 생성 및 반환
         return self._conn.cursor()

    def insert_records(self, records_list: List[WorkoutRecord]) -> int:
        """WorkoutRecord 객체 목록을 PostgreSQL의 'records' 테이블에 삽입"""
        if not records_list: # 삽입할 레코드가 없으면 0 반환
            print("삽입할 레코드가 없습니다.")
            return 0

        # 삽입 전에 데이터베이스 연결 확인/재연결
        if not self.connect():
             print("데이터베이스 연결 실패로 삽입을 진행할 수 없습니다.")
             return 0

        # INSERT SQL 쿼리문
        insert_sql = """
        INSERT INTO records (record_date, exercise_type, weight, reps, sets, estimated_1rm)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cur = None # 커서 객체 초기화
        inserted_count = 0 # 삽입된 레코드 수 초기화
        try:
            cur = self._get_cursor() # 커서 가져오기
            if cur:
                print(f"PostgreSQL에 {len(records_list)}개의 레코드 삽입 중...")
                # WorkoutRecord 객체 리스트를 DB 삽입을 위한 튜플 리스트로 변환
                data_to_insert = [record.to_tuple() for record in records_list]
                # executemany를 사용하여 여러 레코드를 한 번에 효율적으로 삽입
                cur.executemany(insert_sql, data_to_insert)
                self._conn.commit() # 변경사항 커밋 (실제 DB에 반영)
                inserted_count = len(records_list) # 삽입 성공한 레코드 수 (executemany는 성공 시 전체 수를 반환)
                print(f"{inserted_count}개의 레코드 삽입 완료.")
        except psycopg2.Error as e:
            print(f"데이터베이스 삽입 오류 발생: {e}")
            if self._conn:
                self._conn.rollback() # 오류 발생 시 롤백 (변경사항 취소)
                print("PostgreSQL 변경사항 롤백됨.")
            print(f"데이터베이스 오류 상세 정보: {e.pgerror}") # 상세 오류 메시지 출력
        except Exception as e:
            print(f"삽입 중 알 수 없는 오류 발생: {e}")
        finally:
            if cur:
                cur.close() # 커서 닫기
        return inserted_count # 삽입된 레코드 수 반환

    def fetch_records(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """쿼리를 사용하여 PostgreSQL에서 기록을 가져옵니다."""
        # 조회 전에 데이터베이스 연결 확인/재연결
        if not self.connect():
            print("데이터베이스 연결 실패로 조회를 진행할 수 없습니다.")
            return [] # 연결 실패 시 빈 목록 반환

        cur = None # 커서 객체 초기화
        try:
            cur = self._get_cursor() # 커서 가져오기
            if cur:
                cur.execute(query, params) # SQL 쿼리 실행
                # 결과를 딕셔너리 리스트로 변환 (컬럼 이름 포함)
                columns = [desc[0] for desc in cur.description] # 컬럼 이름 가져오기
                results = []
                for row in cur.fetchall(): # 모든 결과 행 가져오기
                    results.append(dict(zip(columns, row))) # 컬럼 이름과 행 데이터를 딕셔너리로 묶어 추가
                print(f"쿼리 결과 {len(results)}개 레코드 조회.")
                return results # 조회된 레코드 목록 반환
        except psycopg2.Error as e:
            print(f"PostgreSQL 조회 오류 발생: {e}")
            print(f"PostgreSQL 오류 상세 정보: {e.pgerror}") # 상세 오류 메시지 출력
        except Exception as e:
            print(f"조회 중 알 수 없는 오류 발생: {e}")
        finally:
            if cur:
                cur.close() # 커서 닫기
            # 연결은 유지
        return []