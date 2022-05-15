"""Components for searching for taxa"""
from logging import getLogger
from typing import Optional

from pyinaturalist import RANKS, IconPhoto
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QComboBox, QGroupBox, QLabel, QPushButton, QSizePolicy

from naturtag.app.style import fa_icon
from naturtag.constants import SELECTABLE_ICONIC_TAXA
from naturtag.metadata import INAT_CLIENT
from naturtag.settings import Settings
from naturtag.widgets import GridLayout, HorizontalLayout, PixmapLabel, TaxonAutocomplete, VerticalLayout

logger = getLogger(__name__)

# TODO: Option to show all ranks
ignore_terms = ['sub', 'super', 'infra', 'epi', 'hybrid']
COMMON_RANKS = [r for r in RANKS if not any([k in r for k in ignore_terms])][::-1]


class TaxonSearch(VerticalLayout):
    """Taxon search"""

    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings

        # Taxon name autocomplete
        self.autocomplete = TaxonAutocomplete()
        self.autocomplete.setAlignment(Qt.AlignTop)
        group_box = QGroupBox('Search')
        group_box.setFixedWidth(400)
        group_box.setLayout(self.autocomplete)
        group_box.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.addWidget(group_box)

        # Category inputs
        categories = VerticalLayout()
        group_box = QGroupBox('Categories')
        group_box.setFixedWidth(400)
        group_box.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        group_box.setLayout(categories)
        self.addWidget(group_box)
        self.category_filters = IconicTaxonFilters()
        categories.addLayout(self.category_filters)

        # Rank inputs
        rank_layout = VerticalLayout()
        group_box = QGroupBox('Rank')
        group_box.setFixedWidth(400)
        group_box.setLayout(rank_layout)
        self.addWidget(group_box)
        self.exact_rank = RankList('Exact')
        self.min_rank = RankList('Minimum')
        self.max_rank = RankList('Maximum')
        rank_layout.addLayout(self.exact_rank)
        rank_layout.addLayout(self.min_rank)
        rank_layout.addLayout(self.max_rank)

        # Clear exact rank after selecting min or max, and vice versa
        self.min_rank.dropdown.activated.connect(self.exact_rank.reset)
        self.max_rank.dropdown.activated.connect(self.exact_rank.reset)
        self.exact_rank.dropdown.activated.connect(self.min_rank.reset)
        self.exact_rank.dropdown.activated.connect(self.max_rank.reset)

        # Search/reset buttons
        button_layout = HorizontalLayout()
        search_button = QPushButton('Search')
        search_button.setIcon(fa_icon('fa.search'))
        search_button.clicked.connect(self.search)
        button_layout.addWidget(search_button)

        reset_button = QPushButton('Reset')
        reset_button.setIcon(fa_icon('mdi.backspace'))
        reset_button.clicked.connect(self.reset)
        button_layout.addWidget(reset_button)
        self.addLayout(button_layout)

        self.addStretch()

    def search(self):
        """Search for taxa with the currently selected filters"""
        taxa = INAT_CLIENT.taxa.search(
            q=self.autocomplete.search_input.text(),
            taxon_id=self.category_filters.selected_iconic_taxa,
            rank=self.exact_rank.text,
            min_rank=self.min_rank.text,
            max_rank=self.max_rank.text,
            preferred_place_id=self.settings.preferred_place_id,
            locale=self.settings.locale,
        ).limit(10)
        logger.info('\n'.join([str(t) for t in taxa]))

    def reset(self):
        """Reset all search filters"""
        self.autocomplete.search_input.setText('')
        self.category_filters.reset()


class IconicTaxonFilters(GridLayout):
    """Filters for iconic taxa"""

    def __init__(self):
        super().__init__(n_columns=6)
        for id, name in SELECTABLE_ICONIC_TAXA.items():
            button = IconicTaxonButton(id, name)
            self.add_widget(button)

    @property
    def selected_iconic_taxa(self) -> list[int]:
        return [t.taxon_id for t in self.widgets if t.isChecked()]

    def reset(self):
        for widget in self.widgets:
            widget.setChecked(False)


class IconicTaxonButton(QPushButton):
    """Button used as a filter for iconic taxa"""

    def __init__(self, taxon_id: int, name: str):
        super().__init__()
        self.taxon_id = taxon_id
        self.name = name

        photo = IconPhoto.from_iconic_taxon(name)
        img = PixmapLabel(url=photo.thumbnail_url)
        self.setIcon(QIcon(img.pixmap()))
        self.setIconSize(QSize(45, 45))

        self.setCheckable(True)
        self.setFixedSize(50, 50)
        self.setContentsMargins(0, 0, 0, 0)
        self.setToolTip(name)


class RankList(HorizontalLayout):
    """Taxonomic rank dropdown"""

    def __init__(self, label: str):
        super().__init__()
        self.addWidget(QLabel(label))
        self.dropdown = QComboBox()
        self.dropdown.addItems([''] + COMMON_RANKS[::-1])
        self.addWidget(self.dropdown)

    def reset(self):
        self.dropdown.setCurrentIndex(0)

    @property
    def text(self) -> Optional[str]:
        return self.dropdown.currentText() or None
