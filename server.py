import time, json
import redis

redis = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

from flask import Flask
from flask import request
app = Flask(__name__)

@app.route("/web/", methods=['GET'])
def get():
    redis_data = str(redis.get("api_key_list"))
    print(redis_data)
    api_key_list = redis_data.split(',')
    quorum_data = ""
    for keys in api_key_list:
        data = str(redis.get(keys)).split(',')
        print(data)
        if data[0] != "None":
            quorum_data = "{}<tr><th>{}</th><th>{}</th><th>{}</th></tr>".format(quorum_data, data[0], data[1], data[2])

    quorum_table = '<table style="width:60%"><tr><th>Online Stake Total</th><th>Peers Stake Total</th><th>Quorum Delta</th>{}</tr></table>'.format(quorum_data)

    peer_data = ""

    for peers in redis.scan_iter("peers:*"):
        print(peers)
        peer_num = 600 - (redis.ttl(peers))
        peer_data = "{}<tr><th>{}</th><th>{}</th></tr>".format(peer_data, peers, peer_num)

    peers_table = '<table style="width:60%"><tr><th>IP</th><th>Age (seconds)</th>{}</tr></table>'.format(peer_data)
    header = '<!DOCTYPE html><html><head><style>table, th, td {border: 1px solid black;}</style></head><body>'
    return "{}<h1>RR Working Group</h1><p>{}</p>{}".format(header, quorum_table, peers_table)

@app.route("/callback/", methods=['POST'])
def post():
    receive_time = time.strftime("%d/%m/%Y %H:%M:%S")
    post_data = request.get_json()
    print(post_data)
    whitelist = redis.get("api_key_whitelist")
    if post_data['api_key'] in whitelist.split(','):
        username = redis.get("api:{}".format(post_data['api_key']))
        print("\n{}".format(redis.get(post_data['api_key'])))

        try:
            redis_data = str(redis.get('api_key_list'))
        except:
            print("Error")
            redis_data = ""

        api_key_list = redis_data.split(',')

        print(api_key_list)
        if post_data['api_key'] not in api_key_list:
            print("Update list")
            result = redis.append("api_key_list", "{},".format(str(post_data['api_key'])))
            print(result)
        else:
            print("Nothing to update")

        data = "{},{},{}".format(post_data['online_stake_total'], post_data['peers_stake_total'], post_data['quorum_delta'])
        redis.set(post_data['api_key'],data)

        peers_list = post_data['peers']
        for peers in peers_list['peers']:
            print(peers)
            redis.append("peers:{}".format(peers), username)
            redis.expire("peers:{}".format(peers), 600)
        return "Success"

    else:
        print("Incorrect api_key")
        return "Error"

#7092
app.run(host='0.0.0.0', port=7092)
