import os
from datetime import date, datetime
from typing import Literal

import pymysql
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

load_dotenv()
app = FastAPI(title="Steady")
app.mount("/static", StaticFiles(directory="static"), name="static")


class TaskInput(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    course: str = Field(min_length=1, max_length=150)
    due_date: date
    status: Literal["pending", "in_progress", "completed"] = "pending"

    @field_validator("title", "course", mode="before")
    @classmethod
    def trim(cls, value):
        return value.strip() if isinstance(value, str) else value


class TaskUpdate(TaskInput):
    status: Literal["pending", "in_progress", "completed"]


class Task(TaskInput):
    id: int
    created_at: datetime


def connect():
    ca = os.environ.get("DB_SSL_CA")
    return pymysql.connect(
        host=os.environ["DB_HOST"], port=int(os.environ.get("DB_PORT", "3306")),
        database=os.environ["DB_NAME"], user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"], connect_timeout=3,
        cursorclass=pymysql.cursors.DictCursor,
        **({"ssl_ca": ca, "ssl_verify_cert": True, "ssl_verify_identity": True} if ca else {}),
    )


@app.exception_handler(pymysql.MySQLError)
def database_error(request, exc):
    return Response(content='{"detail":"Database tidak tersedia"}', status_code=503, media_type="application/json")


@app.get("/")
def index():
    return FileResponse("static/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    try:
        with connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
    except (pymysql.MySQLError, KeyError, ValueError):
        raise HTTPException(status_code=503, detail="Database tidak tersedia") from None
    return {"status": "ok"}


@app.get("/tasks", response_model=list[Task])
def list_tasks():
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT * FROM tasks ORDER BY due_date, id")
        return cursor.fetchall()


@app.post("/tasks", response_model=Task, status_code=201)
def create_task(task: TaskInput):
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("INSERT INTO tasks (title, course, due_date, status) VALUES (%s, %s, %s, %s)",
                       (task.title, task.course, task.due_date, task.status))
        cursor.execute("SELECT * FROM tasks WHERE id = %s", (cursor.lastrowid,))
        result = cursor.fetchone()
        connection.commit()
        return result


@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task: TaskUpdate):
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("UPDATE tasks SET title=%s, course=%s, due_date=%s, status=%s WHERE id=%s",
                       (task.title, task.course, task.due_date, task.status, task_id))
        cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Tugas tidak ditemukan")
        connection.commit()
        return result


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
        if not cursor.rowcount:
            raise HTTPException(status_code=404, detail="Tugas tidak ditemukan")
        connection.commit()
    return Response(status_code=204)
