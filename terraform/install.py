import os
import json
import paramiko
from tempfile import TemporaryFile
import time

httpserver = '10.0.0.26'
image_dir = '/var/lib/rancher/k3s/agent/images'
image_file = 'k3s-airgap-images-amd64.tar'


def generate_plan(direc, args):
    plan = open("%s/k3s.tf" % (direc), mode='w')
    plan.write("""
    provider "openstack" {
        user_name   = "%s"
        tenant_name = "%s"
        password    = "%s"
        auth_url    = "http://public.cloud.sail:5000/v3"
        region      = "RegionOne"
    }

    """ % (args['user'], args['project'], args['password']))

    # key
    plan.write("""
    resource "openstack_compute_keypair_v2" "k3s" {
        name = "k3s"
    }
    """)

    # master
    plan.write("""
    resource "openstack_compute_instance_v2" "k3s-master" {
        name            = "k3s-master"
        image_name        = "ubuntu-x86_64-16.04"
        flavor_name       = "m1.medium"
        key_pair        = "k3s"
        security_groups = ["default"]

        network {
            name = "demo-net"
        }
        depends_on = [openstack_compute_keypair_v2.k3s]
    }
    """)
    # slave
    for slave in range(args['slaves']):
        plan.write("""
        resource "openstack_compute_instance_v2" "k3s-slave-%d" {
            name            = "k3s-slave-%d"
            image_name        = "ubuntu-x86_64-16.04"
            flavor_name       = "m1.medium"
            key_pair        = "k3s"
            security_groups = ["default"]

            network {
                name = "demo-net"
            }
            depends_on = [openstack_compute_keypair_v2.k3s]
        }
        """ % (slave, slave))


def execute(direc):
    os.system("cd %s; terraform apply -auto-approve" % (direc))


def install_master(ip, private_key):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=ip, port=22, username='ubuntu', pkey=private_key)

    stdin, stdout, stderr = client.exec_command(
        'sudo mkdir -p %s' % (image_dir)
        )
    print(stdout.read())
    stdin, stdout, stderr = client.exec_command(
        'sudo wget http://%s/%s -O %s/%s; sudo wget http://%s/k3s -O /usr/local/bin/k3s; sudo chmod 700 /usr/local/bin/k3s'
        % (httpserver, image_file, image_dir, image_file, httpserver)
        )
    print(stdout.read())
    stdin, stdout, stderr = client.exec_command(
        'curl -sfL http://%s/get-k3s | sudo INSTALL_K3S_SKIP_DOWNLOAD=true sh -'
        % (httpserver)
        )

    print(stdout.read())
    stdin, stdout, stderr = client.exec_command(
        'sudo cat /var/lib/rancher/k3s/server/node-token'
        )

    output = stdout.read()
    print(output)
    token = str(output, encoding='utf8').strip()
    client.close()
    return token


def install_slave(ip, private_key, name, master_ip, token):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=ip, port=22, username='ubuntu', pkey=private_key)

    stdin, stdout, stderr = client.exec_command(
        'sudo mkdir -p %s' % (image_dir)
        )
    print(stdout.read())
    stdin, stdout, stderr = client.exec_command(
        'sudo wget http://%s/%s -O %s/%s; sudo wget http://%s/k3s -O /usr/local/bin/k3s; sudo chmod 700 /usr/local/bin/k3s'
        % (httpserver, image_file, image_dir, image_file, httpserver)
        )

    print(stdout.read())
    print(master_ip)
    print(token)
    print(name)
    command = 'curl -sfL http://%s/get-k3s | sudo K3S_NODE_NAME=%s K3S_URL=https://%s:6443 K3S_TOKEN=%s INSTALL_K3S_SKIP_DOWNLOAD=true sh -' % (httpserver, name, master_ip, token)
    print(command)
    stdin, stdout, stderr = client.exec_command(command)
    print(stdout.read())

    client.close()
    return ""


def install(direc):
    state = getstate(direc)
    for resource in state['values']['root_module']['resources']:
        if resource['address'] == "openstack_compute_keypair_v2.k3s":
            private_key_file = TemporaryFile('w+')
            pkey = resource['values']['private_key']
            private_key_file.write(resource['values']['private_key'])
            private_key_file.seek(0)
            private_key = paramiko.RSAKey.from_private_key(private_key_file)
            break

    token = ""
    print("install master")
    for resource in state['values']['root_module']['resources']:
        print(resource['address'])
        if resource['address'] == "openstack_compute_instance_v2.k3s-master":
            token = install_master(resource['values']['access_ip_v4'], private_key)
            master = resource['values']
            break

    for resource in state['values']['root_module']['resources']:
        if "openstack_compute_instance_v2.k3s-slave" in resource['address']:
            install_slave(resource['values']['access_ip_v4'], private_key, resource['values']['name'], master['access_ip_v4'], token)

    return pkey

def provider(direc):
    os.system("cd %s; cp -r /home/ubuntu/.terraform ." % (direc))


def destroy(direc):
    os.system("cd %s; terraform destroy -auto-approve" % (direc))

def getstate(direc):
    return json.loads(os.popen("cd %s; terraform show -json" % (direc)).read())

def mkdir(path):
    folder = os.path.exists(path)
    if not folder:
        os.makedirs(path)


def oneLine(direc, args):
    mkdir(direc)
    generate_plan(direc, args)
    provider(direc)
    # destroy(direc)
    execute(direc)
    time.sleep(30)
    return install(direc)


if __name__ == "__main__":
    args = {
        'user': '123',
        'project': '123',
        'password': '123',
        'slaves': 1
    }
    direc = "%s/%s/%s" % (args['user'], args['password'], args['project'])
    oneLine(direc, args)
