from logging import getLogger

from pyinaturalist.node_api import get_taxa, get_taxa_autocomplete
from naturtag.constants import ICONIC_TAXA, RANKS
from naturtag.models import Taxon
from naturtag.ui import get_app
from naturtag.ui.autocomplete import AutocompleteSearch
from naturtag.ui.image import IconicTaxaIcon, TaxonListItem
from naturtag.ui.widgets import DropdownTextField, StarButton

logger = getLogger().getChild(__name__)


class TaxonAutocompleteSearch(AutocompleteSearch):
    """ Autocomplete search for iNaturalist taxa """
    def get_autocomplete(self, search_str):
        """ Get taxa autocomplete search results, as display text + other metadata """
        def get_dropdown_info(taxon):
            common_name = f' ({taxon["preferred_common_name"]})' if 'preferred_common_name' in taxon else ''
            display_text = f'{taxon["rank"].title()}: {taxon["name"]}{common_name}'
            return {'text': display_text, 'suggestion_text': taxon['matched_term'], 'metadata': taxon}

        results = get_taxa_autocomplete(q=search_str).get('results', [])
        return [get_dropdown_info(taxon) for taxon in results]


class TaxonSelectionController:
    """ Controller class to manage taxon search and selection """
    def __init__(self, screen):
        # Screen and tab references
        self.screen = screen
        self.search_tab = screen.search_tab
        self.search_results_tab = screen.search_results_tab
        self.history_tab = screen.history_tab
        self.frequent_tab = screen.frequent_tab
        self.starred_tab = screen.starred_tab

        # Search inputs
        self.taxon_id_input = screen.search_tab.ids.taxon_id_input
        self.taxon_id_input.bind(on_text_validate=self.on_taxon_id)
        self.taxon_search_input = screen.search_tab.ids.taxon_search_input
        self.taxon_search_input.selection_callback = self.on_select_search_result
        self.exact_rank_input = screen.search_tab.ids.exact_rank_input
        self.min_rank_input = screen.search_tab.ids.min_rank_input
        self.max_rank_input = screen.search_tab.ids.max_rank_input
        self.iconic_taxa_filters = self.screen.search_tab.ids.iconic_taxa

        # Search inputs with dropdowns
        self.rank_menus = (
            DropdownTextField(text_input=self.exact_rank_input, text_items=RANKS),
            DropdownTextField(text_input=self.min_rank_input, text_items=RANKS),
            DropdownTextField(text_input=self.max_rank_input, text_items=RANKS),
        )

        # Buttons
        self.taxon_search_button = self.screen.search_tab.ids.taxon_search_button
        self.taxon_search_button.bind(on_release=self.search)
        self.reset_search_button = self.screen.search_tab.ids.reset_search_button
        self.reset_search_button.bind(on_release=self.reset_search_inputs)

        # 'Categories' (iconic taxa) icons
        for id in ICONIC_TAXA:
            icon = IconicTaxaIcon(id)
            icon.bind(on_release=self.on_select_iconic_taxon)
            self.iconic_taxa_filters.add_widget(icon)

        # Various taxon lists
        self.search_results_list = self.search_results_tab.ids.search_results_list
        self.taxon_history_ids = []
        self.taxon_history_map = {}
        self.taxon_history_list = screen.history_tab.ids.taxon_history_list
        self.starred_taxa_ids = []
        self.starred_taxa_map = {}
        self.starred_taxa_list = screen.starred_tab.ids.starred_taxa_list
        self.frequent_taxa_ids = {}
        self.frequent_taxa_list = screen.frequent_tab.ids.frequent_taxa_list
        self.frequent_taxa_list.sort_key = self.get_frequent_taxon_idx

    @property
    def selected_iconic_taxa(self):
        return [t for t in self.iconic_taxa_filters.children if t.is_selected]

    # TODO: This should be done asynchronously
    def init_stored_taxa(self):
        """ Load taxon history, starred, and frequently viewed items """
        logger.info('Loading stored taxa')
        stored_taxa = get_app().stored_taxa
        self.taxon_history_ids, self.starred_taxa_ids, self.frequent_taxa_ids = stored_taxa

        for taxon_id in self.taxon_history_ids[::-1]:
            if taxon_id not in self.taxon_history_map:
                item = self.get_taxon_list_item(taxon_id=taxon_id, parent_tab=self.history_tab)
                self.taxon_history_list.add_widget(item)
                self.taxon_history_map[taxon_id] = item

        for taxon_id in self.starred_taxa_ids[::-1]:
            self.add_star(taxon_id)

        for taxon_id in self.frequent_taxa_ids.keys():
            item = self.get_taxon_list_item(taxon_id=taxon_id, parent_tab=self.frequent_tab)
            self.frequent_taxa_list.add_widget(item)

    # TODO: Paginated results
    def search(self, *args):
        """ Run a search with the currently selected search parameters """
        params = self.get_search_parameters()
        logger.info(f'Searching taxa with parameters: {params}')
        results = get_taxa(**params)['results']
        logger.info(f'Found {len(results)} search results')
        self.update_search_results(results)

    def get_search_parameters(self):
        """ Get API-compatible search parameters from the input widgets """
        params = {
            'q': self.taxon_search_input.input.text,
            'taxon_id': [t.taxon_id for t in self.selected_iconic_taxa],
            'rank': self.exact_rank_input.text,
            'min_rank': self.min_rank_input.text,
            'max_rank': self.max_rank_input.text,
            'per_page': 30,
            'locale': get_app().locale,
            'preferred_place_id': get_app().preferred_place_id,
        }
        return {k: v for k, v in params.items() if v}

    def update_search_results(self, results):
        self.search_results_list.clear_widgets()
        for taxon_dict in results:
            item = self.get_taxon_list_item(taxon=Taxon.from_dict(taxon_dict), parent_tab=self.search_results_tab)
            self.search_results_list.add_widget(item)

    def reset_search_inputs(self, *args):
        logger.info('Resetting search filters')
        for t in self.selected_iconic_taxa:
            t.toggle_selection()
        self.exact_rank_input.text = ''
        self.min_rank_input.text = ''
        self.max_rank_input.text = ''

    def update_history(self, taxon_id: int):
        """ Update history + frequency """
        self.taxon_history_ids.append(taxon_id)

        # If item already exists in history, move it from its previous position to the top
        if taxon_id in self.taxon_history_map:
            item = self.taxon_history_map[taxon_id]
            self.taxon_history_list.remove_widget(item)
        else:
            item = self.get_taxon_list_item(taxon_id=taxon_id, parent_tab=self.history_tab)
            self.taxon_history_map[taxon_id] = item

        self.taxon_history_list.add_widget(item, len(self.taxon_history_list.children))
        self.add_frequent_taxon(taxon_id)

    def add_frequent_taxon(self, taxon_id: int):
        self.frequent_taxa_ids.setdefault(taxon_id, 0)
        self.frequent_taxa_ids[taxon_id] += 1
        self.frequent_taxa_list.sort()

    def add_star(self, taxon_id: int):
        """ Add a taxon to Starred list """
        logger.info(f'Adding taxon to starred: {taxon_id}')
        item = self.get_taxon_list_item(taxon_id=taxon_id, parent_tab=self.starred_tab)
        if taxon_id not in self.starred_taxa_ids:
            self.starred_taxa_ids.append(taxon_id)
        self.starred_taxa_map[taxon_id] = item
        self.starred_taxa_list.add_widget(item, len(self.starred_taxa_list.children))
        # Add X (remove) button
        remove_button = StarButton(taxon_id, icon='close')
        remove_button.bind(on_release=lambda x: self.remove_star(x.taxon_id))
        item.add_widget(remove_button)

    def remove_star(self, taxon_id: int):
        """ Remove a taxon from Starred list """
        logger.info(f'Removing taxon from starred: {taxon_id}')
        item = self.starred_taxa_map.pop(taxon_id)
        self.starred_taxa_ids.remove(taxon_id)
        self.starred_taxa_list.remove_widget(item)

    def is_starred(self, taxon_id: int) -> bool:
        """ Check if the specified taxon is in the Starred list """
        return taxon_id in self.starred_taxa_map

    def get_frequent_taxon_idx(self, list_item) -> int:
        """ Get sort index for frequently viewed taxa (by number of views, descending) """
        num_views = self.frequent_taxa_ids.get(list_item.taxon.id, 0)
        return num_views * -1  # Effectively the same as reverse=True

    @staticmethod
    def get_taxon_list_item(**kwargs):
        """ Get a taxon list item, with thumbnail + info, that selects its taxon when pressed """
        return TaxonListItem(**kwargs, button_callback=lambda x: get_app().select_taxon(x.taxon))

    @staticmethod
    def on_select_iconic_taxon(button):
        """ Handle clicking an iconic taxon; don't re-select the taxon if we're de-selecting it """
        if not button.is_selected:
            get_app().select_taxon(id=button.taxon_id)

    @staticmethod
    def on_select_search_result(metadata: dict):
        """ Handle clicking a taxon from autocomplete dropdown """
        get_app().select_taxon(taxon_dict=metadata)

    @staticmethod
    def on_taxon_id(input):
        """ Handle entering a taxon ID and pressing Enter """
        get_app().select_taxon(id=int(input.text))

