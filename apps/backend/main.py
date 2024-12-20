from fastapi import FastAPI, HTTPException
from redis import Redis
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, select
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from typing import Optional
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
DATABASE_URL = f"mysql://root:{os.getenv('MYSQL_ROOT_PASSWORD')}@{os.getenv('MYSQL_HOST', 'mysql')}"
root_engine = create_engine(DATABASE_URL)

# 创建数据库
@app.on_event("startup")
async def create_database():
    try:
        with root_engine.connect() as conn:
            conn.execute("CREATE DATABASE IF NOT EXISTS test")
            conn.execute("USE test")
    except Exception as e:
        print(f"Error creating database: {e}")

# 连接到特定数据库
engine = create_engine(f"{DATABASE_URL}/test")

# 创建 users 表
metadata = MetaData()
users = Table(
    'users',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(50)),
    Column('email', String(100))
)

# 在应用启动时创建表
@app.on_event("startup")
async def create_tables():
    metadata.create_all(engine)

# Pydantic model for user
class User(BaseModel):
    name: str
    email: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

@app.get("/")
def read_root():
    return {"Hello": "World"}

# Redis endpoints
@app.get("/redis/hits")
def get_hits():
    return {"hits": int(redis_client.get('hits') or 0)}

@app.post("/redis/hits/increment")
def increment_hits():
    redis_client.incr('hits')
    return {"hits": int(redis_client.get('hits'))}

@app.post("/redis/hits/reset")
def reset_hits():
    redis_client.set('hits', 0)
    return {"hits": 0}

# MySQL CRUD endpoints
@app.post("/users/")
def create_user(user: User):
    try:
        with engine.connect() as conn:
            result = conn.execute(
                users.insert().values(
                    name=user.name,
                    email=user.email
                )
            )
            conn.commit()
            return {"id": result.lastrowid, **user.dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users/")
def read_users():
    try:
        with engine.connect() as conn:
            result = conn.execute(select(users))
            return [{"id": row[0], "name": row[1], "email": row[2]} for row in result]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users/{user_id}")
def read_user(user_id: int):
    try:
        with engine.connect() as conn:
            result = conn.execute(
                select(users).where(users.c.id == user_id)
            ).first()
            if result is None:
                raise HTTPException(status_code=404, detail="User not found")
            return {"id": result[0], "name": result[1], "email": result[2]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/users/{user_id}")
def update_user(user_id: int, user: UserUpdate):
    try:
        with engine.connect() as conn:
            # Only update provided fields
            update_data = {k: v for k, v in user.dict().items() if v is not None}
            if not update_data:
                raise HTTPException(status_code=400, detail="No fields to update")

            result = conn.execute(
                users.update()
                .where(users.c.id == user_id)
                .values(**update_data)
            )
            conn.commit()

            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="User not found")

            # Get updated user
            updated_user = conn.execute(
                select(users).where(users.c.id == user_id)
            ).first()
            return {"id": updated_user[0], "name": updated_user[1], "email": updated_user[2]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    try:
        with engine.connect() as conn:
            result = conn.execute(
                users.delete().where(users.c.id == user_id)
            )
            conn.commit()
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="User not found")
            return {"message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
