import time, json
import redis
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import hashlib


redis = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
from influxdb import InfluxDBClient
influx_client = InfluxDBClient(host='localhost', port=8086)
influx_client.switch_database('quorum_db')

raw = 1000000000000000000000000000000

from flask import Flask
from flask import request
app = Flask(__name__)

def format_ip(peer):
    split_peers = peer.split(':')
    if split_peers[2] == 'ffff':
        ip_address = split_peers[3]
    else:
        ip_address = ":".join(peer.split(":")[:-1])
        ip_address = ip_address[1:-1]
#    print(ip_address)
    return ip_address

@app.route("/web/")
def get():
    redis_data = str(redis.get("api_key_list"))
    print(redis_data)
    api_key_list = redis_data.split(',')
    quorum_data = ""
    avg_online_stake = 0
    avg_peer_stake = 0
    avg_quorum_delta = 0
    avg_peers = 0
    for keys in api_key_list:
        data = str(redis.get(keys)).split(',')
    #    print(data)
        username = redis.get("api:{}".format(keys))
        client_hash = "None"
        if username != None:
            print(username)
            client_hash = hashlib.sha256(username.encode('utf-8')).hexdigest()[:8]
            print(client_hash)

        if data[0] != "None":
            quorum_data = "{}<tr><th>{}</th><th>{}</th><th>{}</th><th>{}</th><th>{}</th></tr>".format(quorum_data, client_hash, data[0], data[1], data[2], data[3])
#            quorum_data = "{}<tr><th>ID123232323</th><th>{}</th><th>{}</th><th>{}</th><th>{}</th></tr>".format(quorum_data, data[0], data[1], data[2], data[3])
            avg_online_stake += int(data[0])
            avg_peer_stake += int(data[1])
            avg_quorum_delta += int(data[2])
            avg_peers += int(data[3])

    avg_online_stake = avg_online_stake / (len(api_key_list) - 1)
    avg_peer_stake = avg_peer_stake / (len(api_key_list) - 1)
    avg_quorum_delta = avg_quorum_delta / (len(api_key_list) - 1)
    avg_peers = avg_peers / (len(api_key_list) - 1)

    quorum_data = "{}<tr><th>Avg</th><th>{}</th><th>{}</th><th>{}</th><th>{}</th></tr>".format(quorum_data, avg_online_stake, avg_peer_stake, avg_quorum_delta, avg_peers)
    quorum_table = '<table style="width:90%"><tr><th>ID</th><th>Online Stake Total</th><th>Peers Stake Total</th><th>Quorum Delta</th><th>Peers</th>{}</tr></table>'.format(quorum_data)

    peer_data = ""
    count = 0
    total_weight = 0
    for peers in redis.scan_iter("peers:*"):
#        print(peers)
        num_clients = len(str(redis.get(peers)).split(',')) - 1
        perc_clients = (int(num_clients) / (len(api_key_list) - 1)) * 100 
        peer_num = 600 - (redis.ttl(peers))
        peer_data_address = "peer_data:{}".format(peers[6:]).rstrip()
        peer_weight = "None"

        try:
            peer_results = redis.get(peer_data_address)

        except:
            print("Error")

        if peer_results != None:
            if len(peer_results) > 64: 
                print(peer_results)
                peer_data1 = peer_results.split(',')
                peer_weight = peer_data1[1]
                total_weight += int(peer_data1[1])
            else:
                peer_weight = "None"
        else:
            peer_weight = "None"

#        peer_weight = redis.get("peer_data:81.169.174.23")
#        print("{}:{} {}".format(peers, redis.get(peers), peer_weight))
        peer_data = "{}<tr><th>{}</th><th>{}</th><th>{}</th><th>{}</th><th>{}</th></tr>".format(peer_data, peers, peer_num, num_clients, int(perc_clients), peer_weight)
        count += 1

    peers_table = '<p>Number of unique Peers: {}, Total Weight {}</p><table style="width:60%"><tr><th>IP</th><th>Age (seconds)</th><th>Num Clients</th><th>Perc Clients</th><th>Weight</th>{}</tr></table>'.format(count, total_weight, peer_data)
    header = '<!DOCTYPE html><html><head><style>table, th, td {border: 1px solid black;}</style></head><body>'
    return "{}<h1>RR Working Group</h1><p>{}</p>{}".format(header, quorum_table, peers_table)

