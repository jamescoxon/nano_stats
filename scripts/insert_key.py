import random
import time
import redis

redis = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

username = input("username: ")
print("Generate new key")
new_key = hex(random.SystemRandom().getrandbits(128))
api_key = new_key[2:].upper()
print("{}".format(api_key))
print()
print(redis.get("api_key_whitelist"))

print("Insert into database")

result = redis.append("api_key_whitelist", "{},".format(api_key))
redis.set("api:{}".format(api_key),username)

print(redis.get("api_key_whitelist"))
print("Done")
