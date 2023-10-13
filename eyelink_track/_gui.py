from pathlib import Path

from pyglet.canvas import Display
from qtpy.QtCore import QRegExp, Slot
from qtpy.QtGui import QRegExpValidator
from qtpy.QtWidgets import (
    QAction,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStatusBar,
    QStyle,
    QToolBar,
    QWidget,
)
from screeninfo import get_monitors


class GUI(QMainWindow):
    """Main window of the GUI."""

    def __init__(self):
        super().__init__()
        self.setCentralWidget(CentralWidget())
        # tool bar
        start = QAction(
            self.style().standardIcon(QStyle.SP_MediaPlay),
            "",
            self,
            objectName="start",
        )
        start.triggered.connect(self.start)
        stop = QAction(
            self.style().standardIcon(QStyle.SP_MediaStop),
            "",
            self,
            objectName="stop",
        )
        stop.triggered.connect(self.stop)
        stop.setEnabled(False)
        toolbar = QToolBar()
        toolbar.addAction(start)
        toolbar.addAction(stop)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        # status bar
        status = QStatusBar()
        status.showMessage("[Not recording]")
        self.setStatusBar(status)
        # render
        self.show()

    @Slot()
    def start(self):
        """Start the EyeTracker calibration and recording."""
        self.statusBar().showMessage("[Recording..]")
        self.findChildren(QAction, name="start")[0].setEnabled(False)
        self.findChildren(QAction, name="stop")[0].setEnabled(True)
        # disable widgets from the central widget
        for widget_type in (QLineEdit, QPushButton, QComboBoxMonitor):
            for widget in self.centralWidget().findChildren(widget_type):
                widget.setEnabled(False)

    @Slot()
    def stop(self):
        """Stop the EyeTracker calibration and recording."""
        self.statusBar().showMessage("[Not recording]")
        self.findChildren(QAction, name="start")[0].setEnabled(True)
        self.findChildren(QAction, name="stop")[0].setEnabled(False)
        # enable widgets from the central widget
        for widget_type in (QLineEdit, QPushButton, QComboBoxMonitor):
            for widget in self.centralWidget().findChildren(widget_type):
                widget.setEnabled(True)


class CentralWidget(QWidget):
    """Main widget arranging the settings."""

    def __init__(self):
        super().__init__()
        self.setObjectName("central_widget")

        # create central widget layout
        layout = QFormLayout(self)
        layout.addRow("Directory:", DirectoryDialog())
        layout.addRow("File name:", LineEditFname())
        layout.addRow("Monitor:", QComboBoxMonitor())


class DirectoryDialog(QWidget):
    """QFileDialog and QLineEdit to select the recording directory."""

    def __init__(self):
        super().__init__()
        self.line = QLineEdit()
        self.line.setText(str(Path.home()))
        self.button = QPushButton()
        self.button.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.button.clicked.connect(self.browse_path)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.line, stretch=1)
        layout.addWidget(self.button)

    @Slot()
    def browse_path(self):
        """Slot executed when the 'browse' button is pressed."""
        path = QFileDialog.getExistingDirectory(
            self, "Select directory", str(Path.home()), QFileDialog.ShowDirsOnly
        )
        if path:
            self.line.setText(path)


class LineEditFname(QLineEdit):
    """QLineEdit validated for EyeLink file names."""

    def __init__(self):
        super().__init__()
        self.rx = QRegExp(r"^[a-zA-Z0-9]{1,8}$")
        self.validator = QRegExpValidator(self.rx)
        self.setValidator(self.validator)


class QComboBoxMonitor(QComboBox):
    """QComboBox listing the available monitors."""

    def __init__(self):
        super().__init__()
        self.screens = Display().get_screens()
        self.monitors = get_monitors()
        # map monitors by geometry to pyglet
        self.monitors_matching = sorted(
            [(elt.x, elt.y, elt.height, elt.width) for elt in self.screens]
        ) == sorted([(elt.x, elt.y, elt.height, elt.width) for elt in self.monitors])
        if self.monitors_matching:
            idx = 0
            for k, elt in enumerate(self.monitors):
                self.addItem(f"{elt.name} (primary)" if elt.is_primary else elt.name)
                if k != 0 and idx == 0 and not elt.is_primary:
                    idx = k
            self.setCurrentIndex(idx)
        else:
            self.addItems(
                [
                    f"{k}: (x={screen.x}, y={screen.y}, {screen.width}x{screen.height})"
                    for k, screen in enumerate(self.screens)
                ]
            )

    @property
    def monitor(self) -> int:
        """ID of the monitor for pyglet."""
        if self.monitors_matching:
            monitor = self.monitors[self.currentIndex()]
            for k, screen in enumerate(self.screens):
                if all(
                    getattr(screen, elt) == getattr(monitor, elt)
                    for elt in ("x", "y", "height", "width")
                ):
                    idx = k
                    break
        else:
            idx = self.currentIndex()
        return idx
