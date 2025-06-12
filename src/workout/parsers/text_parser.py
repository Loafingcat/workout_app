# src/workout_importer/parsers/text_parser.py
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

# 상위 패키지에서 추상 클래스 및 모델 임포트
from ..abstracts import AbstractWorkoutParser
from ..models import WorkoutRecord, estimate_1rm_epley

# 운동 종목 표준화 매핑: 텍스트 파일의 별칭 -> 표준 이름
EXERCISE_ALIASES = {
    '벤치': '벤치프레스',
    '데드': '데드리프트',
    '스쿼트': '스쿼트',
    # 다른 별칭이 있다면 여기에 추가 (예: '스쾃': '스쿼트')
}

# 데이터베이스에 삽입 가능한 운동 종목 목록 (CHECK 제약 조건과 일치해야 함)
ALLOWED_EXERCISE_TYPES = ['벤치프레스', '데드리프트', '스쿼트']

# 텍스트 파일 라인 파싱을 위한 정규표현식 컴파일
# 날짜 패턴: [YYYY-M-D ...] 형식 (월, 일 한두 자리 허용)
date_pattern = re.compile(r'^\s*\[(\d{4}-\d{1,2}-\d{1,2}).*\]\s*$')
# 중량 * 횟수 패턴: 숫자 * 숫자
weight_reps_pattern = re.compile(r'(\d+)\s*\*\s*(\d+)')

