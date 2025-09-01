

# README — راهنمای جامع Redis برای Python (در حد سینیور)

این سند یک مرور عملی و عمیق از Redis و الگوهای متداول استفاده از آن در Python است. علاوه بر معرفی ساختار داده‌ها و تفاوت متدها، نکات تولیدی (production-grade) و نسخه‌ی اصلاح‌شده‌ی اسکریپت شما نیز ارائه شده است. همه‌ی مثال‌ها با کتابخانه‌ی رسمی `redis-py` نوشته شده‌اند.

---

## فهرست

* مقدمه
* نصب و راه‌اندازی
* اتصال به Redis و تنظیمات کلیدی
* ساختارهای داده و الگوهای رایج

  * String
  * List
  * Counter
  * Expire/TTL
  * Set
  * Hash
  * Sorted Set
* مدیریت کلیدها و جست‌وجو
* حافظه‌نهان (Cache) و Memoization
* صف، Pub/Sub و الگوهای پردازش
* تراکنش‌ها، اتمی بودن، Pipeline و Lua
* پایداری داده، تکرار و خوشه‌بندی
* سیاست‌های حافظه و تخلیه (Eviction)
* امنیت و تنظیمات تولیدی
* نسخه‌ی اصلاح‌شده‌ی اسکریپت شما

---

## مقدمه

Redis یک پایگاه‌داده‌ی in-memory و key–value است که علاوه بر سرعت بالا، مجموعه‌ای از ساختارهای داده‌ی سطح‌بالا مانند لیست، ست، هش و Sorted Set را فراهم می‌کند. موارد استفاده‌ی پرتکرار:

* Cache برای نتایج محاسبات یا پاسخ‌های API
* Session Store برای وب‌اپلیکیشن‌ها
* صف‌ها و پیام‌رسانی (Queue / Pub-Sub)
* Leaderboard با Sorted Set
* شمارنده‌های اتمی و ریت‌لیمیتینگ

---

## نصب و راه‌اندازی

### نصب Redis سرور

* لینوکس/مک: از بسته‌های رسمی یا Docker استفاده کنید:

```bash
docker run -p 6379:6379 --name redis -d redis:7-alpine
```

### نصب کتابخانه Python

```bash
pip install redis
```

---

## اتصال به Redis و تنظیمات کلیدی

برای جلوگیری از نیاز به `decode()` روی مقادیر، از `decode_responses=True` استفاده کنید. همچنین Connection Pool و Timeoutها را مشخص کنید.

```python
import redis

pool = redis.ConnectionPool(
    host='localhost', port=6379, db=0,
    decode_responses=True,  # str به‌جای bytes
    socket_connect_timeout=2, socket_timeout=2
)
r = redis.Redis(connection_pool=pool)
```

نکات:

* `decode_responses=True` خوانایی کد را بالا می‌برد.
* Timeoutها را حتماً تنظیم کنید تا در شرایط شبکه‌ای نامطمئن، بلاک نشوید.
* برای حجم بالای عملیات پشت‌سرهم از `pipeline` استفاده کنید.

---

## ساختارهای داده و الگوهای رایج

### 1) String (کلید–مقدار ساده)

کاربرد: کش ساده، فلگ‌ها، توکن‌ها.

```python
r.set("name", "Ali")     # ایجاد/بازنویسی
r.set("name", "Ali2")
print(r.get("name"))     # 'Ali2'
```

متدهای مهم و تفاوت‌ها:

* `SET` با گزینه‌های `NX`/`XX`: ایجاد فقط اگر کلید وجود ندارد/دارد.
* `EX`/`PX`: TTL بر حسب ثانیه/میلی‌ثانیه.
* `MGET`/`MSET` برای چند کلید همزمان (کاهش round-trip).

---

### 2) List (پشته/صف)

کاربرد: نگهداشت تاریخچه، صف‌های ساده، لاگ‌های کوتاه‌مدت.

```python
r.delete("history:name")
r.rpush("history:name", "Ali")   # انتهای لیست
r.rpush("history:name", "Ali2")
r.lpush("history:name", "Reza")  # ابتدای لیست

print(r.lrange("history:name", 0, -1))  # ['Reza','Ali','Ali2']
print(r.lindex("history:name", 0))      # 'Reza'
print(r.lindex("history:name", -1))     # 'Ali2'
```

تفاوت متدها:

* `LPUSH` در ابتدای لیست درج می‌کند، `RPUSH` در انتها.
* `LPOP`/`RPOP` از ابتدا/انتها خارج می‌کند.
* `BLPOP`/`BRPOP` نسخه‌ی بلاکینگ برای الگوی صف مصرف‌کننده/تولیدکننده.

---

### 3) Counter (شمارنده‌های اتمی)

کاربرد: شمارش بازدید، ریت‌لیمیتینگ، آمار.

```python
r.delete("counter")
r.incr("counter")        # 1
r.incrby("counter", 5)   # 6
r.decr("counter")        # 5
print(r.get("counter"))  # '5'
```

نکته: عملیات `INCR/DECR` اتمی هستند و نیازی به قفل اضافی ندارند.

---

### 4) Expire/TTL (انقضا)

کاربرد: کش موقت، کلیدهای خودپاک‌شونده.

```python
r.set("temp", "hello", ex=3)
print(r.get("temp"))   # 'hello'
import time; time.sleep(4)
print(r.get("temp"))   # None
```

متدهای مرتبط:

* `EXPIRE key seconds`، `PEXPIRE key ms`
* `TTL key`/`PTTL key`
* `PERSIST key` برای حذف TTL و دائمی کردن کلید

---

### 5) Set (مقادیر یکتا)

کاربرد: تگ‌ها، مجموعه‌ی یکتا، آزمون عضویت.

