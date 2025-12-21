# TNet Roadmap

## Current State
- ✅ Basic code for creating an ipfs pinning node
- ✅ Fixed python library ipfshttpclient version match error by switching to subprocesses instead
- ✅ Fixed PUBSUB publish failed error (need to enable ipfs PUBSUB before running daemon)
- ✅ Node's can pin data, discover each other, gossip, ensure replication of data, and remove dead nodes
- ✅ Check if enough storage to pin CID
- ✅ Re-Pin lost data when a node goes offline
- ❌ Only allow authorized data to be pinned from web app (currently anyone can pin anything)
- ❌ Integrate upload and CID creation from web app

✅-DONE, ⚠️-BUG, ❌-NOT DONE
## Short-Term Goals
- [ ] Split critical site and video replication rules
- [ ] Remove data from node that died and revived
- [ ] Single content storage size caps
- [ ] Rate limiting (timestamp windows)
- [ ] Allowed content whitelist
- [ ] Malicious node detection


## Long-Term Goals
- [ ] Graceful shutdown
- [ ] Incentives - user tech debt feature on UNet
- [ ] Dashboards for system health and information
- [ ] Conflict resolution logic
- [ ] Network-wide storage totals