from uuid_utils.compat import uuid7

from app.modules.conversations.tree import MessageTree


def test_siblings_and_latest_leaf():
    q1, a1, q2, a2, q1b, a1b, a1c = (uuid7() for _ in range(7))
    tree = MessageTree(
        [
            (q1, None),
            (a1, q1),
            (q2, a1),
            (a2, q2),
            (q1b, None),  # edit of the first question
            (a1b, q1b),
            (a1c, q1b),  # regenerated answer
        ]
    )
    assert tree.siblings(q1) == [q1, q1b]
    assert tree.siblings(a1c) == [a1b, a1c]
    assert tree.siblings(a2) == [a2]
    assert tree.latest_leaf(q1) == a2
    assert tree.latest_leaf(q1b) == a1c
    assert tree.latest_leaf(a1b) == a1b
    assert q1 in tree and uuid7() not in tree
