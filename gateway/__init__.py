# gateway/ — MCP aggregator gateway.
#
# The gateway is the single MCP server that the agent connects to.
# It spawns each institution server as a subprocess, collects their tools,
# namespaces them, and routes calls to the correct institution.
#
# From the agent's perspective there is only ONE MCP server — the gateway.
# The multi-institution architecture is completely transparent to the LLM.
