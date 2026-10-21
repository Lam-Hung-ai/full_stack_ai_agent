# Nối tay endpoint `/agent` thay vì dùng helper có sẵn

## Vấn đề

`ag_ui_langgraph` cung cấp sẵn `add_langgraph_fastapi_endpoint(app, agent, path)` — một dòng là xong, tự động đăng ký route AG-UI cho LangGraph agent. Đây là cách "chuẩn" được gợi ý trong docs của thư viện.

Nhưng yêu cầu thực tế: về sau cần thêm **custom authentication/authorization** cho endpoint này (xác thực user, kiểm tra quyền trước khi cho chạy agent). Helper tiện lợi kia không để lộ chỗ nào để chèn một FastAPI `Depends(...)` vào route — nó tự tạo route bên trong, mình không kiểm soát signature của handler.

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
