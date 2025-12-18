# TNet Roadmap

## Current State
- ✅ Basic code for creating an ipfs pinning node
- ✅ Fixed python library ipfshttpclient version match error by switching to subprocesses instead
- ✅ Fixed PUBSUB publish failed error (need to enable ipfs PUBSUB before running daemon)
- ✅ Node's can pin data, discover each other, gossip, ensure replication of data, and remove dead nodes
- ❌ Integrate upload and CID creation from web app

✅-DONE, ⚠️-BUG, ❌-NOT DONE
## Short-Term Goals
- [ ] Split critical site and video replication rules
- [ ] Re-Pin lost data when a node goes offline
- [ ] Remove data from node that died and revived
- [ ] Rate limiting
- [ ] Malicious node detection


## Long-Term Goals
- [ ] Graceful shutdown
- [ ] Incentives - user tech debt feature on UNet
- [ ] Dashboards for system health and information
- [ ] Conflict resolution logic
- [ ] Network-wide storage totals