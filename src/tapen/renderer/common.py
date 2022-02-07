import abc

from tapen.common.domain import PrintJob


class BaseRenderer(abc.ABC):

    @abc.abstractmethod
    def render(self, print_job: PrintJob, tape_params: TapeParams):
        pass