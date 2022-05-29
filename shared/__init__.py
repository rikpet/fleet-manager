from dataclasses import dataclass, field

@dataclass
class Device:
    name: str
    id: str
    cpu_load: float
    memory_usage: float
    ip_addr: str
    containers: list[object] = field(default_factory=list)