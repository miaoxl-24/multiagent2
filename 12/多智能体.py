import asyncio
import os

from langgraph.prebuilt import create_react_agent
from langchain_community.chat_models import ChatTongyi
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_redis import RedisConfig, RedisVectorStore
from operator import add
from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_stream_writer
from langgraph.graph import StateGraph, START, END
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import StructuredTool
from config.load_key import load_key


def wrap_async_tool(async_tool):
    async def async_run(**kwargs):
        return await async_tool.arun(**kwargs)
    
    return async_tool


nodes = ["supervisor", "travel", "couplet", "joke", "other"]

llm = ChatTongyi(
    model="qwen-plus",
    dashscope_api_key=load_key("BAILIAN_API_KEY")
)


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add]
    type: str


def other_node(state: State):
    writer = get_stream_writer()
    writer({"node": ">>> other_node"})
    return {
        "messages": [HumanMessage(content="我暂时无法回答这个问题")],
        "type": "other"
    }


def supervisor_node(state: State):
    writer = get_stream_writer()
    writer({"node": ">>>> supervisor_node"})
    prompt = """你是一个专业的客服助手，负责对用户的问题进行分类，并将任务分给其他Agent执行。
    如果用户的问题是和旅游路线规划相关的，那就返回 travel 。
    如果用户的问题是希望讲一个笑话，那就返回 joke 。
    如果用户的问题是希望对一个对联，那就返回 couplet 。
    如果是其他的问题，返回 other 。
    除了这几个选项外，不要返回任何其他的内容。
    """

    prompts = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": str(state["messages"][0])}
    ]
    
    if "type" in state:
        writer({"supervisor_step": f"已获得{state['type']} 智能体处理结果"})
        return {"type": END}

    else:
        response = llm.invoke(prompts)
        typeRes = response.content
        writer({"supervisor_step": f"问题分类结果: {typeRes}"})
        if typeRes in nodes:
            return {"type": typeRes}
        else:
            raise ValueError(f"type is not in (travel,joke,other,couplet): {typeRes}")

    return {}


async def travel_node_async(state: State):
    writer = get_stream_writer()
    writer({"node": ">>>> travel_node"})

    system_prompt = "你是一个专业的旅行规划助手，根据用户的问题，使用地图工具查询路线并生成一个旅游路线规划。请用中文回答。"

    prompts = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": state["messages"][0]}
    ]

    client = MultiServerMCPClient(
        {
            "amap-maps": {
                "command": "npx",
                "args": [
                    "-y",
                    "@amap/amap-maps-mcp-server"
                ],
                "env": {
                    "AMAP_MAPS_API_KEY": "451ad40d0e39453600f2a305e31eabe4"
                },
                "transport": "stdio"
            }
        }
    )

    async_tools = await client.get_tools()
    agent = create_react_agent(model=llm, tools=async_tools)
    response = await agent.ainvoke({"messages": prompts})
    writer({"travel_result": response["messages"][-1].content})
    return {"messages": [HumanMessage(content=response["messages"][-1].content)], "type": "travel"}


def travel_node(state: State):
    return asyncio.run(travel_node_async(state))


def joke_node(state: State):
    writer = get_stream_writer()
    writer({"node": ">>> joke_node"})

    system_prompt = "你是一个笑话大师，根据用户的问题，写一个不超过100个字的笑话。"

    prompts = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": state["messages"][0]}
        ]
    response = llm.invoke(prompts)
    writer({"joke_result": response.content})

    return {"messages": [HumanMessage(content=response.content)], "type": "joke"}


def couplet_node(state: State):
    writer = get_stream_writer()
    writer({"node": ">>> couplet_node"})
    
    # 设置环境变量
    if not os.environ.get("DASHSCOPE_API_KEY"):
        os.environ["DASHSCOPE_API_KEY"] = load_key("BAILIAN_API_KEY")
    
    # 提取用户查询
    query = str(state["messages"][0])
    
    # 提取上联
    上联 = query
    if "上联" in query:
        parts = query.split("：") if "：" in query else query.split(":")
        if len(parts) > 1:
            上联 = parts[1].strip()
    
    # 从 Redis Hash 中获取对联样本
    import redis
    import json
    
    redis_client = redis.from_url("redis://localhost:6379")
    samples = []
    
    try:
        # 获取所有对联数据（最多取10条）
        hash_data = redis_client.hgetall("poi_data")
        count = min(len(hash_data), 10)
        
        for i in range(count):
            item = redis_client.hget("poi_data", str(i))
            if item:
                try:
                    data = json.loads(item.decode('utf-8'))
                    # 提取对联内容
                    if 'text' in data:
                        samples.append(data['text'])
                    elif '上联' in data and '下联' in data:
                        samples.append(f"{data['上联']} - {data['下联']}")
                    elif isinstance(data, dict) and len(data) >= 2:
                        # 假设第一个字段是上联，第二个是下联
                        keys = list(data.keys())[:2]
                        if len(keys) == 2:
                            samples.append(f"{data.get(keys[0], '')} - {data.get(keys[1], '')}")
                except:
                    # 如果解析失败，直接使用原始内容
                    samples.append(item.decode('utf-8')[:50])
        
        writer({"couplet_samples_count": len(samples)})
    except Exception as e:
        writer({"couplet_error": str(e)})
        samples = []
    
    # 构建 RAG 提示词
    system_prompt = """你是一个专业的对联大师，你的任务是根据用户给出的上联，设计一个下联。
回答时，可以参考下面的参考对联。

参考对联：
{samples}

请用中文回答问题
"""
    
    # 格式化参考对联
    if samples:
        samples_text = "\n".join([f"{i+1}. {sample}" for i, sample in enumerate(samples)])
    else:
        samples_text = "暂无参考对联"
    
    system_prompt = system_prompt.format(samples=samples_text)
    
    prompts = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"根据上联生成下联：{上联}"}
    ]
    
    response = llm.invoke(prompts)
    下联 = response.content.strip()
    
    writer({"couplet_result": f"上联: {上联}, 下联: {下联}"})
    return {"messages": [HumanMessage(content=f"上联：{上联}\n下联：{下联}")], "type": "couplet"}


def routing_func(state: State):
    if state["type"] == "travel":
        return "travel_node"
    elif state["type"] == "joke":
        return "joke_node"
    elif state["type"] == "couplet":
        return "couplet_node"
    elif state["type"] == END:
        return END
    else:
        return "other_node"


builder = StateGraph(State)

builder.add_node("supervisor_node", supervisor_node)
builder.add_node("travel_node", travel_node)
builder.add_node("joke_node", joke_node)
builder.add_node("couplet_node", couplet_node)
builder.add_node("other_node", other_node)

builder.add_edge(START, "supervisor_node")
builder.add_conditional_edges("supervisor_node", routing_func, path_map=["travel_node", "joke_node", "couplet_node", "other_node", END])
builder.add_edge(start_key="travel_node", end_key="supervisor_node")
builder.add_edge(start_key="joke_node", end_key="supervisor_node")
builder.add_edge(start_key="couplet_node", end_key="supervisor_node")
builder.add_edge(start_key="other_node", end_key="supervisor_node")

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

if __name__ == "__main__":
    config = {
        "configurable": {
            "thread_id": "1"
        }
    }

    # 测试对联功能
    for chunk in graph.stream(
        input={"messages": ["帮我对个对联，上联是：瑞雪兆丰年"]},
        config=config,
        stream_mode="custom"
    ):
        print(chunk)