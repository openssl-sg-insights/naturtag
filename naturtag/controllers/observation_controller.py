from logging import getLogger

from pyinaturalist import Observation
from PySide6.QtCore import Qt, QThread, Signal, Slot

from naturtag.client import INAT_CLIENT
from naturtag.controllers import BaseController, ObservationInfoSection
from naturtag.widgets import HorizontalLayout, VerticalLayout

logger = getLogger(__name__)


class ObservationController(BaseController):

    on_select = Signal(Observation)  #: An observation was selected

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.root = HorizontalLayout(self)
        self.root.setAlignment(Qt.AlignLeft)
        self.selected_observation: Observation = None

        # TODO: basically everything
        # self.root.addWidget(QLabel("Observation"))

        # Selected observation info
        self.obs_info = ObservationInfoSection(self.threadpool)
        # self.obs_info.on_select.connect(self.select_observation)
        self.obs_info.on_select_obj.connect(self.display_observation)
        obs_layout = VerticalLayout()
        obs_layout.addLayout(self.obs_info)
        self.root.addLayout(obs_layout)

    def select_observation(self, observation_id: int):
        # Don't need to do anything if this observation is already selected
        if self.selected_observation and self.selected_observation.id == observation_id:
            return

        logger.info(f'Selecting observation {observation_id}')
        future = self.threadpool.schedule(
            lambda: INAT_CLIENT.observations(observation_id, taxonomy=True),
            priority=QThread.HighPriority,
        )
        future.on_result.connect(self.display_observation)

    @Slot(Observation)
    def display_observation(self, observation: Observation):
        self.selected_observation = observation
        self.on_select.emit(observation)
        self.obs_info.load(observation)
        logger.debug(f'Loaded observation {observation.id}')
