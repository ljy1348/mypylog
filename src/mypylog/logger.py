"""
loguru + rich 조합 로거

문자열이 아닌 객체(dict, list 등)가 들어오면 rich로 예쁘게 출력
"""

import enum
import functools
import sys
import time
from typing import Any, Callable, TypeVar, overload, Protocol, runtime_checkable

from loguru import logger as _loguru_logger
from rich.console import Console
from rich.pretty import Pretty
from rich.panel import Panel


@runtime_checkable
class LogHandler(Protocol):
    def __call__(
        self, level: str, message: str, parts: list[Any], traceback: str | None = None
    ) -> None: ...


# Rich 콘솔 (컬러 출력용)
_console = Console()


class LogLevel(enum.Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def _is_pretty_printable(obj: Any) -> bool:
    """rich로 예쁘게 출력할 수 있는 객체인지 확인"""
    return isinstance(obj, (dict, list, tuple, set, frozenset))


def _format_message(message: Any, *args: Any, **kwargs: Any) -> str:
    """
    메시지 포맷팅
    - 여러 인자가 있으면 각각 처리해서 공백으로 연결
    - 객체: rich Pretty로 변환
    """
    all_parts = [message] + list(args)

    formatted_parts = []
    has_multiline = False

    for part in all_parts:
        if _is_pretty_printable(part):
            pretty = _pretty_repr(part)
            formatted_parts.append(pretty)
            if "\n" in pretty:
                has_multiline = True
        else:
            formatted_parts.append(str(part))

    if has_multiline:
        # 여러 줄이 있으면 각 파트를 줄바꿈으로 연결
        return "\n".join(formatted_parts)
    else:
        # 한 줄이면 공백으로 연결
        return " ".join(formatted_parts)


def _pretty_repr(obj: Any, title: str | None = None) -> str:
    """객체를 rich로 예쁘게 문자열로 변환"""
    from io import StringIO

    string_io = StringIO()
    # force_terminal=False로 ANSI 코드 없이 텍스트만 출력
    console = Console(file=string_io, force_terminal=False, width=100, no_color=True)

    if title:
        console.print(Panel(Pretty(obj, expand_all=True), title=title))
    else:
        console.print(Pretty(obj, expand_all=True))

    return string_io.getvalue().rstrip()


# 레벨 우선순위 매핑
_LEVEL_PRIORITY = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}


