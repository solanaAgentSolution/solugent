import requests
import json
from ast import literal_eval
from typing import Any
from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool


class SwarmsEditAgentTool(BuiltinTool):
    """
    Tool for editing an existing agent on swarms.world via the /api/edit-agent route.
    """

    def _invoke(self, user_id: str, tool_parameters: dict[str, Any]) -> ToolInvokeMessage:
        swarms_api_key = self.runtime.credentials.get("swarms_api_key")
        if not swarms_api_key:
            return self.create_text_message("Missing Swarms API key in credentials.")

        url = "https://swarms.world/api/edit-agent"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {swarms_api_key}"
        }

        agent_id = tool_parameters.get("id")
        name = tool_parameters.get("name")
        agent_text = tool_parameters.get("agent")
        description = tool_parameters.get("description")
        language = tool_parameters.get("language")
        use_cases = tool_parameters.get("use_cases", [])
        if use_cases:
            use_cases = literal_eval(use_cases)
        else:
            use_cases = []
        requirements = tool_parameters.get("requirements", [])
        if requirements:
            requirements = literal_eval(requirements)
        else:
            requirements = []
        tags = tool_parameters.get("tags", "")

        data = {
            "id": agent_id,
            "name": name,
            "agent": agent_text,
            "description": description,
            "language": language,
            "useCases": use_cases,
            "requirements": requirements,
            "tags": tags
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            response_data = response.json()

            if response.status_code != 200:
                return self.create_text_message(text=f"Error editing agent: {response_data}")

            return self.create_text_message(text=f"Agent edited successfully: {response_data}")
        except Exception as e:
            return self.create_text_message(text=f"Exception while editing agent: {str(e)}")