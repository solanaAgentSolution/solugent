import requests
import json
from ast import literal_eval
from typing import Any, List
from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool


class SwarmsAddAgentTool(BuiltinTool):
    """
    Tool for adding a new agent to swarms.world via the /api/add-agent route.
    """

    def _invoke(self, user_id: str, tool_parameters: dict[str, Any]) -> ToolInvokeMessage:
        swarms_api_key = self.runtime.credentials.get("swarms_api_key")
        if not swarms_api_key:
            return self.create_text_message("Missing Swarms API key in credentials.")

        url = "https://swarms.world/api/add-agent"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {swarms_api_key}"
        }

        name = tool_parameters.get("name")
        agent = tool_parameters.get("agent")
        description = tool_parameters.get("description")
        language = tool_parameters.get("language", "python")
        use_cases = tool_parameters.get("use_cases", '')
        if use_cases:
            use_cases = literal_eval(use_cases)
        else:
            use_cases = []
        
        requirements = tool_parameters.get("requirements", '')
        if requirements:
            requirements = literal_eval(requirements)
        else:
            requirements = []
        
        tags = tool_parameters.get("tags", "")

        data = {
            "name": name,
            "agent": agent,
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
                return self.create_text_message(text=f"Error adding agent: {response_data}")

            return self.create_text_message(text=f"Agent added successfully: {response_data}")
        except Exception as e:
            return self.create_text_message(text=f"Exception while adding agent: {str(e)}")