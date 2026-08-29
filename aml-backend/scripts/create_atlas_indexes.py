import asyncio
import os
import json
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def create_indexes():
    c = AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    db = c[os.getenv('DB_NAME')]
    coll = db['threatsightEntities']
    
    print("Creating entity_resolution_search...")
    try:
        await coll.create_search_index({
            "name": "entity_resolution_search",
            "definition": {
              "mappings": {
                "dynamic": False,
                "fields": {
                  "name": {
                    "type": "document",
                    "fields": {
                      "full": [
                        {"type": "string", "analyzer": "lucene.standard"},
                        {"type": "autocomplete", "tokenization": "edgeGram", "minGrams": 2, "maxGrams": 15, "foldDiacritics": True}
                      ],
                      "aliases": {"type": "string", "analyzer": "lucene.standard"}
                    }
                  },
                  "entityType": {"type": "stringFacet"},
                  "nationality": {"type": "stringFacet"},
                  "residency": {"type": "stringFacet"},
                  "jurisdictionOfIncorporation": {"type": "stringFacet"},
                  "riskAssessment": {
                    "type": "document",
                    "fields": {
                      "overall": {
                        "type": "document",
                        "fields": {
                          "level": {"type": "stringFacet"},
                          "score": {"type": "numberFacet"}
                        }
                      }
                    }
                  },
                  "customerInfo": {
                    "type": "document",
                    "fields": {
                      "businessType": {"type": "stringFacet"}
                    }
                  },
                  "addresses": {
                    "type": "document",
                    "fields": {
                      "structured": {
                        "type": "document",
                        "fields": {
                          "country": {"type": "string", "analyzer": "lucene.keyword"},
                          "city": {"type": "string", "analyzer": "lucene.keyword"}
                        }
                      },
                      "full": {"type": "string", "analyzer": "lucene.standard"}
                    }
                  },
                  "identifiers": {
                    "type": "document",
                    "fields": {
                      "type": {"type": "string", "analyzer": "lucene.keyword"},
                      "value": {"type": "string", "analyzer": "lucene.standard"}
                    }
                  },
                  "scenarioKey": {"type": "string", "analyzer": "lucene.keyword"}
                }
              }
            }
        })
        print("Created entity_resolution_search index.")
    except Exception as e:
        print("Error creating entity_resolution_search:", e)

    print("Creating entity_vector_search_index...")
    try:
        await coll.create_search_index({
            "name": "entity_vector_search_index",
            "type": "vectorSearch",
            "definition": {
                "fields": [
                    {
                        "type": "vector",
                        "path": "embedding",
                        "numDimensions": 1536,
                        "similarity": "cosine"
                    }
                ]
            }
        })
        print("Created entity_vector_search_index index.")
    except Exception as e:
        print("Error creating entity_vector_search_index:", e)
        
    print("Creating entity_identifier_vector_index...")
    try:
        await coll.create_search_index({
            "name": "entity_identifier_vector_index",
            "type": "vectorSearch",
            "definition": {
                "fields": [
                    {
                        "type": "vector",
                        "path": "identifierEmbedding",
                        "numDimensions": 1536,
                        "similarity": "cosine"
                    }
                ]
            }
        })
        print("Created entity_identifier_vector_index index.")
    except Exception as e:
        print("Error creating entity_identifier_vector_index:", e)

    print("Creating entity_behavioral_vector_index...")
    try:
        await coll.create_search_index({
            "name": "entity_behavioral_vector_index",
            "type": "vectorSearch",
            "definition": {
                "fields": [
                    {
                        "type": "vector",
                        "path": "behavioralEmbedding",
                        "numDimensions": 1536,
                        "similarity": "cosine"
                    }
                ]
            }
        })
        print("Created entity_behavioral_vector_index index.")
    except Exception as e:
        print("Error creating entity_behavioral_vector_index:", e)

    c.close()

if __name__ == '__main__':
    asyncio.run(create_indexes())
