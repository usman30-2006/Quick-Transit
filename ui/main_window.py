"""
ui/main_window.py
------------------
The PySide6 user interface: two dropdowns, a "Find Route" button, and an
embedded web view rendering the Folium map.

Design notes:
- A* runs on a QThread (via the RouteWorker class) instead of directly in
  the button's slot. For this small graph it would finish instantly either
  way, but doing it properly means the UI never locks up if the graph grows
  (real GTFS data can have thousands of stops).
- PathfindingError subclasses are caught and shown as a QMessageBox instead
  of crashing or silently failing.
- The map is generated once at startup (no route) and again after each
  successful search (with the highlighted route), then the QWebEngineView
  is reloaded from the same file path.
"""

import os

from PySide6.QtCore import QObject, QThread, Signal, QUrl
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QPushButton,
    QLabel,
    QMessageBox,
)
from PySide6.QtWebEngineWidgets import QWebEngineView

from config import GRAPH, get_stop_names
from pathfinding import find_shortest_path, PathfindingError, RouteResult
from map_manager import generate_route_map


class RouteWorker(QObject):
    """
    Runs A* on a background thread so the GUI never freezes, even if the
    graph grows large. Communicates back to the main thread via signals.
    """
    finished = Signal(object)   # emits a RouteResult on success
    error = Signal(str)         # emits a user-friendly error message on failure

    def __init__(self, start: str, end: str):
        super().__init__()
        self.start = start
        self.end = end

    def run(self):
        try:
            result: RouteResult = find_shortest_path(GRAPH, self.start, self.end)
            self.finished.emit(result)
        except PathfindingError as exc:
            self.error.emit(str(exc))
        except Exception as exc:  # noqa: BLE001 - last-resort safety net for the worker thread
            self.error.emit(f"Unexpected error while finding route: {exc}")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bus Route Simulator")
        self.resize(1000, 700)

        self._thread: QThread | None = None
        self._worker: RouteWorker | None = None

        self._build_ui()
        self._load_initial_map()

    # ------------------------------------------------------------------ UI

    def _build_ui(self) -> None:
        stop_names = get_stop_names()

        self.start_combo = QComboBox()
        self.start_combo.addItems(stop_names)

        self.end_combo = QComboBox()
        self.end_combo.addItems(stop_names)
        # Default destination to a different stop than the start, if possible.
        if len(stop_names) > 1:
            self.end_combo.setCurrentIndex(1)

        self.find_button = QPushButton("Find Route")
        self.find_button.clicked.connect(self._on_find_route_clicked)

        self.status_label = QLabel("Select a start and destination, then click Find Route.")
        self.status_label.setWordWrap(True)

        self.map_view = QWebEngineView()

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Start:"))
        controls_layout.addWidget(self.start_combo)
        controls_layout.addWidget(QLabel("Destination:"))
        controls_layout.addWidget(self.end_combo)
        controls_layout.addWidget(self.find_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(controls_layout)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.map_view, stretch=1)

        self.setLayout(main_layout)

    def _load_initial_map(self) -> None:
        """Show the bare network (no route highlighted) on startup."""
        path = generate_route_map(route=None)
        self._reload_map_view(path)

    def _reload_map_view(self, path: str) -> None:
        self.map_view.load(QUrl.fromLocalFile(os.path.abspath(path)))

    # ------------------------------------------------------------ Actions

    def _on_find_route_clicked(self) -> None:
        start = self.start_combo.currentText()
        end = self.end_combo.currentText()

        self.find_button.setEnabled(False)
        self.status_label.setText(f"Finding route from {start} to {end}...")

        # Set up the worker + thread. Keep references on self so they
        # aren't garbage-collected mid-flight.
        self._thread = QThread()
        self._worker = RouteWorker(start, end)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_route_found)
        self._worker.error.connect(self._on_route_error)

        # Clean up the thread once the worker signals completion either way.
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_thread)

        self._thread.start()

    def _on_route_found(self, result: RouteResult) -> None:
        path = generate_route_map(route=result)
        self._reload_map_view(path)

        route_str = " → ".join(result.path)
        self.status_label.setText(
            f"Route: {result.num_stops} stops, {result.total_distance_km} km\n{route_str}"
        )
        self.find_button.setEnabled(True)

    def _on_route_error(self, message: str) -> None:
        QMessageBox.warning(self, "Route Not Found", message)
        self.status_label.setText("Select a start and destination, then click Find Route.")
        self.find_button.setEnabled(True)

    def _cleanup_thread(self) -> None:
        if self._thread is not None:
            self._thread.deleteLater()
            self._thread = None
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None
