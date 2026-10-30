"""Files the agent creates with `create_file` (D06, QD-31)."""

import io
import json

from langchain_core.messages import AIMessage

from tests.api.shares.test_shares import share, token_of
from tests.support.chat import body, history, new_conversation, send


def create_call(call_id="call_file", **args):
    return AIMessage(
        content="", tool_calls=[{"name": "create_file", "args": args, "id": call_id}]
    )


def tool_results(assistant):
    return [m for m in assistant["content"] if m["role"] == "tool"]


async def made_file(client, user, headers, *calls, question="Tạo tệp giúp"):
    conversation_id = await new_conversation(client, user, headers)
    await send(client, conversation_id, headers, body(question))
    assistant = (await history(client, conversation_id, headers))["data"][-1]
    return conversation_id, assistant


def stored_body(storage, key):
    return next(body for (_, k), (body, _) in storage.objects.items() if k == key)


async def test_spreadsheet_is_stored_attached_and_downloadable(
    client, db, make_user, login, storage, scripted_model
):
    from openpyxl import load_workbook

    scripted_model(
        create_call(
            name="Chi phí/tháng 3",
            format="xlsx",
            rows=[["Khoản", "Số tiền"], ["Ăn uống", 1500000], ["=HYPERLINK(1)", 2]],
        ),
        "Đã tạo tệp Chi phí tháng 3.xlsx",
    )
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id, assistant = await made_file(client, user, headers)

    (result,) = tool_results(assistant)
    made = json.loads(result["content"])
    assert made["name"] == "Chi phí tháng 3.xlsx"
    (row,) = db("SELECT * FROM chat_app.stored_files WHERE id = %s", (made["file_id"],))
    assert row["uploaded_by"] == user.id and row["size_bytes"] == made["size_bytes"]
    links = db(
        "SELECT message_id FROM chat_app.message_files WHERE stored_file_id = %s",
        (made["file_id"],),
    )
    assert [str(link["message_id"]) for link in links] == [assistant["id"]]

    sheet = load_workbook(io.BytesIO(stored_body(storage, row["object_key"]))).active
    assert sheet is not None
    assert sheet["B2"].value == 1500000
    # Written as text: a spreadsheet never runs it as a formula.
    assert sheet["A3"].value == "=HYPERLINK(1)" and sheet["A3"].data_type == "s"

    link = await client.get(
        f"/api/v1/conversations/{conversation_id}/files/{made['file_id']}",
        headers=headers,
    )
    assert link.status_code == 200 and "attachment" in link.json()["url"]


async def test_text_formats_and_csv_injection(
    client, db, make_user, login, storage, scripted_model
):
    scripted_model(
        create_call(
            "c1", name="bang_so_lieu", format="csv", rows=[["a", "=1+1"], ["@x", -3]]
        ),
        create_call("c2", name="ghi chu.md", format="md", content="# Tiêu đề"),
        "Xong",
    )
    user = make_user("an@example.com")
    headers = await login(user)
    _, assistant = await made_file(client, user, headers)

    csv_made, md_made = [json.loads(m["content"]) for m in tool_results(assistant)]
    # Underscores a model likes become spaces people read.
    assert (csv_made["name"], md_made["name"]) == ("bang so lieu.csv", "ghi chu.md")
    keys = {
        str(r["id"]): r["object_key"]
        for r in db("SELECT id, object_key FROM chat_app.stored_files")
    }
    csv_text = stored_body(storage, keys[csv_made["file_id"]]).decode("utf-8-sig")
    assert csv_text.splitlines() == ["a,'=1+1", "'@x,-3"]
    assert stored_body(storage, keys[md_made["file_id"]]).decode() == "# Tiêu đề"


async def test_bad_requests_are_refused_to_the_model(
    client, db, make_user, login, storage, scripted_model, monkeypatch
):
    from app.modules.files import generated

    monkeypatch.setattr(generated, "MAX_FILES_PER_TURN", 1)
    scripted_model(
        create_call("c1", name="a", format="txt"),  # no content
        create_call("c2", name="b", format="txt", content="ok"),
        create_call("c3", name="c", format="txt", content="quá số tệp"),
        "Xong",
    )
    user = make_user("an@example.com")
    headers = await login(user)
    _, assistant = await made_file(client, user, headers)

    missing, ok, too_many = [m["content"] for m in tool_results(assistant)]
    assert missing.startswith("Could not create the file: content is required")
    assert json.loads(ok)["name"] == "b.txt"
    assert "at most 1 files" in too_many
    assert len(db("SELECT id FROM chat_app.stored_files")) == 1


async def test_member_without_the_grant_never_sees_create_file(
    client, make_user, make_organization, add_member, assign_role, login, scripted_model
):
    model = scripted_model("Không tạo được tệp")
    owner = make_user("owner@example.com")
    member = make_user("member@example.com")
    organization_id, workspace_id = make_organization(owner)
    assign_role(organization_id, add_member(organization_id, member), "member")
    headers = await login(member)
    created = await client.post(
        f"/api/v1/workspaces/{workspace_id}/conversations", json={}, headers=headers
    )
    await send(client, created.json()["id"], headers, body("Tạo tệp"))
    assert all("create_file" not in names for names in model.bound_tools)


async def test_made_files_follow_shares_and_copies(
    client, db, make_user, login, storage, scripted_model
):
    scripted_model(create_call(name="ds", format="txt", content="danh sách"), "Xong")
    owner = make_user("an@example.com")
    reader = make_user("binh@example.com")
    headers = await login(owner)
    conversation_id, assistant = await made_file(client, owner, headers)
    original = json.loads(tool_results(assistant)[0]["content"])["file_id"]
    token = token_of((await share(client, conversation_id, headers))["url"])

    shared = await client.get(f"/api/v1/shares/{token}/files/{original}")
    assert shared.status_code == 200

    reader_headers = await login(reader)
    copied = await client.post(
        f"/api/v1/shares/{token}/copy",
        json={"client_request_id": "r1"},
        headers=reader_headers,
    )
    target = copied.json()["conversation_id"]
    copy_answer = (await history(client, target, reader_headers))["data"][-1]
    new_id = json.loads(tool_results(copy_answer)[0]["content"])["file_id"]
    assert new_id != original
    opened = await client.get(
        f"/api/v1/conversations/{target}/files/{new_id}", headers=reader_headers
    )
    assert opened.status_code == 200


async def test_a_resumed_turn_can_create_files(
    client, db, make_user, login, storage, scripted_model
):
    from tests.api.conversations.test_pause_resume import ASK_ROOM, resume, waiting

    scripted_model(
        ASK_ROOM, create_call(name="Phòng họp", format="txt", content="P1"), "Xong"
    )
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id, assistant = await made_file(client, user, headers)
    (question,) = waiting(assistant)

    status, _ = await resume(
        client,
        conversation_id,
        assistant["id"],
        headers,
        question["interrupt_id"],
        {"answer": "P1"},
    )
    assert status == 200
    final = (await history(client, conversation_id, headers))["data"][-1]
    made = json.loads(tool_results(final)[-1]["content"])
    assert made["name"] == "Phòng họp.txt"
