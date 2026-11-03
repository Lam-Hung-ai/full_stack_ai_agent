from app.modules.ai.tools import TOOL_RESOURCE, TOOLS
from app.modules.authorization.catalog import PERMISSIONS


def test_every_tool_has_a_permission():
    granted = {p.action for p in PERMISSIONS if p.resource == TOOL_RESOURCE}
    assert granted == set(TOOLS)
