from fastapi import FastAPI
from redis import Redis
from sqlalchemy import create_engine
from prometheus_fastapi_instrumentator import Instrumentator
import os

app = FastAPI()

# 添加 Prometheus 监控
@app.on_event("startup")
async def startup():
    Instrumentator().instrument(app).expose(app)

# Redis 连接
redis_client = Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=6379,
    db=0
)

# MySQL 连接
DATABASE_URL = f"mysql://root:{os.getenv('MYSQL_ROOT_PASSWORD')}@{os.getenv('MYSQL_HOST', 'mysql')}/test"
engine = create_engine(DATABASE_URL)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/redis-test")
def test_redis():
    redis_client.incr('hits')
    return {"hits": int(redis_client.get('hits') or 0)}

@app.get("/mysql-test")
def test_mysql():
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            return {"mysql": "connected"}
    except Exception as e:
        return {"error": str(e)}
