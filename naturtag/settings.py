""" Basic utilities for reading and writing settings from config files """
from collections import Counter, OrderedDict
from itertools import chain
from logging import getLogger
from pathlib import Path
from typing import Iterable, Optional

import yaml
from attr import define, field
from cattr import Converter
from cattr.preconf import pyyaml
from pyinaturalist import TaxonCounts

from naturtag.constants import (
    CONFIG_PATH,
    DEFAULT_WINDOW_SIZE,
    LOGFILE,
    MAX_DISPLAY_HISTORY,
    MAX_DISPLAY_OBSERVED,
    USER_TAXA_PATH,
)

logger = getLogger().getChild(__name__)


def make_converter() -> Converter:
    converter = pyyaml.make_converter()
    converter.register_unstructure_hook(Path, str)
    converter.register_structure_hook(Path, lambda obj, cls: Path(obj))
    return converter


YamlConverter = make_converter()


class YamlMixin:
    """Attrs class mixin that converts to and from a YAML file"""

    path: Path

    @classmethod
    def read(cls) -> 'YamlMixin':
        """Read settings from config file"""
        if not cls.path.is_file():
            return cls()

        logger.info(f'Reading {cls.__name__} from {cls.path}')
        with open(cls.path) as f:
            attrs_dict = yaml.safe_load(f)
            return YamlConverter.structure(attrs_dict, cl=cls)

    def write(self):
        """Write settings to config file"""
        logger.info(f'Writing {self.__class__.__name__} to {self.path}')
        logger.debug(str(self))
        self.path.parent.mkdir(parents=True, exist_ok=True)

        attrs_dict = YamlConverter.unstructure(self)
        with open(self.path, 'w') as f:
            yaml.safe_dump(attrs_dict, f)

    @classmethod
    def reset_defaults(cls) -> 'YamlMixin':
        cls().write()
        return cls.read()


def doc_field(doc: str = '', **kwargs):
    """
    Create a field for an attrs class that is documented in the class docstring.
    """
    return field(metadata={'doc': doc}, **kwargs)


@define
class Settings(YamlMixin):
    path = CONFIG_PATH

    # Display settings
    dark_mode: bool = field(default=False)
    show_logs: bool = field(default=False)
    window_size: tuple[int, int] = field(default=DEFAULT_WINDOW_SIZE)

    # Logging settings
    log_level: str = field(default='INFO')
    log_level_external: str = field(default='INFO')
    logfile: Path = field(default=LOGFILE, converter=Path)

    # iNaturalist
    all_ranks: bool = doc_field(
        default=False, doc='Show all available taxonomic rank filters on taxon search page'
    )
    casual_observations: bool = doc_field(default=True, doc='Include casual observations in searches')
    locale: str = doc_field(default='en', doc='Locale preference for species common names')
    preferred_place_id: int = doc_field(
        default=1, converter=int, doc='Place preference for regional species common names'
    )
    username: str = doc_field(default='', doc='Your iNaturalist username')

    # Metadata
    common_names: bool = doc_field(default=True, doc='Include common names in taxonomy keywords')
    create_sidecar: bool = doc_field(
        default=True, doc="Create XMP sidecar files if they don't already exist"
    )
    hierarchical_keywords: bool = doc_field(
        default=False, doc='Generate pipe-delimited hierarchical keyword tags'
    )

    # TODO: User-specified data directories
    # data_dir: Path = field(default=DATA_DIR, converter=Path)
    # default_image_dir: Path = field(default=Path('~').expanduser(), converter=Path)
    # starred_image_dirs: list[Path] = field(factory=list)

    setup_complete: bool = field(default=False)


@define
class UserTaxa(YamlMixin):
    """Relevant taxon IDs stored for the current user"""

    path = USER_TAXA_PATH

    history: list[int] = field(factory=list)
    starred: list[int] = field(factory=list)
    observed: dict[int, int] = field(factory=dict)
    frequent: Counter[int] = None  # type: ignore

    def __attrs_post_init__(self):
        """Initialize frequent taxa counter"""
        self.frequent = Counter(self.history)

    @property
    def display_ids(self) -> set[int]:
        """Return top history, frequent, observed, and starred taxa combined.
        Returns only unique IDs, since a given taxon may appear in more than one list.
        """
        top_ids = [self.top_history, self.top_frequent, self.top_observed, self.starred]
        return set(chain.from_iterable(top_ids))

    @property
    def top_history(self) -> list[int]:
        """Get the most recently viewed unique taxa"""
        return _top_unique_ids(self.history[::-1])

    @property
    def top_frequent(self) -> list[int]:
        """Get the most frequently viewed taxa"""
        return [t[0] for t in self.frequent.most_common(MAX_DISPLAY_HISTORY)]

    @property
    def top_observed(self) -> list[int]:
        """Get the most commonly observed taxa"""
        return _top_unique_ids(self.observed.keys(), MAX_DISPLAY_OBSERVED)

    def frequent_idx(self, taxon_id: int) -> Optional[int]:
        """Return the position of a taxon in the frequent list, if it's in the top
        ``MAX_DISPLAY_HISTORY`` taxa.
        """
        try:
            return self.top_frequent.index(taxon_id)
        except ValueError:
            return None

    def view_count(self, taxon_id: int) -> int:
        """Return the number of times this taxon has been viewed"""
        return self.frequent.get(taxon_id, 0)

    def update_history(self, taxon_id: int):
        """Update history and frequent with a new or existing taxon ID"""
        self.history.append(taxon_id)
        self.frequent.update([taxon_id])

    def update_observed(self, taxon_counts: TaxonCounts):
        self.observed = {t.id: t.count for t in taxon_counts}
        self.write()

    def __str__(self):
        sizes = [
            f'History: {len(self.history)}',
            f'Starred: {len(self.starred)}',
            f'Frequent: {len(self.frequent)}',
            f'Observed: {len(self.observed)}',
        ]
        return '\n'.join(sizes)

    @classmethod
    def read(cls) -> 'UserTaxa':
        return super(UserTaxa, cls).read()  # type: ignore


def _top_unique_ids(ids: Iterable[int], n: int = MAX_DISPLAY_HISTORY) -> list[int]:
    """Get the top unique IDs from a list, preserving order"""
    return list(OrderedDict.fromkeys(ids))[:n]
