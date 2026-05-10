"""
Neo4j Service — graph database operations for claim relationships.

Falls back to in-memory storage if NEO4J_URI is not configured.
"""

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class ClaimNode:
    """Represents a claim node in the graph."""
    id: str
    text: str
    confidence: float = 0.5
    entities: List[str] = field(default_factory=list)
    source_doc: str = ""
    node_type: str = "claim"


@dataclass
class ClaimRelationship:
    """Represents a relationship between two claims."""
    source_id: str
    target_id: str
    rel_type: str  # supports, contradicts, neutral_to
    confidence: float = 0.5
    evidence: str = ""


class InMemoryGraphStore:
    """Fallback graph store when Neo4j is not configured."""

    def __init__(self) -> None:
        self._nodes: Dict[str, ClaimNode] = {}
        self._relationships: List[ClaimRelationship] = []

    async def store_claim_node(self, node: ClaimNode) -> str:
        """Store a claim node. Returns the node ID."""
        self._nodes[node.id] = node
        return node.id

    async def store_relationship(self, rel: ClaimRelationship) -> None:
        """Store a relationship between two claims."""
        self._relationships.append(rel)

    async def get_graph_data(self) -> Dict[str, Any]:
        """Return all nodes and edges for visualization."""
        nodes = []
        for n in self._nodes.values():
            nodes.append({
                "id": n.id,
                "label": n.text[:50] + ("..." if len(n.text) > 50 else ""),
                "confidence": n.confidence,
                "type": n.node_type,
            })
        edges = []
        for r in self._relationships:
            edges.append({
                "source": r.source_id,
                "target": r.target_id,
                "relationship": r.rel_type,
                "weight": r.confidence,
            })
        return {"nodes": nodes, "edges": edges}

    async def get_claim_relationships(self, claim_id: str) -> List[Dict]:
        """Get all relationships for a specific claim."""
        return [
            {"source": r.source_id, "target": r.target_id,
             "type": r.rel_type, "confidence": r.confidence}
            for r in self._relationships
            if r.source_id == claim_id or r.target_id == claim_id
        ]

    async def close(self) -> None:
        """No-op for in-memory store."""
        pass

    def stats(self) -> Dict[str, Any]:
        return {"nodes": len(self._nodes), "relationships": len(self._relationships),
                "store_type": "in-memory"}


class Neo4jGraphStore:
    """Production graph store using Neo4j Aura."""

    def __init__(self) -> None:
        self._driver = None
        self._initialized = False

    async def init(self) -> None:
        """Connect to Neo4j and create constraints."""
        if self._initialized:
            # Verify the connection is still valid for this event loop
            try:
                async with self._driver.session() as session:
                    await session.run("RETURN 1")
                return
            except RuntimeError:
                # Event loop mismatch — need to reinitialize
                logger.warning("Neo4j driver bound to different event loop, reinitializing...")
                self._initialized = False
                self._driver = None

        settings = get_settings()
        from neo4j import AsyncGraphDatabase
        self._driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        # Verify connectivity
        try:
            async with self._driver.session() as session:
                await session.run("RETURN 1")
            # Create constraints
            async with self._driver.session() as session:
                await session.run(
                    "CREATE CONSTRAINT claim_id IF NOT EXISTS "
                    "FOR (c:Claim) REQUIRE c.id IS UNIQUE"
                )
            self._initialized = True
            logger.info("Neo4j connected at %s", settings.neo4j_uri)
        except Exception as exc:
            logger.error("Neo4j connection failed: %s", exc)
            raise

    async def store_claim_node(self, node: ClaimNode) -> str:
        """Store a claim node in Neo4j."""
        await self.init()
        async with self._driver.session() as session:
            await session.run(
                "MERGE (c:Claim {id: $id}) "
                "SET c.text = $text, c.confidence = $confidence, "
                "c.entities = $entities, c.source_doc = $source_doc, "
                "c.node_type = $node_type",
                id=node.id, text=node.text, confidence=node.confidence,
                entities=node.entities, source_doc=node.source_doc,
                node_type=node.node_type,
            )
        return node.id

    async def store_relationship(self, rel: ClaimRelationship) -> None:
        """Store a relationship between two claim nodes."""
        await self.init()
        # Map relationship types to Neo4j relationship labels
        rel_label_map = {
            "supports": "SUPPORTS",
            "contradicts": "CONTRADICTS",
            "neutral_to": "NEUTRAL_TO",
        }
        label = rel_label_map.get(rel.rel_type, "RELATED_TO")
        async with self._driver.session() as session:
            await session.run(
                f"MATCH (a:Claim {{id: $source_id}}) "
                f"MATCH (b:Claim {{id: $target_id}}) "
                f"MERGE (a)-[r:{label}]->(b) "
                f"SET r.confidence = $confidence, r.evidence = $evidence",
                source_id=rel.source_id, target_id=rel.target_id,
                confidence=rel.confidence, evidence=rel.evidence,
            )

    async def get_graph_data(self) -> Dict[str, Any]:
        """Return all nodes and edges for visualization."""
        await self.init()
        nodes = []
        edges = []
        async with self._driver.session() as session:
            # Get all claim nodes
            result = await session.run("MATCH (c:Claim) RETURN c")
            async for record in result:
                c = record["c"]
                text = c.get("text", "")
                nodes.append({
                    "id": c["id"],
                    "label": text[:50] + ("..." if len(text) > 50 else ""),
                    "confidence": c.get("confidence", 0.5),
                    "type": c.get("node_type", "claim"),
                })
            # Get all relationships
            result = await session.run(
                "MATCH (a:Claim)-[r]->(b:Claim) "
                "RETURN a.id AS source, b.id AS target, type(r) AS rel_type, "
                "r.confidence AS confidence"
            )
            async for record in result:
                edges.append({
                    "source": record["source"],
                    "target": record["target"],
                    "relationship": record["rel_type"].lower(),
                    "weight": record.get("confidence", 0.5),
                })
        return {"nodes": nodes, "edges": edges}

    async def get_claim_relationships(self, claim_id: str) -> List[Dict]:
        """Get all relationships for a specific claim."""
        await self.init()
        results = []
        async with self._driver.session() as session:
            result = await session.run(
                "MATCH (a:Claim {id: $id})-[r]-(b:Claim) "
                "RETURN a.id AS source, b.id AS target, type(r) AS rel_type, "
                "r.confidence AS confidence",
                id=claim_id,
            )
            async for record in result:
                results.append({
                    "source": record["source"], "target": record["target"],
                    "type": record["rel_type"].lower(),
                    "confidence": record.get("confidence", 0.5),
                })
        return results

    async def close(self) -> None:
        """Close the Neo4j driver."""
        if self._driver:
            await self._driver.close()
            logger.info("Neo4j connection closed.")

    def stats(self) -> Dict[str, Any]:
        return {"store_type": "neo4j", "connected": self._initialized}


# ── Factory / Singleton ──────────────────────────────────────────────────

_store: Optional[Any] = None


def get_graph_store():
    """Get the active graph store (Neo4j or in-memory fallback)."""
    global _store
    if _store is not None:
        return _store
    settings = get_settings()
    if settings.neo4j_configured:
        logger.info("Using Neo4j graph store.")
        _store = Neo4jGraphStore()
    else:
        logger.info("Neo4j not configured — using in-memory graph store.")
        _store = InMemoryGraphStore()
    return _store
