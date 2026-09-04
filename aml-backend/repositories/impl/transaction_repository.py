"""
Transaction Repository Implementation - MongoDB-based transaction operations

Repository for transaction activity and network analysis using the transactionsv2 collection.
Leverages existing indexes for efficient queries.
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import DESCENDING

from models.core.transaction import (
    TransactionActivity,
    TransactionNetwork,
    TransactionNetworkNode,
    TransactionNetworkEdge,
    TransactionActivityResponse
)


class TransactionRepository:
    """MongoDB transaction repository implementation"""
    
    def __init__(self, transactions_collection: AsyncIOMotorCollection):
        self.transactions_collection = transactions_collection
    
    async def get_entity_transactions(
        self,
        entity_id: str,
        limit: int = 50,
        skip: int = 0
    ) -> TransactionActivityResponse:
        """Get transaction activity for entity using existing indexes"""
        
        # Build aggregation pipeline to get transactions with counterparty info
        pipeline = [
            # Match transactions involving this entity (uses compound indexes)
            {
                "$match": {
                    "$or": [
                        {"fromEntityId": entity_id},
                        {"toEntityId": entity_id}
                    ]
                }
            },
            
            # Add computed fields for direction and counterparty
            {
                "$addFields": {
                    "computed_direction": {
                        "$cond": [
                            {"$eq": ["$fromEntityId", entity_id]},
                            "sent",
                            "received"
                        ]
                    },
                    "computed_counterparty_id": {
                        "$cond": [
                            {"$eq": ["$fromEntityId", entity_id]},
                            "$toEntityId",
                            "$fromEntityId"
                        ]
                    }
                }
            },
            
            # Sort by timestamp descending (uses timestamp index)
            {"$sort": {"timestamp": -1}},
            
            # Pagination
            {"$skip": skip},
            {"$limit": limit}
        ]
        
        # Execute aggregation
        cursor = self.transactions_collection.aggregate(pipeline)
        transactions_data = await cursor.to_list(length=None)
        
        # Get total count for pagination
        count_pipeline = [
            {
                "$match": {
                    "$or": [
                        {"fromEntityId": entity_id},
                        {"toEntityId": entity_id}
                    ]
                }
            },
            {"$count": "total"}
        ]
        
        count_result = await self.transactions_collection.aggregate(count_pipeline).to_list(length=1)
        total_count = count_result[0]["total"] if count_result else 0
        
        # Convert to TransactionActivity objects
        activity_list = []
        for txn in transactions_data:
            activity = TransactionActivity(
                transaction_id=txn.get("transactionId", str(txn.get("_id"))),
                counterparty_id=txn.get("computed_counterparty_id", ""),
                counterparty_name=txn.get("counterparty_name", "Unknown"),
                counterparty_type=txn.get("counterparty_type", "Unknown"),
                direction=txn.get("computed_direction", "unknown"),
                amount=txn.get("amount", 0.0),
                currency=txn.get("currency", "USD"),
                transaction_type=txn.get("type", "transfer"),
                payment_method=txn.get("type", "unknown"),
                timestamp=txn.get("timestamp", datetime.utcnow()),
                status=txn.get("status", "completed"),
                channel=txn.get("channel", "unknown"),
                description=txn.get("description", ""),
                risk_score=txn.get("riskScore", 85.0 if txn.get("flagged") else 15.0),
                flagged=txn.get("flagged", False),
                tags=txn.get("tags", [])
            )
            activity_list.append(activity)
        
        return TransactionActivityResponse(
            entity_id=entity_id,
            transactions=activity_list,
            total_count=total_count,
            page_size=limit,
            current_page=(skip // limit) + 1
        )
    
    async def build_transaction_network(
        self,
        entity_id: str,
        max_depth: int = 1
    ) -> TransactionNetwork:
        """Build transaction network using proper entity-based traversal"""
        
        # Step 1: Find entities connected to center entity by depth
        connected_entities = set([entity_id])  # Start with center entity
        
        for depth in range(max_depth):
            # Find entities connected to current level entities
            current_level_entities = list(connected_entities)
            
            # Get transactions involving current level entities
            level_pipeline = [
                {
                    "$match": {
                        "$or": [
                            {"fromEntityId": {"$in": current_level_entities}},
                            {"toEntityId": {"$in": current_level_entities}}
                        ]
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "connected_entities": {
                            "$addToSet": {
                                "$concatArrays": [
                                    ["$fromEntityId"],
                                    ["$toEntityId"]
                                ]
                            }
                        }
                    }
                },
                {
                    "$project": {
                        "all_entities": {
                            "$reduce": {
                                "input": "$connected_entities",
                                "initialValue": [],
                                "in": {"$setUnion": ["$$value", "$$this"]}
                            }
                        }
                    }
                }
            ]
            
            level_result = await self.transactions_collection.aggregate(level_pipeline).to_list(1)
            if level_result:
                new_entities = set(level_result[0].get("all_entities", []))
                connected_entities.update(new_entities)
        
        # Step 2: Get only transactions between entities in our connected set
        network_pipeline = [
            {
                "$match": {
                    "$and": [
                        {"fromEntityId": {"$in": list(connected_entities)}},
                        {"toEntityId": {"$in": list(connected_entities)}}
                    ]
                }
            }
        ]
        
        # Execute network query - only get transactions within our network
        network_cursor = self.transactions_collection.aggregate(network_pipeline)
        all_transactions = await network_cursor.to_list(length=None)
        
        # Step 3: Build nodes (entities) with aggregated metrics
        entity_metrics = {}
        all_entities = set()
        
        # Fetch actual entity names and types
        db = self.transactions_collection.database
        entities_cursor = db.sentinelaiEntities.find(
            {"entityId": {"$in": list(connected_entities)}},
            {"entityId": 1, "name.full": 1, "entityType": 1}
        )
        entity_info = {}
        async for doc in entities_cursor:
            entity_info[doc["entityId"]] = {
                "name": doc.get("name", {}).get("full", "Unknown"),
                "type": doc.get("entityType", "unknown")
            }
            
        for txn in all_transactions:
            from_id = txn.get("fromEntityId")
            to_id = txn.get("toEntityId")
                
            amount = txn.get("amount", 0.0)
            risk_score = txn.get("riskScore", 85.0 if txn.get("flagged") else 15.0)
            
            # Use actual entity names and types
            from_name = entity_info.get(from_id, {}).get("name", "Unknown")
            from_type = entity_info.get(from_id, {}).get("type", "unknown")
            to_name = entity_info.get(to_id, {}).get("name", "Unknown")
            to_type = entity_info.get(to_id, {}).get("type", "unknown")
            
            # Track all entities
            all_entities.add((from_id, from_name, from_type))
            all_entities.add((to_id, to_name, to_type))
            
            # Initialize entity metrics if not exists
            for entity_id, name, entity_type in [(from_id, from_name, from_type),
                                                  (to_id, to_name, to_type)]:
                if entity_id not in entity_metrics:
                    entity_metrics[entity_id] = {
                        "entity_name": name,
                        "entity_type": entity_type,
                        "total_sent": 0.0,
                        "total_received": 0.0,
                        "transaction_count": 0,
                        "risk_scores": []
                    }
            
            # Update sender metrics
            entity_metrics[from_id]["total_sent"] += amount
            entity_metrics[from_id]["transaction_count"] += 1
            entity_metrics[from_id]["risk_scores"].append(risk_score)
            
            # Update receiver metrics
            entity_metrics[to_id]["total_received"] += amount
            entity_metrics[to_id]["transaction_count"] += 1
            entity_metrics[to_id]["risk_scores"].append(risk_score)
        
        # Build network nodes
        nodes = []
        for entity_id, metrics in entity_metrics.items():
            avg_risk = sum(metrics["risk_scores"]) / len(metrics["risk_scores"]) if metrics["risk_scores"] else 0
            
            node = TransactionNetworkNode(
                entity_id=entity_id,
                entity_name=metrics["entity_name"],
                entity_type=metrics["entity_type"],
                total_sent=metrics["total_sent"],
                total_received=metrics["total_received"],
                transaction_count=metrics["transaction_count"],
                avg_risk_score=avg_risk
            )
            nodes.append(node)
        
        # Step 3: Build edges (transaction flows between entities)
        edge_metrics = {}
        
        for txn in all_transactions:
            from_id = txn.get("fromEntityId")
            to_id = txn.get("toEntityId")
                
            edge_key = f"{from_id}->{to_id}"
            
            if edge_key not in edge_metrics:
                edge_metrics[edge_key] = {
                    "from_entity_id": from_id,
                    "to_entity_id": to_id,
                    "transaction_count": 0,
                    "total_amount": 0.0,
                    "amounts": [],
                    "risk_scores": [],
                    "latest_transaction": None,
                    "transaction_types": [],
                    "currency": txn.get("currency", "USD")
                }
            
            metrics = edge_metrics[edge_key]
            metrics["transaction_count"] += 1
            metrics["total_amount"] += txn.get("amount", 0.0)
            metrics["amounts"].append(txn.get("amount", 0.0))
            metrics["risk_scores"].append(txn.get("riskScore", 85.0 if txn.get("flagged") else 15.0))
            metrics["transaction_types"].append(txn.get("type", "transfer"))
            
            # Track latest transaction
            if not metrics["latest_transaction"] or txn["timestamp"] > metrics["latest_transaction"]:
                metrics["latest_transaction"] = txn["timestamp"]
        
        # Build network edges
        edges = []
        for metrics in edge_metrics.values():
            avg_amount = sum(metrics["amounts"]) / len(metrics["amounts"]) if metrics["amounts"] else 0
            avg_risk = sum(metrics["risk_scores"]) / len(metrics["risk_scores"]) if metrics["risk_scores"] else 0
            
            # Find most common transaction type
            type_counts = {}
            for txn_type in metrics["transaction_types"]:
                type_counts[txn_type] = type_counts.get(txn_type, 0) + 1
            primary_type = max(type_counts.keys(), key=type_counts.get) if type_counts else "unknown"
            
            edge = TransactionNetworkEdge(
                from_entity_id=metrics["from_entity_id"],
                to_entity_id=metrics["to_entity_id"],
                transaction_count=metrics["transaction_count"],
                total_amount=metrics["total_amount"],
                avg_amount=avg_amount,
                currency=metrics["currency"],
                avg_risk_score=avg_risk,
                latest_transaction=metrics["latest_transaction"],
                primary_transaction_type=primary_type
            )
            edges.append(edge)
        
        # Calculate network summary with distinction between total and center entity transactions
        total_transactions_in_network = len(all_transactions)
        total_volume_in_network = sum(txn.get("amount", 0.0) for txn in all_transactions)
        
        # Calculate transactions involving center entity only (for comparison with table)
        center_entity_transactions = [
            txn for txn in all_transactions 
            if txn.get("entityId") == entity_id or txn.get("counterpartyEntityId") == entity_id
        ]
        center_entity_transaction_count = len(center_entity_transactions)
        center_entity_volume = sum(txn.get("amount", 0.0) for txn in center_entity_transactions)
        
        return TransactionNetwork(
            center_entity_id=entity_id,
            nodes=nodes,
            edges=edges,
            total_transactions=total_transactions_in_network,
            total_volume=total_volume_in_network,
            center_entity_transaction_count=center_entity_transaction_count,
            center_entity_volume=center_entity_volume,
            max_depth=max_depth
        )