from flask import Flask, request, abort, send_file
import sys
from install import oneLine
from tempfile import TemporaryFile

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
    private_key_file = TemporaryFile('w+')
    private_key_file.write(private_key)
    private_key_file.seek(0)
    return send_file(private_key_file)

if __name__ == '__main__':
    app.run(host='0.0.0.0')