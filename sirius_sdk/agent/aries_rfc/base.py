from abc import ABC, abstractmethod

from ..coprotocols import *
from ..agent import TransportLayers


ARIES_DOC_URI = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/'
THREAD_DECORATOR = '~thread'


class AriesProtocolMessage(Message):

    PROTOCOL = None
    NAME = None

    def __init__(self, id_: str=None, version: str='1.0', *args, **kwargs):
        if self.NAME and ('@type' not in dict(*args, **kwargs)):
            kwargs['@type'] = str(
                Type(
                    doc_uri=ARIES_DOC_URI, protocol=self.PROTOCOL,
                    name=self.NAME, version=version
                )
            )
        super().__init__(*args, **kwargs)
        if id_ is not None:
            self['@id'] = id_
        if self.doc_uri != ARIES_DOC_URI:
            raise SiriusValidationError('Unexpected doc_uri "%s"' % self.doc_uri)
        if self.protocol != self.PROTOCOL:
            raise SiriusValidationError('Unexpected protocol "%s"' % self.protocol)
        if self.name != self.NAME:
            raise SiriusValidationError('Unexpected name "%s"' % self.name)

    def validate(self):
        validate_common_blocks(self)


class AriesProblemReport(AriesProtocolMessage):

    NAME = 'problem_report'

    def __init__(self, problem_code: str, explain: str, thread_id: str=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self['problem-code'] = problem_code
        self['explain'] = explain
        if thread_id is not None:
            thread = self.get(THREAD_DECORATOR, {})
            thread['thid'] = thread_id
            self[THREAD_DECORATOR] = thread

    @property
    def problem_code(self) -> str:
        return self.get('problem-code', '')

    @property
    def explain(self) -> str:
        return self.get('explain', '')


class RegisterMessage(type):

    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        if issubclass(cls, AriesProtocolMessage):
            register_message_class(cls, protocol=cls.PROTOCOL, name=cls.NAME)
        return cls


class AbstractStateMachine(ABC):

    def __init__(self, transports: TransportLayers, time_to_live: int=60):
        """
        :param transports: aries-rfc transports factory
        :param time_to_live: state machine time to live to finish progress
        """
        self.__transports = transports
        self.__time_to_live = time_to_live

    @property
    def transports(self) -> TransportLayers:
        return self.__transports

    @property
    def time_to_live(self) -> int:
        return self.__time_to_live

    @property
    @abstractmethod
    def protocols(self) -> List[str]:
        raise NotImplemented('Need to be implemented in descendant')
