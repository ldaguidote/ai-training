"""
mcp_secure_server.py — A FastMCP server with JWT authentication.

Run:
    python mcp_secure_server.py
    # It will print the access token to the console — copy it!
"""

import random
from fastmcp import FastMCP
from fastmcp.server.auth import JWTVerifier
from fastmcp.server.auth.providers.jwt import RSAKeyPair

# Generate a key pair (in production: load from environment/secrets manager)
key_pair = RSAKeyPair.generate()
access_token = key_pair.create_token(audience="secure-dice-server")

# Configure JWT authentication
auth = JWTVerifier(
    public_key=key_pair.public_key,
    audience="secure-dice-server",
)

mcp = FastMCP(name="SecureDiceServer", auth=auth)

@mcp.tool
def roll_dice(n_dice: int = 2, sides: int = 6) -> dict:
    """Roll n_dice dice each with the given number of sides."""
    rolls = [random.randint(1, sides) for _ in range(n_dice)]
    return {"rolls": rolls, "total": sum(rolls)}

if __name__ == "__main__":
    # ⚠️ In production: NEVER print tokens to console or logs!
    # This is for demo purposes only.
    print(f"\n🔑 Access token (copy this):\n\n{access_token}\n")
    print("🚀 Starting SecureDiceServer on http://localhost:8001/mcp/")
    mcp.run(transport="http", port=8001)
