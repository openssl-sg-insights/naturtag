from locale import locale_alias, getdefaultlocale
from logging import getLogger
from typing import Tuple, List, Dict
import webbrowser

import requests_cache
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivymd.app import MDApp

from naturtag.app import alert
from naturtag.constants import PLACES_BASE_URL
from naturtag.inat_metadata import get_http_cache_size
from naturtag.thumbnails import get_thumbnail_cache_size
from naturtag.settings import (
    read_settings,
    write_settings,
    read_stored_taxa,
    write_stored_taxa,
    reset_defaults,
)

logger = getLogger(__name__)


# TODO: Track whether state changed since last write; if not, don't write on close
class SettingsController:
    """ Controller class to manage Settings screen, and reading from and writing to settings file """

    def __init__(self, settings_screen):
        self.screen = settings_screen
        self.settings_dict = read_settings()
        self._stored_taxa = read_stored_taxa()

        # Set default locale if it's unset
        if self.inaturalist['locale'] is None:
            self.inaturalist['locale'] = getdefaultlocale()[0]

        self.screen.preferred_place_id_label.bind(
            on_release=lambda *x: webbrowser.open(PLACES_BASE_URL)
        )
        self.screen.dark_mode_chk.bind(active=MDApp.get_running_app().set_theme_mode)

        # Bind buttons (with no persisted value)
        self.screen.reset_default_button.bind(on_release=self.clear_settings)
        self.screen.clear_request_cache_button.bind(on_release=self.clear_http_cache)
        self.screen.clear_thumbnail_cache_button.bind(on_release=self.clear_thumbnail_cache)

        self.screen.cache_size_output.bind(on_release=self.update_cache_sizes)

        # Control widget ids should match the options in the settings file (with suffixes)
        self.controls = {
            id.replace('_chk', '').replace('_input', ''): getattr(settings_screen, id)
            for id in settings_screen
        }
        self.update_control_widgets()
        Clock.schedule_once(self.update_cache_sizes, 5)

    def add_control_widget(self, widget: Widget, setting_name: str, section: str):
        """ Add a control widget from another screen, so its state will be stored with app settings """
        self.controls[setting_name] = widget
        value = self.settings_dict.get(section, {}).get(setting_name)
        self.set_control_value(setting_name, value)
        # Initialize section and setting if either have never been set before
        self.settings_dict.setdefault(section, {})
        self.settings_dict[section].setdefault(setting_name, value)

    def clear_http_cache(self, *args):
        logger.info('Settings: Clearing HTTP request cache')
        requests_cache.clear()
        self.update_cache_sizes()
        alert('Cache has been cleared')

    # TODO
    def clear_thumbnail_cache(self, *args):
        pass

    def clear_settings(self, *args):
        reset_defaults()
        self.update_control_widgets()
        alert('Settings have been reset to defaults')

    @property
    def stored_taxa(self) -> Tuple[List[int], List[int], Dict[int, int]]:
        return (
            self._stored_taxa['history'],
            self._stored_taxa['starred'],
            self._stored_taxa['frequent'],
        )

    def update_control_widgets(self):
        """ Update state of settings controls in UI with values from settings file """
        logger.info(f'Settings: Loading settings: {self.settings_dict}')
        for k, section in self.settings_dict.items():
            for setting_name, value in section.items():
                self.set_control_value(setting_name, value)

    def save_settings(self):
        """ Save the current state of the control widgets to settings file """
        logger.info(f'Settings: Saving settings: {self.settings_dict}')
        for k, section in self.settings_dict.items():
            for setting_name in section.keys():
                value = self.get_control_value(setting_name)
                if value is not None:
                    section[setting_name] = value

        write_settings(self.settings_dict)
        write_stored_taxa(self._stored_taxa)

    def get_control_value(self, setting_name):
        """ Get the value of the control widget corresponding to a setting """
        control_widget, property, _ = self.get_control_widget(setting_name)
        return getattr(control_widget, property) if control_widget else None

    def set_control_value(self, setting_name, value):
        """ Set the value of the control widget corresponding to a setting """
        control_widget, property, setting_type = self.get_control_widget(setting_name)
        if control_widget:
            setattr(control_widget, property, setting_type(value))

    def get_control_widget(self, setting_name):
        """  Find the widget corresponding to a setting and detect its type (bool, str, int) """
        # The setting (from file) may not have a corresponding widget on the Settings screen
        if setting_name not in self.controls:
            return None, None, None

        control_widget = self.controls[setting_name]
        if hasattr(control_widget, 'active'):
            return control_widget, 'active', bool
        elif hasattr(control_widget, 'text'):
            return control_widget, 'text', str
        if hasattr(control_widget, 'path'):
            return control_widget, 'path', str
        else:
            logger.warning(f'Settings: Could not detect type for {control_widget}')

    def update_cache_sizes(self, *args):
        """Populate 'Cache Size' sections with calculated totals"""
        out = self.screen.cache_size_output

        out.text = f'Request cache size: {get_http_cache_size()}'
        num_thumbs, thumbnail_total_size = get_thumbnail_cache_size()
        out.secondary_text = (
            f'Thumbnail cache size: {num_thumbs} files totaling {thumbnail_total_size}'
        )
        hist, hist_unique = len(self._stored_taxa['history']), len(self._stored_taxa['frequent'])

    @property
    def locale(self):
        return self.inaturalist.get('locale')

    @property
    def username(self):
        return self.inaturalist.get('username')

    @property
    def preferred_place_id(self):
        return self.inaturalist.get('preferred_place_id')

    @property
    def inaturalist(self):
        return self.settings_dict['inaturalist']

    @property
    def metadata(self):
        return self.settings_dict['metadata']

    @property
    def display(self):
        return self.settings_dict['display']
