# Nối tay endpoint `/agent` thay vì dùng helper có sẵn

> Quyết định hiện hành 26/10/2026: dùng `from ag_ui_langgraph import LangGraphAgent` để emit AG-UI, `EventEncoder` encode SSE. Không dùng CopilotKit; chỉ tham khảo input/output API. Các snippet dưới mô tả endpoint hiện tại, chưa phải detached-worker implementation.

## Vấn đề

`ag_ui_langgraph` cung cấp sẵn `add_langgraph_fastapi_endpoint(app, agent, path)` — một dòng là xong, tự động đăng ký route AG-UI cho LangGraph agent. Đây là cách "chuẩn" được gợi ý trong docs của thư viện.

Nhưng yêu cầu thực tế: về sau cần thêm **custom authentication/authorization** cho endpoint này (xác thực user, kiểm tra quyền trước khi cho chạy agent). Ở phiên bản thư viện local đã đọc, helper nhận `**kwargs` và có thể chuyển `dependencies=[Depends(...)]` vào route; vì vậy không phải helper hoàn toàn không hỗ trợ auth. Dự án vẫn nối tay để nhận principal trong signature, kiểm soát ownership, queue, subscribe/replay và stop lifecycle theo application contract.

## Giải pháp

Nối tay route, dùng trực tiếp các khối xây dựng mà `add_langgraph_fastapi_endpoint` dùng bên trong (`RunAgentInput`, `EventEncoder`, `LangGraphAgent.clone()`/`.run()`), chỉ bỏ qua lớp helper bọc ngoài:

```python
# backend/src/agent_backend/main.py
@app.post("/agent")
async def agent_endpoint(input_data: RunAgentInput, request: Request) -> StreamingResponse:
    # Nối tay (thay vì ag_ui_langgraph.add_langgraph_fastapi_endpoint) để sau này
    # có thể chèn thêm 1 dependency auth/authz ngay tại đây, ví dụ:
    #   async def agent_endpoint(input_data: RunAgentInput, request: Request, user=Depends(get_current_user)):
    encoder = EventEncoder(accept=request.headers.get("accept"))

    # Clone theo từng request: LangGraphAgent giữ state riêng của từng lần chạy
    # trên chính instance, dùng chung 1 instance sẽ bị lẫn state giữa các request đồng thời.
    request_agent = get_agui_agent().clone()

    async def event_generator():
        async for event in request_agent.run(input_data):
            yield encoder.encode(event)

    return StreamingResponse(event_generator(), media_type=encoder.get_content_type())
```

`get_agui_agent()` (trong `agui.py`) chỉ build `LangGraphAgent` **một lần** (`@lru_cache`), còn `.clone()` được gọi **mỗi request** — đây là điểm dễ nhầm: nếu dùng chung một instance cho nhiều request đồng thời, state của các lần chạy sẽ ghi đè lẫn nhau.

## Ví dụ sau khi xử lý

Khi cần thêm auth, chỉ sửa đúng signature của `agent_endpoint`, không phải đào lại cách AG-UI hoạt động bên trong thư viện:

```python
@app.post("/agent")
async def agent_endpoint(
    input_data: RunAgentInput,
    request: Request,
    user: User = Depends(get_current_user),
) -> StreamingResponse:
    ...
```

Đánh đổi: mất vài dòng boilerplate so với gọi helper 1 dòng, đổi lại toàn quyền kiểm soát route — đáng giá vì auth là yêu cầu đã biết trước, không phải đoán.


## Áp dụng cho worker và reconnect

Trong thiết kế đích, worker sở hữu `LangGraphAgent.run(validated_input)` và consume events dù browser đã rời đi. Shared publisher lưu các BaseEvent và cập nhật live projection; HTTP run handler chỉ đọc output, dùng EventEncoder để trả SSE. Không giữ graph execution trong HTTP generator như snippet hiện trạng khi cần sống qua disconnect.

Connect chỉ đọc snapshot + event tail, không gọi lại LangGraphAgent.run(). Restore/title events dùng model chính thức ag_ui.core; không tự implement mapper native graph-to-AG-UI. Dùng wrapper không tự tạo queue, distributed ownership hoặc replay storage.
