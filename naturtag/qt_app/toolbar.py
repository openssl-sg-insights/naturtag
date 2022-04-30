from logging import getLogger
from typing import Callable

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QToolBar, QWidget

from naturtag.constants import ASSETS_DIR
from naturtag.qt_app.images import ImageViewer

ICONS_DIR = ASSETS_DIR / 'material_icons'
logger = getLogger(__name__)


class Toolbar(QToolBar):
    def __init__(self, parent: QWidget, viewer: ImageViewer):
        super(Toolbar, self).__init__(parent)
        self.setIconSize(QSize(24, 24))
        self.setMovable(False)
        self.setFloatable(False)
        self.setAllowedAreas(Qt.TopToolBarArea)
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.setStyleSheet('#toolbar { border: none; background-color: transparent; }')

        # get_button('&Run', 'control.png', self.on_toolbar_click, self)
        self.run_button = self.add_button(
            '&Run', 'ic_play_arrow_black_24dp.png', 'Run a thing', self.on_toolbar_click
        )
        self.addSeparator()

        # TODO: use signal corretly
        self.open_button = self.add_button(
            '&Open', 'ic_insert_photo_black_24dp.png', 'Open images', viewer.load_file_dialog
        )
        self.addSeparator()

        self.paste_button = self.add_button(
            '&Paste', 'ic_content_paste_black_24dp.png', 'Paste a thing', self.on_toolbar_click
        )
        self.paste_button.setCheckable(True)
        self.addSeparator()

        self.history_button = self.add_button(
            '&History', 'ic_history_black_24dp.png', 'View history', self.on_toolbar_click
        )
        self.history_button.setCheckable(True)

    def add_button(self, name: str, icon: str, tooltip: str, callback: Callable) -> QAction:
        button_action = QAction(QIcon(str(ICONS_DIR / icon)), name, self)
        button_action.setStatusTip(tooltip)
        button_action.triggered.connect(callback)
        self.addAction(button_action)
        return button_action

    def on_toolbar_click(self, s):
        """Placeholder"""
        logger.info(f'Click; checked: {s}')
