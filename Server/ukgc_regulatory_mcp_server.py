#!/usr/bin/env python3
"""
UKGC Regulatory Framework MCP Server
Integrates LCCP, ISO 27001, and RTS documents for unified compliance querying
"""

import json
import os
from pathlib import Path
from typing import Any, Optional
import mcp.server.stdio
from mcp.server import Server
from mcp.types import Tool, TextContent, ToolResult

# Initialize MCP Server
server = Server("ukgc-regulatory-mcp")

# Configuration
BASE_PATH = Path("/Users/adamavery/UKGC_Project/JSON Files")
FRAMEWORKS = {
    "lccp": BASE_PATH / "lccp",
    "iso27001": BASE_PATH / "iso-27001",
    "rts": BASE_PATH / "rts",
    "indexes": BASE_PATH / "index"
}

# In-memory document store
documents = {
    "lccp": [],
    "iso27001": [],
    "rts": [],
    "indexes": {}
}

# Cross-reference cache
cross_references = {}


def load_documents():
    """Load all JSON documents from framework directories"""
    print("Initializing UKGC Regulatory MCP Server...")
    
    for framework, path in FRAMEWORKS.items():
        if framework == "indexes":
            # Load special index files
            if path.exists():
                for file in path.glob("*.json"):
                    try:
                        with open(file, 'r') as f:
                            doc = json.load(f)
                            doc_name = file.stem
                            documents["indexes"][doc_name] = doc
                            print(f"  Loaded index: {doc_name}")
                    except Exception as e:
                        print(f"  Error loading {file}: {e}")
        else:
            # Load framework documents
            if path.exists():
                for file in path.glob("*.json"):
                    try:
                        with open(file, 'r') as f:
                            doc = json.load(f)
                            documents[framework].append({
                                "filename": file.name,
                                "content": doc
                            })
                            print(f"  Loaded {framework}: {file.name}")
                    except Exception as e:
                        print(f"  Error loading {file}: {e}")
    
    print(f"\nDocuments loaded:")
    print(f"  LCCP: {len(documents['lccp'])} files")
    print(f"  ISO 27001: {len(documents['iso27001'])} files")
    print(f"  RTS: {len(documents['rts'])} files")
    print(f"  Indexes: {len(documents['indexes'])} files")
    print()


def search_documents(query: str, framework: Optional[str] = None) -> list[dict]:
    """
    Search documents using natural language query
    Returns matching provisions with framework context
    """
    query_lower = query.lower()
    results = []
    
    frameworks_to_search = [framework] if framework else ["lccp", "iso27001", "rts"]
    
    for fw in frameworks_to_search:
        if fw not in documents or not documents[fw]:
            continue
            
        for doc in documents[fw]:
            content = json.dumps(doc["content"]).lower()
            
            if query_lower in content:
                # Extract relevant sections
                doc_content = doc["content"]
                
                # Try to find specific matching provision/control
                match_info = {
                    "framework": fw,
                    "filename": doc["filename"],
                    "title": doc_content.get("control_title") or 
                            doc_content.get("provision_title") or 
                            doc_content.get("title") or "Unknown",
                    "id": doc_content.get("control_id") or 
                         doc_content.get("provision_id") or 
                         doc_content.get("rts_id") or doc["filename"],
                    "relevance_score": content.count(query_lower)
                }
                
                results.append(match_info)
    
    # Sort by relevance
    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return results[:20]  # Return top 20 results


def get_cross_references(provision_id: str, framework: str) -> dict:
    """
    Get cross-references between frameworks for a provision
    """
    if "cross-reference-mapping-lccp-iso27001-rts" not in documents["indexes"]:
        return {"error": "Cross-reference mapping not loaded"}
    
    mapping = documents["indexes"]["cross-reference-mapping-lccp-iso27001-rts"]
    
    # Search through mappings
    for mapping_group in mapping.get("lccp_operating_licence_conditions_mappings", []):
        for provision in mapping_group.get("mappings", []):
            if provision.get("lccp_id") == provision_id and framework == "lccp":
                return {
                    "provision_id": provision_id,
                    "title": provision.get("lccp_title"),
                    "iso27001_controls": provision.get("supporting_iso27001_controls", []),
                    "rts_chapters": provision.get("supporting_rts", [])
                }
    
    # Similar searches for other frameworks would go here
    return {"error": f"Provision {provision_id} not found in {framework}"}


