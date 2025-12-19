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
from typing import Set
import subprocess
import socket

# INTRO
print(r''' 
   0   0
    \ /
0----0----0
    /|\
   0 | 0
     0
    /|\
   0 | 0
     0
    /|\
   0 | 0
     0
Concedo Nulli
''')

# NODE ID
#get ipfs peer id or fallback to host name
def get_node_id():
    try:
        node_id = subprocess.run(
            ["ipfs", "id", "-f=<id>"],
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()
        return node_id
    except Exception as e:
        print("[NODE_ID] Failed, fallback to hostname:", e)
        return socket.gethostname()

# CONFIG
PUBSUB_TOPIC = "tnet-gossip"
ANNOUNCE_INTERVAL = 30
TARGET_REPLICAS = 3
#user-defined storage allocation
MAX_STORAGE_GB = -1
while(MAX_STORAGE_GB <= 0):
    try:
        MAX_STORAGE_GB = float(input("Max gigabytes node can use for storage (positive non zero value, if unsure input 'inf' for system max): "))
    except:
        print("Wrong data type, enter a float\n")
NODE_TIMEOUT = 120
NODE_ID = get_node_id()

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
cur.close()

# UTILS
def now():
    return int(time.time())

def free_disk_gb():
    total, used, free = shutil.disk_usage("/")
    return free / (1024 ** 3)

def run_ipfs_command(cmd: list) -> str:
    """Run an IPFS CLI command and return stdout."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"IPFS command failed: {cmd}\n{result.stderr}")
    return result.stdout.strip()

#gets list of locally stored cids
def get_local_cids() -> Set[str]:
    """Return set of locally pinned CIDs."""
    try:
        output = run_ipfs_command(["ipfs", "pin", "ls", "-t", "recursive", "-q"])
        return set(output.splitlines())
    except:
        return set()

#takes cid and checks if its already pinned returns true or false
def has_cid(cid: str) -> bool:
    return cid in get_local_cids()

def available_storage():
    """Estimate available storage for new pins."""
    used = 0
    for cid in get_local_cids():
        try:
            size_str = run_ipfs_command(["ipfs", "object", "stat", cid, "--size"])
            used += int(size_str) / (1024 ** 3)
        except:
            pass
    return min(free_disk_gb(), MAX_STORAGE_GB - used)

# PUBSUB
def pubsub_publish(message: dict):
    try:
        #convert dict to JSON string
        data = json.dumps(message)
        #send JSON via stdin
        subprocess.run(
            ["ipfs", "pubsub", "pub", PUBSUB_TOPIC, "-"],
            input=data,
            text=True,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        print("[PUBSUB] publish failed:", e)


def pubsub_subscribe(handle_func):
    try:
        proc = subprocess.Popen(
            ["ipfs", "pubsub", "sub", PUBSUB_TOPIC],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
                handle_func(msg)
            except json.JSONDecodeError:
                print("[PUBSUB] failed to decode message:", line)
    except Exception as e:
        print("[PUBSUB] subscribe failed:", e)

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
    cur = conn.cursor()
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
    cur.close()

# DATA PLANE
def pin_cid(cid):
    #if cid already pinned on node skip
    if has_cid(cid):
        return
    #if node storage full skip
    if available_storage() <= 0:
        return
    cur = conn.cursor()
    print(f"[PIN] Healing replica: {cid}")
    try:
        run_ipfs_command(["ipfs", "pin", "add", cid])
        cur.execute(
            "INSERT OR IGNORE INTO replicas VALUES (?, ?)",
            (cid, NODE_ID)
        )
        conn.commit()
        print(f"[PIN] Success: {cid}")
    except Exception as e:
        print("[PIN] failed:", e)
    cur.close()


def enforce_replication():
    while True:
        cur = conn.cursor()
        cur.execute("""
            SELECT c.cid, COUNT(r.node_id) as replica_count
            FROM cids c
            LEFT JOIN replicas r ON c.cid = r.cid
            GROUP BY c.cid
        """)
        for cid, replica_count in cur.fetchall():
            if replica_count < TARGET_REPLICAS:
                if not has_cid(cid):
                    pin_cid(cid)
        cur.close()
        time.sleep(30)


# HEALTH
def prune_dead_nodes():
    while True:
        cur = conn.cursor()
        cutoff = now() - NODE_TIMEOUT
        cur.execute("SELECT node_id FROM nodes WHERE last_seen < ?", (cutoff,))
        dead = [row[0] for row in cur.fetchall()]
        if dead:
            print("[HEALTH] Dead nodes detected:", dead)
        cur.execute("DELETE FROM nodes WHERE last_seen < ?", (cutoff,))
        cur.execute("""
            DELETE FROM replicas
            WHERE node_id NOT IN (SELECT node_id FROM nodes)
        """)
        conn.commit()
        cur.close()
        time.sleep(30)


# START
print(f"TNet node started: {NODE_ID}")

threading.Thread(target=gossip_announce, daemon=True).start()
threading.Thread(target=pubsub_subscribe, args=(handle_gossip,), daemon=True).start()
threading.Thread(target=enforce_replication, daemon=True).start()
threading.Thread(target=prune_dead_nodes, daemon=True).start()

#keep process alive
while True:
    time.sleep(3600)
