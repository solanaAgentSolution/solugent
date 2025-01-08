import requests
from typing import Any, Dict, Optional
from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool


class SwarmsQueryPromptTool(BuiltinTool):
    """
    Tool for querying all prompts on swarms.world via the /get-prompts route.
    Supports optional query parameters:
      - name
      - tag
      - use_case
      - use_case_description
    """

    def _invoke(self, user_id: str, tool_parameters: dict[str, Any]) -> ToolInvokeMessage:
        swarms_api_key = self.runtime.credentials.get("swarms_api_key")
        if not swarms_api_key:
            return self.create_text_message("Missing Swarms API key in credentials.")

        # Base endpoint
        url = "https://swarms.world/get-prompts"

        # Set request headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {swarms_api_key}"
        }

        # Collect query params (all optional)
        query_params: Dict[str, Any] = {}

        possible_params = ["name", "tag", "use_case", "use_case_description"]
        for param_key in possible_params:
            if param_key in tool_parameters and tool_parameters[param_key]:
                query_params[param_key] = tool_parameters[param_key]

        try:
            response = requests.get(url, headers=headers, params=query_params)
            if response.status_code != 200:
                return self.create_text_message(text=f"Error fetching prompts: {response.text}")
            return self.create_text_message(text=f"Prompts fetched successfully: {response.json()}")
        except Exception as e:
            return self.create_text_message(text=f"Exception while fetching prompts: {str(e)}")