"""Per-artifact code generation start/end events independent of bootstrap.

Both native Defs and SDO CLIs use the same timing representation for
Java and Python generation.  Timestamp includes timezone offset and epoch
milliseconds; a monotonic clock measures runtime in seconds and milliseconds.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from time import monotonic_ns
from typing import Iterator


def _event(generator: str, event: str, technology: str,
           artifact: str, elapsed_ns: int | None = None) -> None:
    """Write one flushed machine-readable and human-readable event."""
    now = datetime.now().astimezone()
    duration = (f' durationMs={elapsed_ns // 1_000_000}'
                f' durationSec={elapsed_ns / 1_000_000_000:.3f}'
                if elapsed_ns is not None else '')
    print(f'{generator} {event} artifact={artifact} technology={technology}'
          f' at={now.isoformat(timespec="milliseconds")}'
          f' epochMillis={int(now.timestamp() * 1000)}{duration}', flush=True)


@contextmanager
def generation_log(generator: str, technology: str, repository: Path,
                   artifact: Path) -> Iterator[None]:
    """Log generator start and end even when validation or writing fails.

    Args:
        generator: Displayed generator name.
        technology: Output language (``java`` or ``python``).
        repository: Repository root used to make the artifact label stable.
        artifact: Selected artifact directory.
    Yields:
        Control to the caller while its selected artifact is generated.
    """
    root = repository.resolve()
    selected = artifact.resolve()
    label = str(selected.relative_to(root)) if selected.is_relative_to(root) else str(selected)
    # A native SDO invocation may receive its artifact directory as its
    # repository root. Reconstruct a stable relative label from the nearest
    # Modustro source-repository marker rather than logging artifact= blank.
    if label in ('', '.'):
        owner = next((candidate for candidate in (selected, *selected.parents)
                      if (candidate / 'modustro-source-repository.yml').is_file()), None)
        label = selected.relative_to(owner).as_posix() if owner is not None else selected.name
    start = monotonic_ns()
    _event(generator, 'START', technology, label)
    try:
        yield
    finally:
        _event(generator, 'END', technology, label, monotonic_ns() - start)
