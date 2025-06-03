from typing import Callable, Generic, TypedDict, TypeVar

from Crypto.PublicKey.ECC import EccKey
from typing_extensions import NotRequired, Unpack

T = TypeVar("T")

class RequestParams(TypedDict, Generic[T]):
    kdf: Callable[[bytes | bytearray | memoryview], T]
    static_priv: NotRequired[EccKey]
    static_pub: NotRequired[EccKey]
    eph_priv: NotRequired[EccKey]
    eph_pub: NotRequired[EccKey]

def import_x25519_public_key(encoded: bytes) -> EccKey: ...
def import_x25519_private_key(encoded: bytes) -> EccKey: ...
def import_x448_public_key(encoded: bytes) -> EccKey: ...
def import_x448_private_key(encoded: bytes) -> EccKey: ...
def key_agreement(**kwargs: Unpack[RequestParams[T]]) -> T: ...
