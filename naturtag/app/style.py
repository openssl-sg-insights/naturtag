from logging import getLogger

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication
from qtawesome import icon
from qtmodern.styles import _STYLESHEET as BASE_STYLESHEET

from naturtag.constants import QSS_PATH

YELLOWGREEN_LIGHT = (154, 205, 50)
YELLOWGREEN_DARK = (135, 181, 44)
SILVER = (173, 168, 182)

# LIGHT_GREEN_INAT = (116, 172, 0)
# PRPL = (200, 0, 200)
# LAVENDER = (180, 180, 255)
# UMBER = (95, 84, 73)
# CERULEAN = (64, 89, 173)
# VIOLET = (42, 30, 92)

logger = getLogger(__name__)


def fa_icon(icon_name, **kwargs):
    """Get a FontAwesome icon, with a default color from the current app's palette"""
    kwargs.setdefault('color', get_palette().brightText().color())
    return icon(icon_name, **kwargs)


def get_palette() -> QPalette:
    return QApplication.instance().palette()


def set_stylesheet(obj=None):
    obj = obj or QApplication.instance()
    logger.debug(f'Loading stylesheet: {QSS_PATH}')

    with open(BASE_STYLESHEET) as f:
        obj.setStyleSheet(f.read())
    with open(QSS_PATH) as f:
        obj.setStyleSheet(f.read())


def set_theme(dark_mode: bool = True):
    logger.debug(f"Setting theme: {'dark' if dark_mode else 'light'}")
    palette = dark_palette() if dark_mode else light_palette()

    app = QApplication.instance()
    app.setStyle('Fusion')
    app.setPalette(palette)
    set_stylesheet()


def dark_palette() -> QPalette:
    base = {
        QPalette.AlternateBase: (66, 66, 66),
        QPalette.Base: (42, 42, 42),
        QPalette.BrightText: YELLOWGREEN_LIGHT,
        QPalette.Button: (53, 53, 53),
        QPalette.ButtonText: (180, 180, 180),
        QPalette.Dark: (35, 35, 35),
        QPalette.Highlight: (42, 130, 218),
        QPalette.HighlightedText: (180, 180, 180),
        QPalette.Light: (180, 180, 180),
        QPalette.Link: (56, 252, 196),
        QPalette.LinkVisited: (80, 80, 80),
        QPalette.Midlight: (90, 90, 90),
        # QPalette.Midlight: CERULEAN,
        QPalette.Shadow: (20, 20, 20),
        QPalette.Text: (180, 180, 180),
        QPalette.ToolTipBase: (53, 53, 53),
        QPalette.ToolTipText: (180, 180, 180),
        # QPalette.ToolTipText: LAVENDER,
        QPalette.Window: (53, 53, 53),
        QPalette.WindowText: (180, 180, 180),
        # QPalette.WindowText: PRPL,
    }
    disabled = {
        QPalette.ButtonText: (127, 127, 127),
        QPalette.Highlight: (80, 80, 80),
        QPalette.HighlightedText: (127, 127, 127),
        QPalette.Text: (127, 127, 127),
        QPalette.WindowText: (127, 127, 127),
    }

    palette = QPalette()
    for role, rgb in base.items():
        palette.setColor(role, QColor(*rgb))
    for role, rgb in disabled.items():
        palette.setColor(QPalette.Disabled, role, QColor(*rgb))
    return palette


def light_palette() -> QPalette:
    base = {
        QPalette.WindowText: (0, 0, 0),
        QPalette.Button: (240, 240, 240),
        QPalette.Light: (180, 180, 180),
        QPalette.Midlight: (200, 200, 200),
        QPalette.Dark: (225, 225, 225),
        QPalette.Text: (0, 0, 0),
        QPalette.BrightText: YELLOWGREEN_DARK,
        QPalette.ButtonText: (0, 0, 0),
        QPalette.Base: (237, 237, 237),
        QPalette.Window: (240, 240, 240),
        QPalette.Shadow: (20, 20, 20),
        QPalette.Highlight: (76, 163, 224),
        QPalette.HighlightedText: (0, 0, 0),
        QPalette.Link: (0, 162, 232),
        QPalette.AlternateBase: (225, 225, 225),
        QPalette.ToolTipBase: (240, 240, 240),
        QPalette.ToolTipText: (0, 0, 0),
        QPalette.LinkVisited: (222, 222, 222),
    }
    disabled = {
        QPalette.WindowText: (115, 115, 115),
        QPalette.Text: (115, 115, 115),
        QPalette.ButtonText: (115, 115, 115),
        QPalette.Highlight: (190, 190, 190),
        QPalette.HighlightedText: (115, 115, 115),
    }

    palette = QPalette()
    for role, rgb in base.items():
        palette.setColor(role, QColor(*rgb))
    for role, rgb in disabled.items():
        palette.setColor(QPalette.Disabled, role, QColor(*rgb))
    return palette
