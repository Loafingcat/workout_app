from flask import jsonify, Blueprint, Flask
from ..services.workout_service import ValidationError, DatabaseServiceError

# 오류 핸들러 함수 정의
def handle_validation_error(error):
    """ValidationError 발생 시 처리"""
    print(f"Caught Validation Error in handler: {error}")
    return jsonify({"message": str(error)}), 400

def handle_database_service_error(error):
    """DatabaseServiceError 발생 시 처리"""
    print(f"Caught Database Service Error in handler: {error}")
    return jsonify({"message": str(error)}), 500

def handle_generic_error(error):
    print(f"Caught Generic Error in handler: {error}")
    return jsonify({"message": "An unexpected server error occurred."}), 500


# 오류 핸들러를 블루프린트 또는 앱에 등록하는 함수
def register_api_error_handlers(blueprint_or_app):
    """주어진 블루프린트 또는 앱에 API 관련 오류 핸들러를 등록합니다."""
    blueprint_or_app.register_error_handler(ValidationError, handle_validation_error)
    blueprint_or_app.register_error_handler(DatabaseServiceError, handle_database_service_error)
    blueprint_or_app.register_error_handler(Exception, handle_generic_error) # 전역 핸들러 등록 예시
