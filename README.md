# nano_stats

### **Client Runtime Instructions**

**Ubuntu 18.04**

1. 
    ```
    $ sudo apt-get update && sudo apt-get install pip3
    ```
2. 
    ```
    $ git clone https://github.com/jamescoxon/nano_stats.git && cd nano_stats
    ```
3. 
    ```
    $ pip3 install requests argparse
    ```
4. 
    ```
    $ python3 client.py --api_key <KEY>
    ```

*Note*: In case you're running Docker with IPv6 callback address mapped, you will also have to pass `--rai_node_uri '[::1]'` as an argument.