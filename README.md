<img width="512" height="512" alt="UNet" src="https://github.com/user-attachments/assets/bd2f869a-6f66-41c8-a19b-26e9a96af382" /> <br />
The **"Terminus Network"** is an IPFS/IPNS pinning network for [UNet](https://github.com/Tyson-Shannon/UNet) <br />
**See also the [Foundation Node](https://github.com/Tyson-Shannon/Foundation-Node)**

## Goal
This code will allow users to turn their computers into nodes for hosting UNet content.

## The Network
<img width="581" height="570" alt="UNet-TNet drawio" src="https://github.com/user-attachments/assets/cb30c881-00b3-456c-9a45-7a6395e2b8d9" /> <br />

## Setup
You should have python and [ipfs](https://docs.ipfs.tech/install/command-line/#install-official-binary-distributions) installed. <br />

Set up ipfs PUBSUB (comonly not enabled by default, only need to run this once).
```
ipfs config --json Pubsub.Enabled true
```
Then run your ipfs daemon.
```
ipfs daemon
```
Then run the node.py file.
```
python3 node.py
```
You will be prompted to enter the amount of GB to allow your node to use for storage. Enter a value or enter 'inf' to use your full system storage.
```
inf
```
