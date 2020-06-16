#  Copyright (c) 2020 KTH Royal Institute of Technology
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#   limitations under the License.
import time
from abc import ABC, abstractmethod
from multiprocessing import Event

from loguru import logger

from .actuator import BaseActuator
from .sensor import BaseSensor


class BasePlant(ABC):
    """
    Base class providing general functionality to represent closed-loop
    control plants.
    """

    def __init__(self,
                 dt: float,
                 sensor: BaseSensor,
                 actuator: BaseActuator):
        logger.debug('Initializing plant.', enqueue=True)
        self.dt = dt
        self.step_cnt = 0

        self.sensor = sensor
        self.actuator = actuator

        self._shutdown_event = Event()
        self._shutdown_event.clear()

    def shutdown(self):
        # TODO: might need to do more stuff here at some point
        logger.warning('Shutting down plant.', enqueue=True)
        self._shutdown_event.set()

    @abstractmethod
    def pre_actuate_hook(self):
        pass

    @abstractmethod
    def pre_simulate_hook(self):
        pass

    @abstractmethod
    def post_simulate_hook(self):
        pass

    @abstractmethod
    def actuate(self):
        pass

    @abstractmethod
    def simulate(self):
        pass

    def sample_system_state(self):
        # TODO
        pass

    def _step(self):
        self.pre_actuate_hook()
        self.actuate()
        self.pre_simulate_hook()
        self.simulate()
        self.post_simulate_hook()
        self.sample_system_state()

    def run(self):
        """
        Executes the simulation loop.
        """
        while not self._shutdown_event.is_set():
            ti = time.time()
            try:
                logger.debug('Executing simulation step.', enqueue=True)
                self._step()
                logger.debug('Finished simulation step', enqueue=True)
            except Exception as e:
                # TODO: descriptive exceptions
                logger.opt(exception=e).error('Caught exception!', enqueue=True)
                self.shutdown()
                return

            self.step_cnt += 1
            time.sleep(max(self.dt - time.time() + ti, 0))
