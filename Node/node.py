'''
Script for creating a storage node on TNet to help store video and data files from UNet
v0.0.1

Run this script to turn your device into a node
'''
import time
import argparse
import requests
import ipfshttpclient
import shutil

#Link depends on registry your communicating with. If default is blocked or down try different registry node.
REGISTRY = "https://registry.universal-network.org" #default-https://registry.universal-network.org
INTERVAL = 30

ipfs = ipfshttpclient.connect()

def used_gb():
    return shutil.disk_usage("/").used // (1024 ** 3)

class Node:
    def __init__(self, storage_gb, api_url):
        self.storage_gb = storage_gb
        self.api_url = api_url
        self.node_id = None

    #declare existence to network
    def register(self):
        r = requests.post(
            f"{REGISTRY}/register",
            json={"storage_gb": self.storage_gb, "api_url": self.api_url}
        )
        self.node_id = r.json()["node_id"]
        print(f"[+] Registered as {self.node_id}")

    #declare continued existence to network
    def heartbeat(self):
        pinned = ipfs.pin.ls(type="recursive")["Keys"].keys()

        r = requests.post(
            f"{REGISTRY}/heartbeat/{self.node_id}",
            json={
                "pinned_cids": list(pinned),
                "used_gb": used_gb()
            }
        )

        for cid in r.json().get("assign", []):
            print(f"[PIN] {cid}")
            ipfs.pin.add(cid)

    #exist
    def run(self):
        self.register()
        while True:
            try:
                self.heartbeat()
            except Exception as e:
                print("Error:", e)
            time.sleep(INTERVAL)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--storage", type=int, required=True)
    parser.add_argument("--api-url", required=True)
    args = parser.parse_args()

    Node(args.storage, args.api_url).run()