def get_compliance_path(provision_id: str) -> dict:
    """
    Get full compliance path: LCCP requirement → ISO 27001 → RTS
    """
    framework_doc = documents["indexes"].get("framework-relationship-documentation-lccp-iso27001-rts", {})
    
    if not framework_doc:
        return {"error": "Framework documentation not available"}
    
    # Return framework relationship guidance
    return {
        "guidance": "Use Master Index to find LCCP → Cross-Reference Mapping for ISO 27001 and RTS → Framework Docs for integration",
        "steps": [
            "1. Identify LCCP requirement - What must you do?",
            "2. Find supporting ISO 27001 controls - How do you do this securely?",
            "3. Reference RTS specifications - What are the technical details?",
            "4. Verify compliance across all three frameworks"
        ]
    }


def query_by_license_type(license_type: str) -> dict:
    """
    Get all applicable LCCP provisions for a specific license type
    """
    master_index = documents["indexes"].get("regulatory-master-index-complete", {})
    
    if not master_index:
        return {"error": "Master index not available"}
    
    # Return guidance on how to use master index
    return {
        "license_type": license_type,
        "guidance": f"Consult Master Regulatory Index for {license_type} applicable provisions",
        "note": "Master Index contains mapping of all {len(documents['lccp'])} LCCP provisions to license types"
    }


# Define MCP Tools

@server.call_tool()
async def search_regulations(query: str, framework: Optional[str] = None) -> ToolResult:
    """
    Search across all regulatory documents
    
    Args:
        query: Natural language search query (e.g., "age verification", "fund protection")
        framework: Optional specific framework to search (lccp, iso27001, rts)
    
    Returns:
        Matching provisions with framework and location information
    """
    results = search_documents(query, framework)
    
    if not results:
        return ToolResult(
            content=[TextContent(
                type="text",
                text=f"No provisions found matching '{query}'"
            )],
            is_error=False
        )
    
    # Format results
    output = f"Found {len(results)} matching provisions:\n\n"
    for result in results:
        output += f"Framework: {result['framework'].upper()}\n"
        output += f"ID: {result['id']}\n"
        output += f"Title: {result['title']}\n"
        output += f"File: {result['filename']}\n"
        output += f"Relevance: {result['relevance_score']} matches\n\n"
    
    return ToolResult(
        content=[TextContent(type="text", text=output)],
        is_error=False
    )


@server.call_tool()
async def get_provision_details(provision_id: str, framework: str) -> ToolResult:
    """
    Get detailed information about a specific provision
    
    Args:
        provision_id: ID of provision (e.g., "3.2.11", "A_8.24", "RTS-07")
        framework: Framework (lccp, iso27001, or rts)
    
    Returns:
        Full provision details and requirements
    """
    # Search for provision in documents
    for doc in documents.get(framework, []):
        content = doc["content"]
        doc_id = (content.get("control_id") or content.get("provision_id") or 
                 content.get("rts_id") or "")
        
        if provision_id in doc_id or provision_id in doc["filename"]:
            return ToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps(content, indent=2)
                )],
                is_error=False
            )
    
    return ToolResult(
        content=[TextContent(
            type="text",
            text=f"Provision {provision_id} not found in {framework}"
        )],
        is_error=True
    )


@server.call_tool()
async def get_cross_reference_mapping(provision_id: str) -> ToolResult:
    """
    Get cross-references between LCCP, ISO 27001, and RTS
    
    Args:
        provision_id: LCCP provision ID (e.g., "3.2.11")
    
    Returns:
        Supporting ISO 27001 controls and RTS specifications
    """
    references = get_cross_references(provision_id, "lccp")
    
    output = f"Cross-Reference Mapping for LCCP {provision_id}:\n\n"
    output += json.dumps(references, indent=2)
    
    return ToolResult(
        content=[TextContent(type="text", text=output)],
        is_error=False
    )


