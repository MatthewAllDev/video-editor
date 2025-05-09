from dataclasses import dataclass

@dataclass
class Metadata:
    filename: str
    width: int
    height: int
    rotation: int
    duration: int
    codec: str
    fps: float
