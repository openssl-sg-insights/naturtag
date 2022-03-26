from logging import getLogger

from kivy.core.clipboard import Clipboard
from kivymd.uix.list import (
    IconRightWidget,
    ILeftBody,
    ILeftBodyTouch,
    IRightBodyTouch,
    MDList,
    ThreeLineAvatarIconListItem,
)
from kivymd.uix.selectioncontrol import MDSwitch

from naturtag.app import alert, get_app
from naturtag.models import Taxon
from naturtag.widgets import CachedAsyncImage

logger = getLogger().getChild(__name__)


class SortableList(MDList):
    """List class that can be sorted by a custom sort key"""

    def __init__(self, sort_key=None, **kwargs):
        self.sort_key = sort_key
        super().__init__(**kwargs)

    def sort(self):
        """Sort child items in-place using current sort key"""
        children = self.children.copy()
        self.clear_widgets()
        for child in sorted(children, key=self.sort_key):
            self.add_widget(child)


class SwitchListItemLeft(ILeftBodyTouch, MDSwitch):
    """Switch that works as a list item"""


class SwitchListItemRight(IRightBodyTouch, MDSwitch):
    """Switch that works as a list item"""


class TaxonListItem(ThreeLineAvatarIconListItem):
    """Class that displays condensed taxon info as a list item"""

    def __init__(
        self,
        taxon: Taxon = None,
        disable_button: bool = False,
        highlight_observed: bool = True,
        **kwargs,
    ):
        self.taxon = taxon

        # Set click event unless disabled
        if not disable_button:
            self.bind(on_touch_down=self._on_touch_down)
        self.disable_button = disable_button

        # TODO: When run from BatchLoader, this appears to just hang and never complete!?
        # Problem may be in ButtonBehavior class?
        super().__init__(
            # font_style='H6',
            text=taxon.name,
            secondary_text=taxon.rank,
            tertiary_text=taxon.preferred_common_name,
            **kwargs,
        )

        # Add thumbnail
        logger.debug(f'TaxonListItem: Loading image {taxon.default_photo.thumbnail_url}')
        self.add_widget(ThumbnailListItem(source=taxon.default_photo.thumbnail_url or taxon.icon_path))
        # Add user icon if taxon has been observed by the user
        if highlight_observed and get_app().is_observed(taxon.id):
            self.add_widget(IconRightWidget(icon='account-search'))

    def _on_touch_down(self, instance, touch):
        """Copy text on right-click"""
        if not self.collide_point(*touch.pos):
            return
        elif touch.button == 'right':
            Clipboard.copy(self.text)
            alert('Copied to clipboard')
        else:
            super().on_touch_down(touch)


class ThumbnailListItem(CachedAsyncImage, ILeftBody):
    """Class that contains a taxon thumbnail to be used in a list item"""

    def __init__(self, **kwargs):
        super().__init__(thumbnail_size='small', **kwargs)
