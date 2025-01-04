from core.tools.provider.builtin.solana_api.tools.solana_get_cluster_nodes import SolanaGetClusterNodesTool
from core.tools.provider.builtin_tool_provider import BuiltinToolProviderController
from core.tools.errors import ToolProviderCredentialValidationError


class SolanaAPIProvider(BuiltinToolProviderController):
    """
    Main interface for the Solana API.
    Manages interaction with the Solana blockchain and validates credentials.
    """

    def _validate_credentials(self, credentials: dict) -> None:
        # Implement credential validation logic here
        try:
            SolanaGetClusterNodesTool().fork_tool_runtime(
                runtime={
                    "credentials": credentials,
                }
            ).invoke(
                user_id="",
                tool_parameters={},
            )
        except Exception as e:
            raise ToolProviderCredentialValidationError(str(e))
