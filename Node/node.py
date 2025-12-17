'''
Script for creating a storage node on TNet to help store video and data files from UNet
v0.0.1

Run this script to turn your device into a node
'''
import time
import json
import sqlite3
import threading
import shutil
from typing import Dict, Set
import ipfshttpclient
import subprocess


# IPFS
ipfs = ipfshttpclient.connect("/ip4/127.0.0.1/tcp/5001")

# CONFIG
PUBSUB_TOPIC = "tnet-gossip"
ANNOUNCE_INTERVAL = 30
NODE_ID = ipfs.id()["ID"]
TARGET_REPLICAS = 3
MAX_STORAGE_GB = 100  # user-defined allocation
NODE_TIMEOUT = 120

# DATABASE
conn = sqlite3.connect("node.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS nodes (
    node_id TEXT PRIMARY KEY,
    free_gb REAL,
    last_seen INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS cids (
    cid TEXT PRIMARY KEY,
    size_gb REAL
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS replicas (
    cid TEXT,
    node_id TEXT,
    PRIMARY KEY (cid, node_id)
)
""")

conn.commit()

# UTILS
def now():
    return int(time.time())

def free_disk_gb():
    total, used, free = shutil.disk_usage("/")
    return free / (1024 ** 3)

def used_storage_gb():
    total = 0
    pins = ipfs.pin.ls(type="recursive")["Keys"]
    for cid in pins:
        try:
            stat = ipfs.object.stat(cid)
            total += stat["CumulativeSize"] / (1024 ** 3)
        except:
            pass
    return total

def available_storage():
    return min(free_disk_gb(), MAX_STORAGE_GB - used_storage_gb())

# HELPER
def pubsub_publish(message: dict):
    try:
        subprocess.run(
            ["ipfs", "pubsub", "pub", PUBSUB_TOPIC, json.dumps(message)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        print("[PUBSUB] publish failed", e)

def pubsub_subscribe():
    proc = subprocess.Popen(
        ["ipfs", "pubsub", "sub", PUBSUB_TOPIC],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True
    )

    for line in proc.stdout:
        try:
            msg = json.loads(line.strip())
            handle_gossip(msg)
        except:
            pass


# GOSSIP
def gossip_announce():
    while True:
        message = {
            "type": "node_announce",
            "node_id": NODE_ID,
            "free_gb": available_storage(),
            "cids": list(get_local_cids()),
            "time": now()
        }

        pubsub_publish(message)
        time.sleep(ANNOUNCE_INTERVAL)

def handle_gossip(msg):
    if msg.get("type") != "node_announce":
        return
    if msg.get("node_id") == NODE_ID:
        return

    cur.execute("""
        INSERT OR REPLACE INTO nodes VALUES (?, ?, ?)
    """, (msg["node_id"], msg["free_gb"], now()))

    for cid in msg.get("cids", []):
        cur.execute("INSERT OR IGNORE INTO cids VALUES (?, ?)", (cid, 0))
        cur.execute("INSERT OR IGNORE INTO replicas VALUES (?, ?)", (cid, msg["node_id"]))

    conn.commit()



# DATA PLANE
def get_local_cids() -> Set[str]:
    pins = ipfs.pin.ls(type="recursive")
    return set(pins["Keys"].keys())

def pin_cid(cid):
    print(f"[PIN] {cid}")
    ipfs.pin.add(cid)
    cur.execute("INSERT OR IGNORE INTO replicas VALUES (?, ?)", (cid, NODE_ID))
    conn.commit()

def enforce_replication():
    while True:
        cur.execute("SELECT cid FROM cids")
        for (cid,) in cur.fetchall():
            cur.execute("SELECT COUNT(*) FROM replicas WHERE cid=?", (cid,))
            replicas = cur.fetchone()[0]

            if replicas < TARGET_REPLICAS:
                if available_storage() > 0:
                    pin_cid(cid)

        time.sleep(60)

# HEALTH
def prune_dead_nodes():
    while True:
        cutoff = now() - NODE_TIMEOUT
        cur.execute("DELETE FROM nodes WHERE last_seen < ?", (cutoff,))
        cur.execute("""
            DELETE FROM replicas
            WHERE node_id NOT IN (SELECT node_id FROM nodes)
        """)
        conn.commit()
        time.sleep(60)

# START
print(f"UNet node started: {NODE_ID}")

threading.Thread(target=gossip_announce, daemon=True).start()
threading.Thread(target=pubsub_subscribe, daemon=True).start()
threading.Thread(target=enforce_replication, daemon=True).start()
threading.Thread(target=prune_dead_nodes, daemon=True).start()

#keep process alive
while True:
    time.sleep(3600)
