"""
Graph Router — endpoint for knowledge graph visualization data.

GET /graph-data → Retrieve all claim nodes and relationships
"""

import logging

from fastapi import APIRouter, HTTPException

from app.models import GraphDataResponse, GraphEdge, GraphNode
from app.services.neo4j_service import get_graph_store

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Graph"])


@router.get("/graph-data", response_model=GraphDataResponse)
async def get_graph_data() -> GraphDataResponse:
    """
    Retrieve knowledge graph data for visualization.

    Returns all claim nodes and their relationships (SUPPORTS, CONTRADICTS,
    NEUTRAL_TO) from the graph database.
    """
    try:
        graph = get_graph_store()
        data = await graph.get_graph_data()

        nodes = [
            GraphNode(
                id=n["id"],
                label=n["label"],
                confidence=n.get("confidence", 0.5),
                type=n.get("type", "claim"),
            )
            for n in data.get("nodes", [])
        ]

        edges = [
            GraphEdge(
                source=e["source"],
                target=e["target"],
                relationship=e["relationship"],
                weight=e.get("weight", 0.5),
            )
            for e in data.get("edges", [])
        ]

        return GraphDataResponse(nodes=nodes, edges=edges)

    except Exception as exc:
        logger.error("Failed to retrieve graph data: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve graph data: {str(exc)}"
        )
