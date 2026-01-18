import os
import sys

from mcp.server.fastmcp import FastMCP

if __package__ in (None, ""):
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from flux_analysis_agent import config
from flux_analysis_agent.core.data_store import DataStore
from flux_analysis_agent.core.llm_manager import LLMManager
from flux_analysis_agent.tools import flux_agent as flux_agent_tool
from flux_analysis_agent.tools import get_analysis_result as get_analysis_result_tool
from flux_analysis_agent.tools import upload_data as upload_data_tool


store = DataStore()
llm = None
if config.LLM_ENABLED:
    llm = LLMManager(
        api_key=config.OPENAI_API_KEY,
        model=config.OPENAI_MODEL,
        api_base=config.OPENAI_API_BASE,
    )

mcp = FastMCP("flux_analysis_agent")


@mcp.tool(
    name="upload_data",
    description="Upload a dataset (CSV text) and store it for analysis.",
    meta={
        "input_schema": upload_data_tool.INPUT_SCHEMA,
        "output_schema": upload_data_tool.OUTPUT_SCHEMA,
    },
)
async def upload_data(csv_data: str, data_name: str | None = None) -> dict:
    return await upload_data_tool.handle(csv_data, data_name, store, llm)


@mcp.tool(
    name="get_analysis_result",
    description="Compute and retrieve structured flux analysis results.",
    meta={
        "input_schema": get_analysis_result_tool.INPUT_SCHEMA,
        "output_schema": get_analysis_result_tool.OUTPUT_SCHEMA,
    },
)
async def get_analysis_result(data_id: str, only_significant: bool = False) -> dict:
    return await get_analysis_result_tool.handle(data_id, only_significant, store)


@mcp.tool(
    name="flux_agent",
    description="LLM-driven agent that interprets questions and explains analysis.",
    meta={
        "input_schema": flux_agent_tool.INPUT_SCHEMA,
        "output_schema": flux_agent_tool.OUTPUT_SCHEMA,
    },
)
async def flux_agent(data_id: str, query: str) -> dict:
    return await flux_agent_tool.handle(data_id, query, store, llm)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
