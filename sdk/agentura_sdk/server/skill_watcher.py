"""File watcher for skills/ and agency/ directories — invalidates caches on change."""

import logging
import os
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)

_DEBOUNCE_MS = int(os.environ.get("SKILL_WATCH_DEBOUNCE_MS", "500"))


class _DebouncedHandler(FileSystemEventHandler):
    """Triggers a callback after a debounce window, coalescing rapid changes."""

    def __init__(self, callback: callable, debounce_s: float, watch_extensions: set[str]):
        super().__init__()
        self._callback = callback
        self._debounce_s = debounce_s
        self._extensions = watch_extensions
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def _matches(self, path: str) -> bool:
        return Path(path).suffix in self._extensions

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        src = getattr(event, "src_path", "")
        if not self._matches(src):
            return
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self._debounce_s, self._fire, args=(src,))
            self._timer.daemon = True
            self._timer.start()

    def _fire(self, path: str) -> None:
        logger.info("File change detected: %s — running callback", path)
        try:
            self._callback(path)
        except Exception:
            logger.exception("Watcher callback failed for %s", path)


def start_skill_watcher(skills_dir: Path, on_change: callable) -> Observer | None:
    """Watch skills_dir for .md/.yaml changes; call on_change(path) with debounce."""
    if not skills_dir.exists():
        logger.warning("Skills dir %s does not exist — skipping watcher", skills_dir)
        return None

    handler = _DebouncedHandler(
        callback=on_change,
        debounce_s=_DEBOUNCE_MS / 1000.0,
        watch_extensions={".md", ".yaml", ".yml"},
    )
    observer = Observer()
    observer.schedule(handler, str(skills_dir), recursive=True)
    observer.daemon = True
    observer.start()
    logger.info("Skill watcher started on %s (debounce=%dms)", skills_dir, _DEBOUNCE_MS)
    return observer


def start_agency_watcher(agency_dir: Path, on_change: callable) -> Observer | None:
    """Watch agency_dir for agent.yaml/SOUL.md changes; call on_change(path) with debounce."""
    if not agency_dir.exists():
        logger.warning("Agency dir %s does not exist — skipping watcher", agency_dir)
        return None

    handler = _DebouncedHandler(
        callback=on_change,
        debounce_s=2.0,  # agents need longer debounce (multi-file writes)
        watch_extensions={".yaml", ".yml", ".md"},
    )
    observer = Observer()
    observer.schedule(handler, str(agency_dir), recursive=True)
    observer.daemon = True
    observer.start()
    logger.info("Agency watcher started on %s (debounce=2000ms)", agency_dir)
    return observer
