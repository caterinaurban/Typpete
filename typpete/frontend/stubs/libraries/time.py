from typing import Tuple, Union
# ----- variables and constants -----
accept2dyear = False
altzone = 0
daylight = 0
timezone = 0
tzname = ('', '')  # type: Tuple[str, str]


CLOCK_HIGHRES = 0  # Solaris only
CLOCK_MONOTONIC = 0  # Unix only
CLOCK_MONOTONIC_RAW = 0  # Linux 2.6.28 or later
CLOCK_PROCESS_CPUTIME_ID = 0  # Unix only
CLOCK_REALTIME = 0  # Unix only
CLOCK_THREAD_CPUTIME_ID = 0  # Unix only



class struct_time:
    def __init__(
        self,
        o: Union[
            Tuple[int, int, int, int, int, int, int, int, int],
            Tuple[int, int, int, int, int, int, int, int, int, str],
            Tuple[int, int, int, int, int, int, int, int, int, str, int]
        ],
        _arg: object = None,
    ) -> None: ...

    def __new__(
        cls,
        o: Union[
            Tuple[int, int, int, int, int, int, int, int, int],
            Tuple[int, int, int, int, int, int, int, int, int, str],
            Tuple[int, int, int, int, int, int, int, int, int, str, int]
        ],
        _arg: object = None,
    ) -> struct_time: ...


# ----- functions -----
def asctime(t: Union[Tuple[int, int, int, int, int, int, int, int, int], struct_time] = None) -> str: ...  # return current time
def clock() -> float: ...
def ctime(secs: float = None) -> str: ...  # return current time
def gmtime(secs: float = None) -> struct_time: ...  # return current time
def localtime(secs: float = None) -> struct_time: ...  # return current time
def mktime(t: Union[Tuple[int, int, int, int, int, int, int, int, int], struct_time]) -> float: ...
def sleep(secs: Union[int, float]) -> None: ...
def strftime(format: str,
             t: Union[Tuple[int, int, int, int, int, int, int, int, int], struct_time] = None) -> str: ...  # return current time
def strptime(string: str,
             format: str = None) -> struct_time: ...
def time() -> float: ...


def monotonic() -> float: ...
def perf_counter() -> float: ...
def process_time() -> float: ...
def clock_getres(clk_id: int) -> float: ...  # Unix only
def clock_gettime(clk_id: int) -> float: ...  # Unix only
def clock_settime(clk_id: int, time: float) -> None: ...  # Unix only