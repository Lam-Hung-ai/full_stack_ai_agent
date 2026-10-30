"""Branch navigation over a conversation's message tree (database §6, API §12).

Edits and regenerations add siblings under the same parent; nothing is
overwritten. The tree is read as bare (id, parent) pairs, oldest first, which
stays small next to the content of a single branch.
"""

from collections import defaultdict
from collections.abc import Iterable
from uuid import UUID


class MessageTree:
    def __init__(self, links: Iterable[tuple[UUID, UUID | None]]) -> None:
        self._parent: dict[UUID, UUID | None] = {}
        self._children: dict[UUID | None, list[UUID]] = defaultdict(list)
        for message_id, parent_id in links:
            self._parent[message_id] = parent_id
            self._children[parent_id].append(message_id)

    def __contains__(self, message_id: object) -> bool:
        return message_id in self._parent

    def siblings(self, message_id: UUID) -> list[UUID]:
        """Versions sharing the message's parent, oldest first, itself included."""
        return list(self._children[self._parent[message_id]])

    def latest_leaf(self, message_id: UUID) -> UUID:
        """Follow the newest child down from `message_id` to a leaf: opening an
        older version shows the conversation as it last continued there."""
        leaf = message_id
        while children := self._children.get(leaf):
            leaf = children[-1]
        return leaf