class PrettyLogger:
    """loguru + rich 조합 로거 래퍼"""

    def __init__(self, name: str | None = None, level: LogLevel = LogLevel.DEBUG):
        self._name = name  # 로거 이름 (파일 분리용)
        self._logger = _loguru_logger
        self._handlers: list[LogHandler] = []  # 범용 핸들러 목록
        self._min_level_no = _LEVEL_PRIORITY[level.value]
        self._configure_default(level)

    def _configure_default(self, level: LogLevel):
        """기본 로거 설정"""
        self._logger.remove()  # 기본 핸들러 제거
        self._logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=level.value,
            colorize=True,
        )

    def _log(self, level: str, message: Any, *args: Any, **kwargs: Any):
        """로그 출력 (객체면 pretty print)"""
        # 레벨 체크
        msg_level_no = _LEVEL_PRIORITY.get(level.upper(), 0)
        if msg_level_no < self._min_level_no:
            return

        all_parts = [message] + list(args)
        has_pretty_obj = any(_is_pretty_printable(p) for p in all_parts)

        if has_pretty_obj:
            # 객체가 있으면 rich로 직접 출력 (색상 유지)
            self._log_with_rich(level, all_parts)
            # 핸들러로 전송
            self._dispatch_to_handlers(level, all_parts)
        else:
            # 문자열만 있으면 loguru로 출력 (콘솔)
            formatted = " ".join(str(p) for p in all_parts)
            getattr(self._logger.opt(depth=2), level)(formatted)
            # 핸들러로 전송
            self._dispatch_to_handlers(level, all_parts)

    def _dispatch_to_handlers(
        self, level: str, parts: list[Any], exception_traceback: str | None = None
    ):
        """등록된 모든 핸들러에게 로그 전송"""
        if not self._handlers:
            return

        from datetime import datetime
        from io import StringIO

        # 타임스탬프
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 메시지 조합 (공통 포맷팅)
        formatted_parts = []
        for part in parts:
            if _is_pretty_printable(part):
                # 객체는 pretty format으로
                string_io = StringIO()
                console = Console(
                    file=string_io, force_terminal=False, width=100, no_color=True
                )
                console.print(Pretty(part, expand_all=True))
                formatted_parts.append("\n" + string_io.getvalue().rstrip())
            else:
                formatted_parts.append(str(part))

        message_body = " ".join(formatted_parts)

        if exception_traceback:
            message_body += f"\n{exception_traceback}"

        full_message = f"{now} | {level.upper():<8} | {message_body}\n"

        # 모든 핸들러 호출
        for handler in self._handlers:
            try:
                handler(level, full_message, parts, exception_traceback)
            except Exception:
                pass  # 핸들러 실행 중 에러 무시

    def _log_with_rich(self, level: str, parts: list[Any]):
        """rich로 직접 출력 (색상 유지)"""
        from datetime import datetime
        from rich.text import Text

        # 레벨별 색상
        level_colors = {
            "debug": "dim",
            "info": "green",
            "warning": "yellow",
            "error": "red",
            "critical": "bold red",
        }

        # 타임스탬프 출력
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level_color = level_colors.get(level, "white")

        header = Text()
        header.append(now, style="green")
        header.append(" | ", style="dim")
        header.append(f"{level.upper():<8}", style=level_color)
        header.append(" | ", style="dim")

        _console.print(header, end="")

        # 각 파트 출력
        for i, part in enumerate(parts):
            if i > 0:
                _console.print(" ", end="")

            if _is_pretty_printable(part):
                _console.print()  # 줄바꿈
                _console.print(Pretty(part, expand_all=True))
            else:
                _console.print(str(part), end="")

        # rich는 exception 출력 시 별도 처리하므로 여기서는 줄바꿈만
        _console.print()

    def debug(self, message: Any, *args: Any, **kwargs: Any):
        self._log("debug", message, *args, **kwargs)

    def info(self, message: Any, *args: Any, **kwargs: Any):
        self._log("info", message, *args, **kwargs)

    def warning(self, message: Any, *args: Any, **kwargs: Any):
        self._log("warning", message, *args, **kwargs)

    def error(self, message: Any, *args: Any, **kwargs: Any):
        self._log("error", message, *args, **kwargs)

    def critical(self, message: Any, *args: Any, **kwargs: Any):
        self._log("critical", message, *args, **kwargs)

    def exception(self, message: Any, *args: Any, **kwargs: Any):
        """예외 정보와 함께 에러 로그"""
        import traceback

        formatted = _format_message(message, *args, **kwargs)
        self._logger.opt(depth=1, exception=True).error(formatted)

        # 핸들러에도 전송 (Traceback 포함)
        tb = traceback.format_exc()
        self._dispatch_to_handlers("error", [formatted], exception_traceback=tb)

    def add(self, *args, **kwargs):
        """loguru의 add 메서드 위임 (파일 로깅 등)"""
        return self._logger.add(*args, **kwargs)

    def add_handler(self, handler: LogHandler):
        """범용 로그 핸들러 추가"""
        self._handlers.append(handler)

    def add_file(
        self,
        path: str,
        rotation: str | None = None,
        retention: str | None = None,
        **kwargs,
    ):
        """
        파일 로깅 추가 (pretty print 포함)

        Args:
            path: 로그 파일 경로
            rotation: 로테이션 설정 (예: "1 day", "10 MB") - 현재 미지원
            retention: 보관 기간 (예: "7 days") - 현재 미지원

        Note:
            각 로거 인스턴스는 자신의 파일에만 로그를 저장합니다.
        """

        def file_handler(
            level: str, message: str, parts: list[Any], traceback: str | None = None
        ):
            try:
                with open(path, "a", encoding="utf-8") as f:
                    f.write(message)
            except Exception:
                pass

        self.add_handler(file_handler)

    def remove(self, handler_id: int | None = None):
        """loguru의 remove 메서드 위임"""
        return self._logger.remove(handler_id)

    def bind(self, **kwargs):
        """loguru의 bind 메서드 위임"""
        return self._logger.bind(**kwargs)

    # JSON 전용 메서드
    def json(self, obj: Any, title: str | None = None, level: str = "info"):
        """JSON/객체를 예쁘게 출력 (명시적, 색상 포함)"""
        # 레벨 체크
        msg_level_no = _LEVEL_PRIORITY.get(level.upper(), 0)
        if msg_level_no < self._min_level_no:
            return

        from datetime import datetime
        from rich.text import Text

        level_colors = {
            "debug": "dim",
            "info": "green",
            "warning": "yellow",
            "error": "red",
            "critical": "bold red",
        }

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level_color = level_colors.get(level, "white")

        header = Text()
        header.append(now, style="green")
        header.append(" | ", style="dim")
        header.append(f"{level.upper():<8}", style=level_color)
        header.append(" | ", style="dim")

        _console.print(header)

        if title:
            _console.print(
                Panel(Pretty(obj, expand_all=True), title=title, expand=False)
            )
        else:
            _console.print(Pretty(obj, expand_all=True))

        # 핸들러로 전송
        self._dispatch_to_handlers(level, [obj] if not title else [f"[{title}]", obj])

    # rich 콘솔 직접 접근
    @property
    def console(self) -> Console:
        """rich Console 객체 직접 접근"""
        return _console