@server.call_tool()
async def get_compliance_framework(query_type: str = "overview") -> ToolResult:
    """
    Get framework relationship and integration guidance
    
    Args:
        query_type: "overview", "hierarchy", "integration_flow", or "gap_resolution"
    
    Returns:
        Framework relationship information
    """
    framework_doc = documents["indexes"].get("framework-relationship-documentation-lccp-iso27001-rts", {})
    
    if not framework_doc:
        return ToolResult(
            content=[TextContent(type="text", text="Framework documentation not available")],
            is_error=True
        )
    
    if query_type == "overview":
        return ToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps(framework_doc.get("executive_summary", {}), indent=2)
            )],
            is_error=False
        )
    elif query_type == "hierarchy":
        return ToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps(framework_doc.get("framework_hierarchy_and_relationships", {}), indent=2)
            )],
            is_error=False
        )
    else:
        return ToolResult(
            content=[TextContent(type="text", text="Framework documentation available")],
            is_error=False
        )


@server.call_tool()
async def query_by_license(license_type: str) -> ToolResult:
    """
    Get all applicable provisions for a specific license type
    
    Args:
        license_type: e.g., "remote_casino", "remote_betting", "adult_gaming_centre"
    
    Returns:
        List of applicable LCCP provisions
    """
    result = query_by_license_type(license_type)
    
    return ToolResult(
        content=[TextContent(type="text", text=json.dumps(result, indent=2))],
        is_error=False
    )


@server.call_tool()
async def verify_compliance(requirement_area: str) -> ToolResult:
    """
    Get compliance verification checklist for a specific area
    
    Args:
        requirement_area: e.g., "customer_funds", "age_verification", "self_exclusion", "rng_fairness"
    
    Returns:
        Compliance verification steps across all three frameworks
    """
    framework_doc = documents["indexes"].get("framework-relationship-documentation-lccp-iso27001-rts", {})
    matrix = framework_doc.get("compliance_verification_matrix", {})
    
    verification_checks = matrix.get("verification_approach", [])
    
    for check in verification_checks:
        if requirement_area.lower() in check.get("requirement", "").lower():
            return ToolResult(
                content=[TextContent(type="text", text=json.dumps(check, indent=2))],
                is_error=False
            )
    
    return ToolResult(
        content=[TextContent(type="text", text=f"No verification checks found for {requirement_area}")],
        is_error=True
    )


# Register tools
@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="search_regulations",
            description="Search across all regulatory documents (LCCP, ISO 27001, RTS) using natural language",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "framework": {"type": "string", "description": "Optional framework filter (lccp, iso27001, rts)"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_provision_details",
            description="Get detailed information about a specific provision",
            inputSchema={
                "type": "object",
                "properties": {
                    "provision_id": {"type": "string", "description": "Provision ID"},
                    "framework": {"type": "string", "description": "Framework (lccp, iso27001, rts)"}
                },
                "required": ["provision_id", "framework"]
            }
        ),
        Tool(
            name="get_cross_reference_mapping",
            description="Get cross-references between LCCP, ISO 27001, and RTS",
            inputSchema={
                "type": "object",
                "properties": {
                    "provision_id": {"type": "string", "description": "LCCP provision ID"}
                },
                "required": ["provision_id"]
            }
        ),
        Tool(
            name="get_compliance_framework",
            description="Get framework relationship and integration guidance",
            inputSchema={
                "type": "object",
                "properties": {
                    "query_type": {"type": "string", "description": "overview, hierarchy, integration_flow"}
                }
            }
        ),
        Tool(
            name="query_by_license",
            description="Get all applicable provisions for a license type",
            inputSchema={
                "type": "object",
                "properties": {
                    "license_type": {"type": "string", "description": "License type"}
                },
                "required": ["license_type"]
            }
        ),
        Tool(
            name="verify_compliance",
            description="Get compliance verification checklist",
            inputSchema={
                "type": "object",
                "properties": {
                    "requirement_area": {"type": "string", "description": "Compliance area to verify"}
                },
                "required": ["requirement_area"]
            }
        )
    ]


# Main initialization
if __name__ == "__main__":
    # Load documents on startup
    load_documents()
    
    # Start MCP server
    print("Starting MCP server on stdio...")
    mcp.server.stdio.run(server)