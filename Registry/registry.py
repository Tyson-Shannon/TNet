'''
Script for creating a registry node on TNet to organize storage nodes
v0.0.1

functionality for multiple registry nodes will be added later but for now we'll build using 1
'''
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List
import time
import uuid
import json
import ipfshttpclient

app = FastAPI(title="UNet Registry")

ipfs = ipfshttpclient.connect()

#number of nodes video data and such should be stored on
REPLICATION_TARGET = 3
#number of nodes critical data should be stored on
CRITICAL_REPLICATION_TARGET = 30
#when to declare a node as dead
HEARTBEAT_TIMEOUT = 120
#when to snapshot registry info
SNAPSHOT_INTERVAL = 60


# State (MVP: memory)

nodes: Dict[str, dict] = {}
cids: Dict[str, dict] = {}
last_snapshot = 0


# Models

class RegisterNode(BaseModel):
    storage_gb: int
    api_url: str

class Heartbeat(BaseModel):
    pinned_cids: List[str]
    used_gb: int

class AddCID(BaseModel):
    cid: str
    size_gb: float


# Helpers

def now():
    return int(time.time())

def prune_nodes():
    for nid in list(nodes.keys()):
        if now() - nodes[nid]["last_seen"] > HEARTBEAT_TIMEOUT:
            del nodes[nid]

def publish_snapshot():
    global last_snapshot
    if now() - last_snapshot < SNAPSHOT_INTERVAL:
        return

    snapshot = {
        "nodes": nodes,
        "cids": cids,
        "timestamp": now()
    }

    data = json.dumps(snapshot).encode()
    res = ipfs.add_bytes(data)
    last_snapshot = now()

    print(f"[SNAPSHOT] Published to IPFS CID {res}")


# Core Logic

def assign_replicas():
    for cid, info in cids.items():
        current = set(info["nodes"])
        if len(current) >= REPLICATION_TARGET:
            continue

        available = [
            nid for nid, n in nodes.items()
            if nid not in current and n["free_gb"] >= info["size_gb"]
        ]

        for nid in available:
            info["nodes"].append(nid)
            nodes[nid]["assigned"].append(cid)
            if len(info["nodes"]) >= REPLICATION_TARGET:
                break


# API

@app.post("/register")
def register(data: RegisterNode):
    nid = str(uuid.uuid4())
    nodes[nid] = {
        "api": data.api_url,
        "storage_gb": data.storage_gb,
        "used_gb": 0,
        "free_gb": data.storage_gb,
        "assigned": [],
        "last_seen": now()
    }
    return {"node_id": nid}

@app.post("/heartbeat/{nid}")
def heartbeat(nid: str, data: Heartbeat):
    if nid not in nodes:
        return {"error": "unknown node"}

    nodes[nid]["used_gb"] = data.used_gb
    nodes[nid]["free_gb"] = nodes[nid]["storage_gb"] - data.used_gb
    nodes[nid]["last_seen"] = now()

    for cid in data.pinned_cids:
        if cid in cids and nid not in cids[cid]["nodes"]:
            cids[cid]["nodes"].append(nid)

    prune_nodes()
    assign_replicas()
    publish_snapshot()

    return {
        "assign": nodes[nid]["assigned"]
    }

@app.post("/cid")
def add_cid(data: AddCID):
    if data.cid not in cids:
        cids[data.cid] = {
            "size_gb": data.size_gb,
            "nodes": []
        }
    assign_replicas()
    publish_snapshot()
    return {"status": "registered"}

@app.get("/stats")
def stats():
    return {
        "nodes": len(nodes),
        "cids": len(cids),
        "available_gb": sum(n["free_gb"] for n in nodes.values())
    }
