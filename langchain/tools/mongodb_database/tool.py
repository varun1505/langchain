# flake8: noqa
"""Tools for interacting with a SQL database."""
from typing import Any, Dict, Optional

from pydantic import BaseModel, Extra, Field, root_validator

from langchain.base_language import BaseLanguageModel
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from langchain.mongodb_database import MongoDB
from langchain.tools.base import BaseTool
from langchain.tools.sql_database.prompt import QUERY_CHECKER


class BaseMongoDBTool(BaseModel):
    """Base tool for interacting with a MongoDB database."""

    db: MongoDB = Field(exclude=True)

    # Override BaseTool.Config to appease mypy
    # See https://github.com/pydantic/pydantic/issues/4173
    class Config(BaseTool.Config):
        """Configuration for this Pydantic object."""

        arbitrary_types_allowed = True
        extra = Extra.forbid



class QueryMongoDBTool(BaseMongoDBTool, BaseTool):
    """Tool for querying a MongoDB database."""

    name = "mongodb_query"
    description = """
    Input to this tool is a detailed and correct MongoDB command, output is a result from the database.
    If the command is not correct, an error message will be returned.
    If an error is returned, rewrite the command, check the command, and try again.
    """

    def _run(
        self,
        command: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute the command, return the results or an error message."""
        return self.db.run_no_throw(command)

    async def _arun(
        self,
        command: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        raise NotImplementedError("QueryMongoDBTool does not support async")



class InfoMongoDBTool(BaseMongoDBTool, BaseTool):
    """Tool for getting metadata about a MongoDB database."""

    name = "mongodb_collection_info"
    description = """
    Input to this tool is a comma-separated list of collections, output is the structure and sample documents for those collections.    

    Example Input: "collection1, collection2, collection3"
    """

    def _run(
        self,
        collection_names: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Get the structure for collections in a comma-separated list."""
        return self.db.get_collection_info_no_throw(collection_names.split(", "))

    async def _arun(
        self,
        collection_name: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        raise NotImplementedError("InfoMongoDBTool does not support async")



class ListMongoDBTool(BaseMongoDBTool, BaseTool):
    """Tool for getting collection names."""

    name = "mongodb_list_collections"
    description = "Input is an empty string, output is a comma-separated list of collections in the database."

    def _run(
        self,
        tool_input: str = "",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Get the list of collection names."""
        return ", ".join(self.db.get_usable_collection_names())

    async def _arun(
        self,
        tool_input: str = "",
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        raise NotImplementedError("ListCollectionsMongoDBTool does not support async")



class QueryMongoDBCheckerTool(BaseMongoDBTool, BaseTool):
    """Use an LLM to check if a MongoDB command is correct.
    Adapted from https://www.patterns.app/blog/2023/01/18/crunchbot-sql-analyst-gpt/"""

    template: str = QUERY_CHECKER
    llm: BaseLanguageModel
    llm_chain: LLMChain = Field(init=False)
    name = "mongodb_command_checker"
    description = """
    Use this tool to double check if your command is correct before executing it.
    Always use this tool before executing a command with query_mongodb!
    """

    @root_validator(pre=True)
    def initialize_llm_chain(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if "llm_chain" not in values:
            values["llm_chain"] = LLMChain(
                llm=values.get("llm"),
                prompt=PromptTemplate(
                    template=QUERY_CHECKER, input_variables=["command", "dialect"]
                ),
            )

        if values["llm_chain"].prompt.input_variables != ["command", "dialect"]:
            raise ValueError(
                "LLM chain for QueryCheckerTool must have input variables ['command', 'dialect']"
            )

        return values

    def _run(
        self,
        command: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the LLM to check the command."""
        return self.llm_chain.predict(command=command, dialect=self.db.dialect)

    async def _arun(
        self,
        command: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        return await self.llm_chain.apredict(command=command, dialect=self.db.dialect)
class QueryMongoDBCheckerTool(BaseMongoDBTool, BaseTool):
    """Use an LLM to check if a MongoDB command is correct.
    Adapted from https://www.patterns.app/blog/2023/01/18/crunchbot-sql-analyst-gpt/"""

    template: str = QUERY_CHECKER
    llm: BaseLanguageModel
    llm_chain: LLMChain = Field(init=False)
    name = "mongodb_command_checker"
    description = """
    Use this tool to double check if your command is correct before executing it.
    Always use this tool before executing a command with query_mongodb!
    """

    @root_validator(pre=True)
    def initialize_llm_chain(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if "llm_chain" not in values:
            values["llm_chain"] = LLMChain(
                llm=values.get("llm"),
                prompt=PromptTemplate(
                    template=QUERY_CHECKER, input_variables=["command", "dialect"]
                ),
            )

        if values["llm_chain"].prompt.input_variables != ["command", "dialect"]:
            raise ValueError(
                "LLM chain for QueryCheckerTool must have input variables ['command', 'dialect']"
            )

        return values

    def _run(
        self,
        command: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the LLM to check the command."""
        return self.llm_chain.predict(command=command, dialect=self.db.dialect)

    async def _arun(
        self,
        command: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        return await self.llm_chain.apredict(command=command, dialect=self.db.dialect)

