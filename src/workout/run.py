import os
from src.workout.api.app import create_app

# 이 파일을 직접 실행했을 때 (개발 서버 시작)
if __name__ == '__main__':
    env_config_name = os.environ.get('FLASK_CONFIG', 'development')
    app = create_app(env_config_name)
    app.run(host='0.0.0.0', port=5000)
