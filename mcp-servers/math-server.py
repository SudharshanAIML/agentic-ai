from mcp.server.fastmcp import FastMCP
mcp = FastMCP("MathServer")

@mcp.tool()
def add(a:int , b:int)->int :
    """Add two numbers"""
    return a+b

@mcp.tool()
def multifply(a:int , b:int)->int:
    """Multiply Two Numbers"""
    return a*b


if __name__ == "__main__":
    mcp.run(transport="stdio")