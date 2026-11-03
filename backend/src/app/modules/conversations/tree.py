"""Branch navigation over a conversation's turn tree (database §6, API §12).

Edits and regenerations add siblings under the same parent; nothing is
overwritten. The tree is read as bare (id, parent) pairs, oldest first, which
stays small next to the content of a single branch.
"""

from collections import defaultdict
from collections.abc import Iterable
from uuid import UUID


class TurnTree:
    def __init__(self, links: Iterable[tuple[UUID, UUID | None]]) -> None:
        self._parent: dict[UUID, UUID | None] = {}
        self._children: dict[UUID | None, list[UUID]] = defaultdict(list)
        for turn_id, parent_id in links:
            self._parent[turn_id] = parent_id
            self._children[parent_id].append(turn_id)

    def __contains__(self, turn_id: object) -> bool:
        return turn_id in self._parent

    def siblings(self, turn_id: UUID) -> list[UUID]:
        """Versions sharing the turn's parent, oldest first, itself included."""
        return list(self._children[self._parent[turn_id]])

    def latest_leaf(self, turn_id: UUID) -> UUID:
        """Follow the newest child down from `turn_id` to a leaf: opening an
        older version shows the conversation as it last continued there."""
        leaf = turn_id
        while children := self._children.get(leaf):
            leaf = children[-1]
        return leaf
