"""多智能体服务 - FastAPI后端"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from Director import invoke_graph, stream_graph
import asyncio

app = FastAPI(title="多智能体服务", description="基于LangGraph的多智能体对话服务")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求模型
class ChatRequest(BaseModel):
    message: str
    thread_id: int = None

# 响应模型
class ChatResponse(BaseModel):
    response: str
    thread_id: int

from fastapi.responses import RedirectResponse

@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """同步聊天接口"""
    try:
        response = invoke_graph(request.message, request.thread_id)
        return ChatResponse(
            response=response,
            thread_id=request.thread_id or 1
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """流式聊天接口"""
    try:
        async for chunk in stream_graph(request.message, request.thread_id):
            yield chunk
    except Exception as e:
        yield {"error": str(e)}

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)