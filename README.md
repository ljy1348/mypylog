# mypylog

**loguru + rich 조합 Python 로거** - 객체 자동 pretty print 지원

## 설치

```bash
pip install git+https://github.com/ljy1348/mypylog.git
```

또는 `pyproject.toml`에 추가:

```toml
[project]
dependencies = [
    "mypylog @ git+https://github.com/ljy1348/mypylog.git",
]
```

## 사용법

### 기본 로깅

```python
from mypylog import logger

logger.info("일반 메시지")
logger.debug("디버그 메시지")
logger.warning("경고 메시지")
logger.error("에러 메시지")
```

### 객체 자동 pretty print

```python
data = {
    "name": "홍길동",
    "age": 30,
    "skills": ["Python", "JavaScript", "Go"],
}

# 객체만 전달하면 자동으로 여러 줄로 예쁘게 출력
logger.info(data)

# 여러 인자 혼합도 가능
logger.info("사용자:", data, "완료!")
```

### JSON 명시적 출력 (제목 추가)

```python
logger.json(data, title="사용자 데이터")
```

### 파일 로깅

```python
# 파일에 로그 저장 (pretty print 포함)
logger.add_file("app.log")
```

### 범용 핸들러 (HTTP 전송 등)

`add_handler(callback)`를 사용하여 로그를 원하는 곳으로 전송할 수 있습니다.

```python
import requests

def http_handler(level, message, parts, traceback=None):
    payload = {
        "level": level,
        "message": message, # pretty print된 최종 문자열
        "data": [str(p) for p in parts] # 원본 데이터
    }
    # requests.post("http://...", json=payload)
    print(f"[전송] {payload}")

logger.add_handler(http_handler)
```

### 여러 로거 인스턴스 (파일 분리)

```python
from mypylog import get_logger

# 서버 로그용 로거
server_logger = get_logger("server")
server_logger.add_file("server.log")
server_logger.info("서버 시작")  # server.log에만 저장

# 앱 로그용 로거  
app_logger = get_logger("app")
app_logger.add_file("app.log")
app_logger.info("앱 로직 실행")  # app.log에만 저장
```

### 함수 실행 로깅 데코레이터

```python
from mypylog import log_execution, logger

@log_execution
def my_func(x, y):
    return x + y

# 특정 로거 지정
@log_execution(log=logger)
def my_func(x, y):
    return x + y
```

출력 예시:
```
2026-01-29 15:00:00 | DEBUG | [CALL] my_func(1, 2)
2026-01-29 15:00:00 | DEBUG | [RETURN] my_func -> 3 (0.0001s)
```

## 특징

- ✅ **loguru 기반** - 컬러 출력, 간편한 설정
- ✅ **rich 통합** - dict, list 등 객체 자동 pretty print
- ✅ **여러 인자 지원** - `logger.info("text", obj, "more")` 형태 사용 가능
- ✅ **파일 저장** - 콘솔과 동일한 pretty format으로 파일에도 저장
- ✅ **여러 로거 인스턴스** - 파일별 로그 분리 가능
- ✅ **함수 실행 로깅** - `@log_execution` 데코레이터