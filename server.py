from flask import Flask, request
from flask_restful import Resource, Api
import requests

app = Flask(__name__)
api = Api(app)

# shows a single todo item and lets you delete a todo item

info = []

class Todo(Resource):
    info = []
    def post(self):
        dataRecieved = request.get_json()
        p_id = dataRecieved['p_ID']
        port = dataRecieved['port']
        pub_key = dataRecieved['publicKey']
        peerInfo = {"p_id": p_id, "port":port, "pub_key": pub_key}
        info.append(peerInfo)
        return "Peer's Registration Succeeds", 201
        
    def get(self):
        return info , 200
        
api.add_resource(Todo, '/peer')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=2000, debug=True)
