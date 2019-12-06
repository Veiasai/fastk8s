#!/bin/bash

dir=~/.spotmore
lock=~/.spotmore/install_lock
imageDir=/var/lib/rancher/k3s/agent/images
imageFile=k3s-airgap-images-amd64.tar

if [ ! -d "$dir" ]; then
    mkdir $dir
fi

{
   flock -e -n 3
    if [ $? -eq 1 ]; then
       echo "somebody has taken lock"
       exit
    fi

    echo "show time"
    # get lock, show time
    if [ ! -d "$imageDir" ]; then
        mkdir -p ${imageDir}
    fi

    wget http://${1}/${imageFile}.sum -O ${imageDir}/${imageFile}.sum
    cd ${imageDir} && sha256sum -c ${imageFile}.sum
    if [ $? -eq 1 ]; then
        wget http://${1}/${imageFile} -O ${imageDir}/k3s-airgap-images-amd64.tar
    fi

    wget http://${1}/k3s.sum -O /usr/local/bin/k3s.sum
    chmod 400 /usr/local/bin/k3s.sum
    cd /usr/local/bin && sha256sum -c k3s.sum
    if [ $? -eq 1 ]; then
        wget http://${1}/k3s -O /usr/local/bin/k3s
        chmod 700 /usr/local/bin/k3s
    fi
    curl -sfL http://${1}/get-k3s | INSTALL_K3S_SKIP_DOWNLOAD=true sh -

    echo "install successfully, sleeping"
    # wait for collecting metrics
    sleep 60

} 3<>$lock
