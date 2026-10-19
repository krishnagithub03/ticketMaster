import redis 
from dotenv import load_dotenv
import os
load_dotenv()

redisClient = redis.Redis(url=os.getenv('REDIS_URL'), decode_responses=True)

if __name__ == "__main__":
    # Test the Redis connection
    try:
        res = redisClient.ping()
        redisClient.set('test_key', 'test_value')
        print("Connected to Redis successfully!", res)
        print(redisClient.get('test_key'))  # Should print 'test_value'
    except redis.ConnectionError:
        print("Failed to connect to Redis.")
