from typing import Optional

class Serializable:
    def __init__(self, raw=None):
        pass


class Cerealizable:
    pass


class SCIONPayloadBaseProto(Cerealizable):
    PAYLOAD_TYPE = None


class PacketBase(Serializable):
    def get_payload(self) -> bytes:
        ...

    def set_payload(self, new_payload: SCIONPayloadBaseProto) -> None:
        ...


class PayloadBase(Serializable):  # pragma: no cover
    METADATA_LEN = 0



class L4HeaderBase(Serializable):
    TYPE = None  # type: Optional[int]

    def matches(self, raw: bytes, offset: int) -> bool:
        return True


class PayloadRaw(PayloadBase):  # pragma: no cover
    SNIPPET_LEN = 32