from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import psutil

GIB = 1024 ** 3


def bytes_to_gib(value: int | None) -> float | None:
    if value is None:
        return None
    return round(value / GIB, 4)


def parse_memory_events(text: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 2:
            try:
                out[parts[0]] = int(parts[1])
            except ValueError:
                continue
    return out


def _read_int(path: Path) -> int | None:
    try:
        raw = path.read_text().strip()
    except OSError:
        return None
    if raw == "max":
        return None
    try:
        return int(raw)
    except ValueError:
        return None


@dataclass(frozen=True)
class MemorySnapshot:
    process_rss_bytes: int
    system_available_bytes: int
    system_total_bytes: int
    cgroup_current_bytes: int | None
    cgroup_peak_bytes: int | None
    cgroup_max_bytes: int | None
    cgroup_events: dict[str, int]

    @property
    def system_available_gib(self) -> float:
        return float(bytes_to_gib(self.system_available_bytes) or 0.0)

    def to_dict(self) -> dict[str, object]:
        raw = asdict(self)
        raw.update({
            "process_rss_gib": bytes_to_gib(self.process_rss_bytes),
            "system_available_gib": bytes_to_gib(self.system_available_bytes),
            "system_total_gib": bytes_to_gib(self.system_total_bytes),
            "cgroup_current_gib": bytes_to_gib(self.cgroup_current_bytes),
            "cgroup_peak_gib": bytes_to_gib(self.cgroup_peak_bytes),
            "cgroup_max_gib": bytes_to_gib(self.cgroup_max_bytes),
        })
        return raw


def capture_memory_snapshot(cgroup_root: Path = Path("/sys/fs/cgroup")) -> MemorySnapshot:
    vm = psutil.virtual_memory()
    proc = psutil.Process()
    events_path = cgroup_root / "memory.events"
    try:
        events = parse_memory_events(events_path.read_text())
    except OSError:
        events = {}
    return MemorySnapshot(
        process_rss_bytes=proc.memory_info().rss,
        system_available_bytes=int(vm.available),
        system_total_bytes=int(vm.total),
        cgroup_current_bytes=_read_int(cgroup_root / "memory.current"),
        cgroup_peak_bytes=_read_int(cgroup_root / "memory.peak"),
        cgroup_max_bytes=_read_int(cgroup_root / "memory.max"),
        cgroup_events=events,
    )
