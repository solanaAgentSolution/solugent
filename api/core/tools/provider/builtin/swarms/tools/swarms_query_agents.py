import requests
from typing import Any, Dict
from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool


class SwarmsQueryAgentsTool(BuiltinTool):
    """
    Tool for querying all agents on swarms.world via the /get-agents route.
    Supports optional query parameters:
      - name
      - tag
      - language
      - use_case
      - req_package
    """

    def _invoke(self, user_id: str, tool_parameters: dict[str, Any]) -> ToolInvokeMessage:
        swarms_api_key = self.runtime.credentials.get("swarms_api_key")
        if not swarms_api_key:
            return self.create_text_message("Missing Swarms API key in credentials.")

        url = "https://swarms.world/get-agents"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {swarms_api_key}"
        }

        query_params: Dict[str, Any] = {}
        possible_params = ["name", "tag", "language", "use_case", "req_package"]

        for param_key in possible_params:
            if param_key in tool_parameters and tool_parameters[param_key]:
                query_params[param_key] = tool_parameters[param_key]

        try:
            response = requests.get(url, headers=headers, params=query_params)
            if response.status_code != 200:
                return self.create_text_message(text=f"Error fetching agents: {response.text}")
            return self.create_text_message(text=f"Agents fetched successfully: {response.json()}")
        except Exception as e:
            return self.create_text_message(text=f"Exception while fetching agents: {str(e)}")