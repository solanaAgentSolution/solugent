from typing import Any
from solana.rpc.api import Client
from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool


class SolanaGetClusterNodesTool(BuiltinTool):
    """
    Tool for checking the balance of a specified Solana account.
    """

    def _invoke(self, user_id: str, tool_parameters: dict[str, Any]) -> ToolInvokeMessage:
        solana_rpc_url = self.runtime.credentials["solana_rpc_url"]
        client = Client(solana_rpc_url)
        try:
            cluster_nodes = client.get_cluster_nodes()
            cluster_nodes = cluster_nodes.to_json()
            return self.create_text_message(text=f"Cluster nodes: {cluster_nodes}")
        except Exception as e:
            return self.create_text_message(text=f"Error fetching cluster nodes: {str(e)}")
