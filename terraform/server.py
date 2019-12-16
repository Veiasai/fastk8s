from flask import Flask, request, abort, send_file
import sys
from install import oneLine, getstate
from tempfile import TemporaryFile
from io import BytesIO

app = Flask(__name__)


@app.route('/install/<user>/<password>/<project>/<node>', methods=['GET'])
def install(user, password, project, node):
    args = {
        'user': user,
        'project': project,
        'password': password,
        'slaves': int(node)
    }
    direc = "/home/ubuntu/terraform/%s/%s/%s" % (args['user'], args['password'], args['project'])
    private_key = oneLine(direc, args)
    private_key_file = BytesIO()
    pkey = bytes(private_key, encoding='utf8')
    private_key_file.write(pkey)
    private_key_file.seek(0)

    return send_file(private_key_file, as_attachment=True,
                     attachment_filename='id_rsa', mimetype = 'text')

@app.route('/key/<user>/<password>/<project>', methods=['GET'])
def key(user, password, project):
    args = {
        'user': user,
        'project': project,
        'password': password
    }
    direc = "/home/ubuntu/terraform/%s/%s/%s" % (args['user'], args['password'], args['project'])

    for resource in getstate(direc)['values']['root_module']['resources']:
        if resource['address'] == "openstack_compute_keypair_v2.k3s":
            private_key_file = BytesIO()
            pkey = bytes(resource['values']['private_key'], encoding='utf8')
            private_key_file.write(pkey)
            private_key_file.seek(0)

    return send_file(private_key_file, as_attachment=True,
                     attachment_filename='id_rsa', mimetype = 'text')

if __name__ == '__main__':
    app.run(host='0.0.0.0')