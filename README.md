<img width="512" height="512" alt="UNet" src="https://github.com/user-attachments/assets/bd2f869a-6f66-41c8-a19b-26e9a96af382" /> <br />
The **"Terminus Network"** is an IPFS/IPNS pinning network for [UNet](https://github.com/Tyson-Shannon/UNet) <br />

## Goal
This code will allow users to turn their computers into nodes for hosting UNet content.

## Setup
You should have python and [ipfs](https://docs.ipfs.tech/install/command-line/#install-official-binary-distributions) installed. <br />

Set up ipfs PUBSUB (comonly not enabled by default, only need to run this once)
```
ipfs config --json Pubsub.Enabled true
```
then run your ipfs daemon.
```
ipfs daemon
```
then run the node.py file.