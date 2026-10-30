"""Tools follow `tool.<name>` grants: hidden from the model when not granted,
refused at call time when the grant is revoked during the turn."""

from langchain_core.messages import AIMessage

from tests.support.chat import body, history, send

CLOCK_CALL = AIMessage(
    content="", tool_calls=[{"name": "get_current_time", "args": {}, "id": "call_1"}]
)


async def org_chat(client, headers, workspace_id):
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/conversations", json={}, headers=headers
    )
    return response.json()["id"]


async def test_personal_workspace_offers_the_allowlisted_tools(
    client, make_user, login, scripted_model
):
    model = scripted_model(CLOCK_CALL, "Bây giờ là sáng")
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await org_chat(client, headers, user.personal_workspace_id)

    await send(client, conversation_id, headers, body("Mấy giờ rồi?"))
    assert any("get_current_time" in names for names in model.bound_tools)
    tool_result = (await history(client, conversation_id, headers))["data"][-1][
        "content"
    ][1]
    assert tool_result["role"] == "tool"
    assert "not available" not in tool_result["content"]


async def test_member_without_the_grant_never_sees_the_tool(
    client, make_user, make_organization, add_member, assign_role, login, scripted_model
):
    model = scripted_model("Tôi không xem được giờ")
    owner = make_user("owner@example.com")
    member = make_user("member@example.com")
    organization_id, workspace_id = make_organization(owner)
    assign_role(organization_id, add_member(organization_id, member), "member")
    headers = await login(member)
    conversation_id = await org_chat(client, headers, workspace_id)

    status, _ = await send(client, conversation_id, headers, body("Mấy giờ rồi?"))
    assert status == 200
    assert all("get_current_time" not in names for names in model.bound_tools)


async def test_grant_revoked_during_the_turn_refuses_the_call(
    client, db, make_user, make_organization, login, scripted_model
):
    owner = make_user("owner@example.com")
    organization_id, workspace_id = make_organization(owner)

    def revoke():
        db(
            "DELETE FROM chat_app.role_permissions rp "
            "USING chat_app.organization_roles r, chat_app.permissions p "
            "WHERE rp.role_id = r.id AND rp.permission_id = p.id "
            "AND r.organization_id = %s AND p.resource = 'tool'",
            (organization_id,),
        )

    model = scripted_model(CLOCK_CALL, "Không xem được giờ")
    headers = await login(owner)
    conversation_id = await org_chat(client, headers, workspace_id)
    # The agent is built with the tool; the grant goes before the call runs.
    model.before_reply = revoke

    status, _ = await send(client, conversation_id, headers, body("Mấy giờ rồi?"))
    assert status == 200
    assert any("get_current_time" in names for names in model.bound_tools)
    turn = (await history(client, conversation_id, headers))["data"][-1]
    tool_result = next(m for m in turn["content"] if m["role"] == "tool")
    assert tool_result["content"] == "This tool is not available to you."
    assert turn["status"] == "completed"
