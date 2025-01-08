import requests
import json
from typing import Any
from ast import literal_eval
from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool


class SwarmsAddPromptTool(BuiltinTool):
    """
    Tool for adding a prompt to swarms.world via the /api/add-prompt route.
    """

    def _invoke(self, user_id: str, tool_parameters: dict[str, Any]) -> ToolInvokeMessage:
        swarms_api_key = self.runtime.credentials.get("swarms_api_key")
        if not swarms_api_key:
            return self.create_text_message("Missing Swarms API key in credentials.")

        url = "https://swarms.world/api/add-prompt"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {swarms_api_key}"
        }

        name = tool_parameters.get("name")
        prompt = tool_parameters.get("prompt")
        description = tool_parameters.get("description")
        tags = tool_parameters.get("tags", "")

        # useCases is a list of dict.
        use_cases = tool_parameters.get("use_cases", '')  # string of list of dict.

        # Convert string to list of dict.
        if use_cases:
            use_cases = literal_eval(use_cases)
        else:
            use_cases = []

        data = {
            "name": name,
            "prompt": prompt,
            "description": description,
            "useCases": use_cases,
            "tags": tags
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            response_data = response.json()

            if response.status_code != 200:
                return self.create_text_message(text=f"Error adding prompt: {response_data}")

            return self.create_text_message(text=f"Prompt added successfully: {response_data}")
        except Exception as e:
            return self.create_text_message(text=f"Exception while adding prompt: {str(e)}")