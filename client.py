import requests, argparse, time, sys, os, logging
from daemonize import Daemonize

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False
fh = logging.FileHandler("/tmp/client.log", "w")
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)
keep_fds = [fh.stream.fileno()]

parser = argparse.ArgumentParser()
parser.add_argument("--rai_node_uri", help='rai_nodes uri, usually 127.0.0.1', default='127.0.0.1')
parser.add_argument("--rai_node_port", help='rai_node port, usually 7076', default='7076')
parser.add_argument("--api_key", help='api key, get from jaycox on discord')
parser.add_argument("--daemon", help='start as daemon', default = False)

args = parser.parse_args()

def main():

    api_key = args.api_key
    logger.debug(api_key)
    if api_key == None:
        logger.debug("Error - no api key")
        sys.exit()
    rai_node_address = 'http://%s:%s' % (args.rai_node_uri, args.rai_node_port)

    def get_data(json_request):
        try:
            r = requests.post(rai_node_address, data = json_request)
            return r
        except:
            message_list.append("Error - no connection to Nano node")
            return "Error"

    while True:
        logger.debug("Grab Quorum Data")
        json_request = '{"action" : "confirmation_quorum", "peer_details" : 1}'
        r = get_data(json_request)
        if r == "Error":
            break
        resulting_data = r.json()
        logger.debug(resulting_data)

        logger.debug("Grab peers")
        peer_req = '{"action":"peers"}'
        peer_raw = get_data(peer_req)
        peer_json = peer_raw.json()
    #    logger.debug(peer_json)

        logger.debug("Send to server")
        payload = {'api_key': api_key, 'online_stake_total' : resulting_data['online_stake_total'], 'peers_stake_total' : resulting_data['peers_stake_total'], 'quorum_delta' : resulting_data['quorum_delta'], 'peers' : peer_json, 'rebroadcast_peers' : resulting_data['peers']}
        try:
            r = requests.post('http://138.68.170.107:7092/callback/', json = payload)
            logger.debug(r.text)
            if args.daemon == False:
                print(r.text)
        except:
            pass

        time.sleep(1)

if __name__ == '__main__':
    
    if args.daemon == True:
        myname=os.path.basename(sys.argv[0])
        pidfile='/tmp/%s' % myname       # any name
        daemon = Daemonize(app=myname,pid=pidfile, action=main, keep_fds=keep_fds)
        daemon.start()
    else:
        main()
