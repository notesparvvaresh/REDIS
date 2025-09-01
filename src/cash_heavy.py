import redis
import time

r = redis.Redis(host='localhost', port=6379, db=0)

def heavy_function(n):
    if r.exists(f"fib:{n}"):
        return int(r.get(f"fib:{n}"))
    

    if n <= 1:
        result = n
    else:
        result = heavy_function(n-1) + heavy_function(n-2)

    r.set(f"fib:{n}", result)
    return result




start = time.time()
print(heavy_function(35))
print("Time s:", time.time() - start)