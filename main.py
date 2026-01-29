"""mypylog 사용 예시"""

from src.mypylog import get_logger, log_execution

logger = get_logger("test", level="INFO")
# 기본 문자열 로깅
logger.info("일반 메시지입니다")
logger.debug("디버그 메시지")
logger.warning("경고 메시지")
logger.error("에러 메시지")
print("\n" + "=" * 50 + "\n")

# 객체 로깅 - 자동으로 pretty print
data = {
    "name": "홍길동",
    "age": 30,
    "skills": ["Python", "JavaScript", "Go"],
    "projects": {
        "mypylog": {"stars": 100, "status": "active"},
        "other": {"stars": 50, "status": "archived"},
    },
}

logger.info("사용자 정보:")
logger.info(data)

print("\n" + "=" * 50 + "\n")

# 리스트도 예쁘게
items = [
    {"id": 1, "name": "아이템1", "price": 1000},
    {"id": 2, "name": "아이템2", "price": 2000},
    {"id": 3, "name": "아이템3", "price": 3000},
]

logger.info(items)

print("\n" + "=" * 50 + "\n")

# 여러 인자 테스트 - 문자열 + 객체 혼합
logger.info("하하", data, "여러개", "테스트")

print("\n" + "=" * 50 + "\n")

# json 메서드로 명시적 출력 (제목 추가 가능)
logger.json(data, title="사용자 데이터")


@log_execution(log=logger)
def deco_test(msg):
    return msg


deco_test(data)
