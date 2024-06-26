from typing import Dict, Iterable, List, Mapping, Sequence

from ._chat_message import ChatMessage, ScoredChatMessage
from ._execution_log_entry import ExecutionLogEntry
from ._message_collection import MessageCollection
from ._message_list import MessageList
from ._monitored_message_list import MonitoredMessageList


class AgentIterationContextStore:
    """
    Data storage for the execution of iteration
    """

    def __init__(self) -> None:
        self._chains: Dict[str, MonitoredMessageList] = {}
        self._evaluator: List[ScoredChatMessage] = []

    @property
    def chains(self) -> Mapping[str, MessageCollection]:
        """
        Returns the messages generated by each chain in this iteration
        """
        return self._chains

    @property
    def evaluator(self) -> Sequence[ScoredChatMessage]:
        """
        Returns the evaluation of this iteration
        """
        return self._evaluator

    def set_evaluator(self, value: Iterable[ScoredChatMessage]) -> None:
        """
        Set the evaluation result for this iteration
        """
        self._evaluator.clear()
        self._evaluator.extend(value)

    def ensure_chain_exists(self, name: str) -> None:
        """
        Ensures a chain exists in the current iteration
        """
        self._chains[name] = MonitoredMessageList(MessageList())

    def append_to_chain(self, chain: str, message: ChatMessage, log_entry: ExecutionLogEntry) -> None:
        """
        store the given message into the chain context

        Args:
            chain: name of the chain
            message: the message to be stored
            log_entry: a log entry to trace the origin of the message
        """
        self._chains[chain].append(message, log_entry)
