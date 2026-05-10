import asyncio
import os
from app.services.neo4j_service import get_graph_store
from app.config import get_settings

async def test_neo4j():
    settings = get_settings()
    print(f"Testing Neo4j connection to {settings.neo4j_uri}...")
    try:
        store = get_graph_store()
        if hasattr(store, 'init'):
            await store.init()
        stats = store.stats()
        print(f"Connection successful! Stats: {stats}")
        
        # Test a simple query
        if hasattr(store, '_driver') and store._driver:
            async with store._driver.session() as session:
                result = await session.run("RETURN 1 as val")
                record = await result.single()
                print(f"Query test (RETURN 1): {record['val']}")
        
        print("Neo4j is working properly.")
    except Exception as e:
        print(f"Neo4j connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_neo4j())
