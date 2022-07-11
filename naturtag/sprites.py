import sqlite3
from logging import basicConfig, getLogger

from attr import define, field
from pyinaturalist import Taxon
from pyinaturalist_convert.db import DbTaxon, get_session
from requests_cache.backends import SQLiteDict
from sqlalchemy import select
from sqlalchemy.exc import MultipleResultsFound, NoResultFound

from naturtag.constants import ASSETS_DIR, DATA_DIR, DB_PATH

SPRITE_DB_PATH = DATA_DIR / 'sprites.db'
SPRITE_DIR = ASSETS_DIR / 'iconic_taxa'


logger = getLogger(__name__)
basicConfig(level='INFO')


@define
class TaxonSprite:
    id: int = field()
    name: str = field()
    sprite: bytes = field(default=None)


# TODO: Order by count, if multiple results take the one with most observations
# TODO: Load from .aseprite files, use Aseprite CLI to export to PNGs
def create_sprite_db():
    """Package sprite files into a database"""
    sprite_db = SQLiteDict(SPRITE_DB_PATH, table_name='taxon_sprite', no_serializer=True)
    session = get_session(DB_PATH)

    # Get taxon names from file paths
    sprite_paths = {}
    for path in SPRITE_DIR.iterdir():
        # name = path.stem.replace('-', ' ')
        name = path.stem.split('-', 1)[-1].replace('-', ' ')
        sprite_paths[name] = path

    for name in sprite_paths.keys():
        # Look up taxon record by name
        try:
            stmt = select(DbTaxon).where(DbTaxon.name == name)
            taxon = session.execute(stmt).one()[0].to_model()
        except NoResultFound:
            logger.warning(f'No taxon found for {name}')
        except MultipleResultsFound:
            logger.warning(f'Multiple taxa found for {name}:')
            for r in session.execute(stmt).all():
                t = r[0].to_model()
                logger.warning(f'  [{t.id}] {t.full_name}')
        # Read corresponding sprite file and save to database
        else:
            with path.open('rb') as f:
                sprite_db[taxon.id] = f.read()
            logger.info(f'Loaded sprite for [{taxon.id}] {taxon.full_name}')

    session.close()


# Or return dict[int, bytes]? Or use SQLiteDict?
def read_sprite_db():
    """Load sprite database into memory"""
    source = sqlite3.connect(SPRITE_DB_PATH)
    dest = sqlite3.connect('file::memory:?cache=shared')
    source.backup(dest)
    return dest


def get_sprite(taxon: Taxon, sprites: dict[int, bytes]) -> bytes:
    """Get sprite for a taxon"""
    for taxon_id in [taxon.id] + list(reversed(taxon.ancestor_ids)):
        if taxon_id in sprites:
            return sprites[taxon_id]
    return b''  # unknown/placeholder