```python
r.delete("myset")
r.sadd("myset", "apple", "banana", "orange")
r.sadd("myset", "banana")    # نادیده به‌دلیل تکراری بودن
print(r.smembers("myset"))   # {'banana','orange','apple'}
```

متدهای مهم:

* `SISMEMBER` بررسی عضویت
* `SINTER`، `SUNION`، `SDIFF` عملیات مجموعه‌ای
* `SPOP`، `SRANDMEMBER` نمونه‌گیری تصادفی

---

### 6) Hash (دیکشنری/آبجکت)

کاربرد: پروفایل کاربر، تنظیمات.

```python
r.delete("user:100")
r.hset("user:100", mapping={"name": "Sara", "age": 25, "city": "Tehran"})
print(r.hgetall("user:100"))        # {'name':'Sara','age':'25','city':'Tehran'}
print(r.hget("user:100","name"))    # 'Sara'
```

تفاوت/نکات:

* `HSET` اتمی روی یک فیلد یا چند فیلد.
* برای افزایش عددی: `HINCRBY`/`HINCRBYFLOAT`.
* `HGETALL` روی هش‌های بزرگ سنگین است؛ ترجیحاً `HMGET` روی فیلدهای لازم.

---

### 7) Sorted Set (رتبه‌بندی/Leaderboard)

کاربرد: امتیازدهی، اولویت‌بندی با عدد واقعی یا زمان.

```python
r.delete("scores")
r.zadd("scores", {"Ali":100, "Sara":120, "Reza":90})
print(r.zrevrange("scores", 0, -1, withscores=True))
# [('Sara',120.0),('Ali',100.0),('Reza',90.0)]
```

تفاوت متدها:

* `ZRANGE`/`ZREVRANGE` با `BYLEX`/`BYSCORE`/`WITHSCORES`
* `ZINCRBY` برای افزایش تدریجی امتیاز
* محدوده بر اساس نمره (`ZRANGEBYSCORE`) یا رتبه (`ZRANK`)

---

## مدیریت کلیدها و جست‌وجو

* از `KEYS *` در تولید استفاده نکنید؛ عملیات O(N) و مسدودکننده است.
* از `SCAN` و دوستانش (`SSCAN`, `HSCAN`, `ZSCAN`) برای پیمایش تدریجی استفاده کنید.

```python
for cursor, keys in r.scan_iter(count=1000):
    pass  # الگوی امن برای جست‌وجوی تدریجی
```

---

## حافظه‌نهان (Cache) و Memoization

الگو: قبل از محاسبه، کش را بررسی کنید؛ بعد از محاسبه، با TTL مناسب ذخیره کنید.

```python
def cached_heavy_fn(n: int) -> int:
    key = f"fib:{n}"
    val = r.get(key)
    if val is not None:
        return int(val)

    # محاسبه‌ی پرهزینه (نمونه)
    result = n if n <= 1 else cached_heavy_fn(n-1) + cached_heavy_fn(n-2)

    # ذخیره با TTL برای جلوگیری از کهنگی داده
    r.set(key, result, ex=3600)
    return result
```

نکات:

* TTL را بر اساس ماهیت داده تنظیم کنید.
* برای تضمین «یک‌بار محاسبه»، می‌توانید از قفل سبک با `SET lock NX EX` استفاده کنید.

---

## صف، Pub/Sub و الگوهای پردازش

* صف ساده: `LPUSH` تولید، `BRPOP` مصرف.
* Pub/Sub: `PUBLISH` برای انتشار و `SUBSCRIBE` برای دریافت. مناسب برای اعلان‌ها، نه ذخیره دائمی پیام.
* برای صف‌های پایدارتر و تحویل تضمین‌شده، Redis Streams مناسب‌تر است (در این سند پوشش داده نشده).

---

## تراکنش‌ها، اتمی بودن، Pipeline و Lua

* بسیاری از عملیات Redis اتمی هستند، اما برای چند دستور پشت‌سرهم:

  * `MULTI/EXEC` با `WATCH` جهت CAS (Check-And-Set).
  * `pipeline()` برای کاهش round-trip (افزایش کارایی شبکه).
  * اسکریپت‌های Lua برای منطق اتمی پیچیده.

مثال Pipeline:

```python
with r.pipeline() as pipe:
    pipe.incr("counter")
    pipe.expire("counter", 60)
    results = pipe.execute()
```

---

## پایداری داده، تکرار و خوشه‌بندی

* پایداری:

  * RDB: اسنپ‌شات‌های دوره‌ای، سبک و سریع برای بکاپ.
  * AOF: ثبت همه دستورات، بازیابی دقیق‌تر، حجم بیشتر.
  * حالت ترکیبی نیز قابل تنظیم است.
* تکرار (Replication) برای خواندن مقیاس‌پذیر و افزونگی.
* Sentinel برای failover خودکار.
* Cluster برای افقی‌سازی و شاردینگ خودکار کلیدها.

---

## سیاست‌های حافظه و تخلیه (Eviction)

وقتی حافظه پر شود، Redis با توجه به `maxmemory-policy` شروع به حذف می‌کند:

* نمونه‌ها: `allkeys-lru`, `volatile-ttl`, `noeviction` و …
* برای Cache از سیاست‌های LRU/LFU استفاده کنید و TTL مناسب بگذارید.

---

## امنیت و تنظیمات تولیدی

* از قرار دادن Redis روی اینترنت عمومی خودداری کنید؛ پشت فایروال/شبکه خصوصی.
* در صورت نیاز `requirepass` و ACLها را تنظیم کنید.
* محدودیت‌های اتصال و Timeoutها را ست کنید.
* مانیتورینگ: `INFO`, `LATENCY`, متریک‌ها و Exporter برای Prometheus.