@app.route("/map")
def map_get():

    G = nx.Graph()
    count = 0
    for peers in redis.scan_iter("peers:*"):
        print("{}:{}".format(peers, redis.get(peers)))
        G.add_node(peers[6:])
        data = str(redis.get(peers))
        try:
            dest = data.split(',')
            for destination in dest:
                if destination != '\n':
                    #count += 1
                    hash_dest = hashlib.sha256(destination.encode('utf-8')).hexdigest()[:8]
                    if hash_dest.upper() not in list(G.nodes):
                        print("Add hash_dest {}".format(hash_dest.upper()))
                        G.add_node(hash_dest.upper())
                    if (peers[6:], hash_dest.upper()) not in list(G.edges):
                        G.add_edge(peers[6:], hash_dest.upper())
        except:
            pass

    # Plot it
    #nx.draw(G, with_labels=True)
    plt.figure(figsize=(56, 56))
    nx.draw(G, with_labels=True, node_size=50, node_color="skyblue", pos=nx.spring_layout(G), linewidths=0, width=0.1, line_color="grey")

    #plt.show()
    plt.savefig('static/foo.png')
    return "<h1>RR Working Group</h1><p><img src='static/foo.png'></p>"

@app.route("/callback/", methods=['POST'])
def post():
    receive_time = time.strftime("%d/%m/%Y %H:%M:%S")
    post_data = request.get_json()
    print("{}".format(request.remote_addr))
#    print(post_data)
    whitelist = redis.get("api_key_whitelist")
    if post_data['api_key'] in whitelist.split(','):
        username = redis.get("api:{}".format(post_data['api_key']))
        print("\n{}".format(redis.get(post_data['api_key'])))
        current_username_list = str(redis.get("peers:{}".format(request.remote_addr))).split(',')
        if username not in current_username_list:
            redis.append("peers:{}".format(request.remote_addr), "{},".format(username))
            redis.expire("peers:{}".format(request.remote_addr), 600)

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

        peers_list = post_data['peers']
        for peers in peers_list['peers']:
#            print(peers)
            split_peers = peers.split(':')
            if split_peers[2] == 'ffff':
                ip_address = split_peers[3][:-1]
            else:
                ip_address = ":".join(peers.split(":")[:-1])
                ip_address = ip_address[1:-1]
            current_username_list = str(redis.get("peers:{}".format(ip_address))).split(',')
            if username not in current_username_list:
                redis.append("peers:{}".format(ip_address), "{},".format(username))
            redis.expire("peers:{}".format(ip_address), 600)

        if 'rebroadcast_peers' in post_data:
#            print("Weight: {}".format(post_data['rebroadcast_peers']))
            for peer_data in post_data['rebroadcast_peers']:
#                print("{} {} {}".format(peer_data['account'], peer_data['ip'], peer_data['weight']))
                ip_address = format_ip(peer_data['ip'])
                redis.set("peer_data:{}".format(ip_address), "{},{}".format(peer_data['account'], peer_data['weight']))
                #print("peer_data:{}".format(ip_address))
                redis.expire("peer_data:{}".format(ip_address), 120)

        data = "{},{},{},{}".format(post_data['online_stake_total'], post_data['peers_stake_total'], post_data['quorum_delta'], len(peers_list['peers']))
        redis.set(post_data['api_key'],data)

        hash_dest = hashlib.sha256(username.encode('utf-8')).hexdigest()[:8]

        measurement = "peers_stake_total_{}".format(hash_dest)
        json_body = [{"measurement" : measurement, "fields": {"value": int(post_data['peers_stake_total']) / raw}}]
        print(json_body)
        influx_client.write_points(json_body)

        return "Success: {}".format(hash_dest)

    else:
        print("Incorrect api_key")
        return "Error"

#7092
app.run(host='0.0.0.0', port=7092)
