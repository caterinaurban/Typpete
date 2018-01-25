

def error(msg: str, a: object = None, b: object = None, c: object = None) -> None: ...

def warning(msg: str, a: object = None, b: object = None, c: object = None) -> None: ...

def debug(msg: str, a: object = None, b: object = None, c: object = None, d: object = None) -> None: ...

def info(msg: str, a: object = None, b: object = None, c: object = None) -> None: ...

def critical(msg: str, a: object = None, b: object = None, c: object = None) -> None: ...


CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
NOTSET = 0