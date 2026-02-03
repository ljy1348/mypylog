# Changelog

## [0.3.0] - 2026-02-03

### Added
- **범용 핸들러 지원**: `add_handler(callback)` 메서드를 통해 사용자 정의 핸들러(HTTP, MQ 등)를 등록할 수 있습니다.
- **LogHandler 프로토콜**: 핸들러 함수가 따라야 할 서명을 `typing.Protocol`로 정의했습니다.
- **구조화된 데이터 전달**: 핸들러에게 포맷팅된 메시지뿐만 아니라 원본 객체(`parts`)를 그대로 전달하여 JSON 직렬화 등에 활용할 수 있습니다.

### Changed
- **내부 구조 개선**: `add_file` 메서드가 내부적으로 `add_handler`를 사용하도록 리팩토링되었습니다.
- **로깅 디스패치 로직**: `_log_to_file` 메서드가 제거되고 `_dispatch_to_handlers`로 대체되었습니다.

## [0.2.2] - 2026-02-02 (Hotfix)

### Fixed
- **중첩 데코레이터 예외 로깅 수정**: `log_execution` 데코레이터 중첩 사용 시 예외 로그가 중복 출력되는 문제를 해결했습니다.
- **Exception 로깅 누락 수정**: `logger.exception` 사용 시 파일에 저장되지 않던 문제를 수정했습니다.

## [0.2.1] - 2026-01-29

### Added
- **JSON 메서드**: `logger.json(obj)` 메서드 추가로 명시적인 JSON/객체 출력을 지원합니다.
- **log_execution 데코레이터**: 함수 실행 시간 및 입출력 로깅을 위한 데코레이터를 추가했습니다.

## [0.1.0] - 2026-01-29

### Initial Release
- **PrettyLogger**: `loguru`와 `rich`를 결합하여 객체 자동 pretty print를 지원하는 로거 구현.
- **파일 로깅**: 콘솔과 동일한 포맷으로 파일에 저장하는 기능 지원.
