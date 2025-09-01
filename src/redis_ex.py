import redis
import time

# Connect to Redis server (default: localhost:6379)
r = redis.Redis(host='localhost', port=6379, db=0)


# ---------------------------
# 1) String (simple key-value)
# ---------------------------
r.set("name", "ali") # store a string
print("String (first set):", r.get("name").decode())  # Ali


r.set("name", "ali") #overwrite the same key
print("String (after overwrite):", r.get("name").decode())  # Ali2

r.set("name2", "ali")
print("String with a new key:", r.get("name2").decode())  # Ali with new a key

# Note: Redis overwrites the old value. If you want to keep history, see below.

# ---------------------------
# 2) String with history using List
# ---------------------------
r.delete("name")  # clear list before use
r.rpush("name", "Ali")   # push first value
r.rpush("name", "Ali2")  # push second value

r.lpush("name", "reza")   # push from left in redis list
r.rpush("name", "Ali2")  # push from left in redis lis

print("All values in 'name':", [x.decode() for x in r.lrange("names", 0, -1)])
print("First value:", r.lindex("name", 0).decode())
print("Last value:", r.lindex("name", -1).decode())



# ---------------------------
# 4) Counter (increment/decrement)
# ---------------------------


r.set("temp", "hello", ex=3) ## key will expire in 3 seconds
print("Temp before expire:", r.get("temp").decode())
time.sleep(4)
print("Temp after expire:", r.get("temp"))  # None


# ---------------------------
# 6) List (queue style)
# ---------------------------

r.delete("mylist")
r.lpush("mylist", "A")
r.lpush("mylist", "B")
r.rpush("mylist", "C")
print("List items:", [x.decode() for x in r.lrange("mylist", 0, -1)])  # [B, A, C]


# ---------------------------
# 7) Set (unique values)
# ---------------------------
r.delete("myset")
r.sadd("myset", "apple", "banana", "orange")
r.sadd("myset", "banana")  # duplicate will not be added
print("Set members:", {x.decode() for x in r.smembers("myset")})


# ---------------------------
# 8) Hash (like dictionary/object)
# ---------------------------
r.delete("user:100")
r.hset("user:100", mapping={"name": "Sara", "age": 25, "city": "Tehran"})
print("Hash fields:", {k.decode(): v.decode() for k, v in r.hgetall("user:100").items()})
print("User name:", r.hget("user:100", "name").decode())


# ---------------------------
# 9) Sorted Set (leaderboard)
# ---------------------------
r.delete("scores")
r.zadd("scores", {"Ali": 100, "Sara": 120, "Reza": 90})
print("Leaderboard:", [(x.decode(), s) for x, s in r.zrevrange("scores", 0, -1, withscores=True)])




# ---------------------------
# 10) Keys management
# ---------------------------
print("All keys in Redis:", [x.decode() for x in r.keys("*")])