class TextFileWorkoutParser(AbstractWorkoutParser):
    """
    특정 텍스트 파일 형식을 위한 AbstractWorkoutParser의 구체 구현체입니다.
    """
    def __init__(self):
        # 파서 인스턴스 생성 시 필요한 초기화 (현재는 특별히 없음)
        pass

    def standardize_exercise_name(self, potential_exercise: str) -> Optional[str]:
        """정의된 별칭을 기반으로 운동 종목 이름을 표준화합니다."""
        # 앞뒤 공백 제거 후 매핑 딕셔너리에서 찾고, 없으면 None 반환
        return EXERCISE_ALIASES.get(potential_exercise.strip(), None)

    def parse(self, file_path: str) -> List[WorkoutRecord]:
        """
        주어진 텍스트 파일 경로로부터 운동 데이터를 파싱합니다.
        WorkoutRecord 객체 목록을 반환합니다.
        """
        records_list: List[WorkoutRecord] = [] # 반환할 WorkoutRecord 객체 리스트
        current_date = None # 현재 처리 중인 날짜
        current_exercise = None # 현재 처리 중인 운동 종목
        set_count = 0 # 현재 운동 종목/날짜 블록 내의 세트 번호

        try:
            print(f"'{file_path}' 파일 파싱 시작...")
            # 파일을 UTF-8 인코딩으로 읽기 모드로 엽니다.
            with open(file_path, 'r', encoding='utf-8') as f:
                # 파일의 각 줄을 순회합니다.
                for line in f:
                    line = line.strip() # 줄의 앞뒤 공백 제거

                    if not line: # 빈 줄이면 건너뜁니다.
                        continue

                    # --- 라인 유형 식별 및 파싱 ---

                    # 1. [YYYY-MM-DD ...] 형식의 날짜 라인 파싱 시도
                    date_match = date_pattern.match(line)
                    if date_match:
                        date_str = date_match.group(1) # 정규식 그룹 1 (날짜 문자열) 추출
                        try:
                            # 날짜 문자열을 date 객체로 변환
                            current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                            current_exercise = None # 새로운 날짜 시작 시 운동 종목 초기화
                            set_count = 0 # 새로운 날짜 시작 시 세트 번호 초기화
                            print(f"--- 날짜 감지: {current_date} ---") # 파싱 진행 확인용 출력
                        except ValueError:
                             print(f"경고: 날짜 파싱 오류 - '{line}' (올바른 날짜 형식이 아닙니다)")
                             current_date = None # 날짜 파싱 실패 시 해당 날짜 블록 무시
                        continue # 이 줄 처리가 끝났으므로 다음 줄로 이동

                    # 2. 중량 * 횟수 라인 파싱 시도
                    weight_reps_match = weight_reps_pattern.match(line)
                    if weight_reps_match:
                        # 중량 * 횟수 라인은 날짜와 운동 종목이 모두 감지되었을 때만 유효
                        if current_date and current_exercise:
                            try:
                                weight = int(weight_reps_match.group(1)) # 정규식 그룹 1 (중량) 추출
                                reps = int(weight_reps_match.group(2)) # 정규식 그룹 2 (횟수) 추출
                                set_count += 1 # 세트 번호 증가

                                # WorkoutRecord 객체 생성 시 1RM 자동 계산
                                record = WorkoutRecord(
                                    record_date=current_date,
                                    exercise_type=current_exercise, # 이미 표준화된 운동 종목 사용
                                    weight=weight,
                                    reps=reps,
                                    sets=set_count
                                )
                                # print(f"  세트 기록 추출: {record}") # 추출 확인용 출력 (디버깅 시 유용)
                                records_list.append(record) # 추출된 레코드를 목록에 추가

                            except ValueError:
                                 print(f"경고: 중량/횟수 파싱 오류 - '{line}' (유효한 숫자가 아닙니다)")
                            except Exception as e:
                                 print(f"경고: 레코드 처리 중 알 수 없는 오류 발생 - {e}, 라인: '{line}'")
                            continue # 이 줄 처리가 끝났으므로 다음 줄로 이동

                        else:
                             # 날짜나 운동 종목 감지 전에 중량*횟수 라인이 나온 경우 (파일 형식 오류)
                             print(f"경고: 날짜 또는 운동 종목 감지 전에 중량*횟수 라인 발견 - '{line}'")
                             continue # 이 줄 처리가 끝났으므로 다음 줄로 이동

                    # 3. 날짜 라인도, 중량*횟수 라인도 아닌 경우 -> 운동 종목 라인 또는 알 수 없는 라인
                    # 날짜가 이미 감지된 상태에서만 운동 종목 라인으로 간주 시도
                    if current_date:
                         potential_exercise = line # 파싱될 가능성이 있는 운동 종목 이름

                         # 운동 종목 표준화 메서드 호출
                         standardized_exercise = self.standardize_exercise_name(potential_exercise)

                         # 표준화된 운동 종목이 데이터베이스 허용 목록에 있는지 최종 확인
                         if standardized_exercise in ALLOWED_EXERCISE_TYPES:
                             current_exercise = standardized_exercise # 유효한 운동 종목으로 설정
                             set_count = 0 # 새로운 운동 종목 시작 시 세트 번호 초기화
                             print(f"운동 종목 감지: {current_exercise}") # 파싱 진행 확인용 출력
                             continue # 이 줄 처리가 끝났으므로 다음 줄로 이동 (성공적으로 운동 종목 감지)
                         else:
                             # 유효하지 않거나 예상치 못한 라인이라면 경고 출력 및 무시
                             print(f"경고: 처리되지 않거나 유효하지 않은 라인 발견 - '{line}' (날짜: {current_date}, 현재 운동: {current_exercise if current_exercise else '없음'})")
                             # current_exercise는 변경되지 않고, 다음 중량*횟수 라인은 처리되지 않음
                             continue # 이 줄 처리가 끝났으므로 다음 줄로 이동
                    else:
                         # 날짜 감지 전에 나온 알 수 없는 라인
                         print(f"경고: 날짜 감지 전에 알 수 없는 라인 발견 - '{line}'")
                         continue # 이 줄 처리가 끝났으므로 다음 줄로 이동

            print(f"파일 파싱 완료. 총 {len(records_list)}개의 레코드 추출.")
            return records_list # 파싱된 레코드 목록 반환

        except FileNotFoundError:
            print(f"오류: 파일을 찾을 수 없습니다 - {file_path}")
            return [] # 파일을 찾지 못하면 빈 목록 반환
        except Exception as e:
            print(f"파일 파싱 중 알 수 없는 오류 발생: {e}")
            return [] # 파싱 중 오류 발생 시 빈 목록 반환