# 기본 로거 인스턴스
logger = PrettyLogger()

# 이름별 로거 인스턴스 저장소
_loggers: dict[str, PrettyLogger] = {}


def get_logger(
    name: str | None = None, level: LogLevel = LogLevel.DEBUG
) -> PrettyLogger:
    """
    로거 인스턴스 반환

    이름이 지정되면 해당 이름의 독립된 로거를 생성/반환합니다.
    같은 이름으로 호출하면 같은 인스턴스를 반환합니다.

    Args:
        name: 로거 이름. None이면 기본 로거 반환.

    Returns:
        PrettyLogger 인스턴스

    Example:
        # 기본 로거
        logger = get_logger()

        # 파일별 독립 로거
        server_logger = get_logger("server")
        server_logger.add_file("server.log")

        app_logger = get_logger("app")
        app_logger.add_file("app.log")
    """
    if name is None:
        return logger

    if name not in _loggers:
        _loggers[name] = PrettyLogger(name=name, level=level)

    return _loggers[name]


F = TypeVar("F", bound=Callable[..., Any])


@overload
def log_execution(_func: F) -> F: ...


@overload
def log_execution(*, log: PrettyLogger | None = None) -> Callable[[F], F]: ...


def log_execution(
    _func: F | None = None, *, log: PrettyLogger | None = None
) -> F | Callable[[F], F]:
    """
    함수 실행 전후로 로그를 남기는 데코레이터

    사용법:
        @log_execution
        def my_func(): ...

        @log_execution(log=logger)
        def my_func(): ...

    Args:
        log: 사용할 로거 인스턴스 (기본: 전역 logger)
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            _logger = log if log else logger
            func_name = func.__name__

            # 입력값 로깅 (너무 길면 자름)
            args_repr = ", ".join(repr(a)[:50] for a in args)
            kwargs_repr = ", ".join(f"{k}={v!r}"[:50] for k, v in kwargs.items())
            signature = ", ".join(filter(None, [args_repr, kwargs_repr]))

            _logger.debug(f"[CALL] {func_name}({signature[:200]})")

            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - start_time

                # 결과값 로깅
                result_repr = repr(result)[:200]
                _logger.debug(f"[RETURN] {func_name} -> {result_repr} ({elapsed:.4f}s)")
                return result

            except Exception as e:
                elapsed = time.perf_counter() - start_time

                # 중복 로깅 방지: 하위 데코레이터에서 이미 로깅했다면 건너뜀
                if not getattr(e, "_logged_by_mypylog", False):
                    _logger.exception(
                        f"[ERROR] {func_name} raised {type(e).__name__}: {e} ({elapsed:.4f}s)"
                    )
                    # 로깅 처리 완료 표시 (속성 추가)
                    try:
                        setattr(e, "_logged_by_mypylog", True)
                    except AttributeError:
                        # 내장 타입 등 속성 추가가 불가능한 경우 무시 (드문 케이스)
                        pass

                raise

        return wrapper  # type: ignore

    # @log_execution 또는 @log_execution() 둘 다 지원
    if _func is not None:
        return decorator(_func)
    return decorator
