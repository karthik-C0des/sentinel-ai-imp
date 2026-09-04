import os
from pprint import pprint
from services.agents.nodes.temporal_analyst import temporal_analyst_node

state = {
    "gathered_data": {
        "entity_profile": {
            "entityId": "ENT-DEMO-006"
        }
    }
}
result = temporal_analyst_node(state)
print("SUCCESS!")
pprint(result["temporal_analysis"])
