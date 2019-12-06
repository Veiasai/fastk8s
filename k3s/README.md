# Example

``` sh
# on master 10.0.0.50, the 1st parameter is the http server which offers offline package
# on se-cloud, 10.0.0.26 is avaliable
sudo ./k3s-master-install.sh 10.0.0.26

# Get Token
sudo cat /var/lib/rancher/k3s/server/node-token

# on node
sudo ./k3s-agent-install.sh 10.0.0.26 10.0.0.50 token name
```
