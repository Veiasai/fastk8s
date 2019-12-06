#!/bin/bash

chmod 777 *.sh

sudo ./k3s-master-install.sh $1

sudo chmod 777 /usr/local/bin/kubectl
sudo chmod 444 /etc/rancher/k3s/k3s.yaml

hostip=`sudo ifconfig ens3 |grep "inet addr"| cut -f 2 -d ":"|cut -f 1 -d " "`
token=`sudo cat /var/lib/rancher/k3s/server/node-token`

while read line
do
scp -o "StrictHostKeyChecking=no" k3s-agent-install.sh ubuntu@${line}:/tmp/
ssh -o "StrictHostKeyChecking=no" ubuntu@${line} "sudo chmod 777 /tmp/k3s-agent-install.sh; sudo /tmp/k3s-agent-install.sh ${1} ${hostip} ${token} ${line}"
done  < inventory