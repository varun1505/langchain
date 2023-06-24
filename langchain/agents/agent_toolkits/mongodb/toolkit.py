"""Toolkit for interacting with a MongoDB databa`s`e."""
from typing import List

from pydantic import Field

from langchain.agents.agent_toolkits.base import BaseToolkit
from langchain.base_language import BaseLanguageModel
from langchain.mongodb_database import MongoDB
from langchain.tools import BaseTool
from langchain.tools.mongodb_database.tool import (
    BaseMongoDBTool,
    InfoMongoDBTool,
    QueryMongoDBTool,
    ListMongoDBTool   
)


class MongoDBToolkit(BaseToolkit):
    """Toolkit for interacting with MongoDB databases."""

    db: MongoDB = Field(exclude=True)
    llm: BaseLanguageModel = Field(exclude=True)

    @property
    def language(self) -> str:
        """Return string representation of language to use."""
        return "MongoDB"

    class Config:
        """Configuration for this Pydantic object."""

        arbitrary_types_allowed = True

    def get_tools(self) -> List[BaseTool]:
        """Get the tools in the toolkit."""
        query_mongodb_tool_description = (
            "Input to this tool is a detailed and correct MongoDB command, output is a "
            "result from the database. If the command is not correct, an error message "
            "will be returned. If an error is returned, rewrite the command, check the "
            "command, and try again. If you encounter an issue with Unknown field "
            "'xxxx' in 'field list', using info_mongodb_tool to query the correct collection "
            "fields."
        )
        info_mongodb_tool_description = (
            "Input to this tool is a comma-separated list of collections, output is the "
            "structure and sample documents for those collections. "
            "Be sure that the collections actually exist by calling list_collections_mongodb_tool "
            "first! Example Input: 'collection1, collection2, collection3'"
        )
        return [
            QueryMongoDBTool(
                db=self.db, description=query_mongodb_tool_description
            ),
            InfoMongoDBTool(
                db=self.db, description=info_mongodb_tool_description
            ),
            ListMongoDBTool(db=self.db),
            QueryMongoDBCheckerTool(db=self.db, llm=self.llm),
        ]
