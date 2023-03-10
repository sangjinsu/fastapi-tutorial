from fastapi import Depends, HTTPException, status, APIRouter
from .auth import get_current_user, User, get_user_exception
from schemas import todo
from models import models
from config.database import get_db, render_query
from sqlalchemy.orm import Session
from sqlalchemy.dialects import mysql
from sqlalchemy import insert

router = APIRouter(
    prefix="/todos",
    tags=["todo"],
)


@router.get("/")
async def read_all(db: Session = Depends(get_db)):
    new_todo = models.Todo(title='todo.title',
                           description='todo.description',
                           priority=7,
                           complete=False,
                           owner_id=3)
    model_value = await method_name(new_todo)
    query = insert(models.Todo).values(model_value)
    raw_query = query.compile(compile_kwargs={"literal_binds": True}, dialect=mysql.dialect())
    print(raw_query)
    # print(render_query(query, db))
    return db.query(models.Todo).all()


async def method_name(model):
    model_value = model.__dict__
    model_value.pop('_sa_instance_state')
    return model_value


@router.get("/user")
async def read_all_by_user(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()
    return db.query(models.Todo).filter(models.Todo.owner_id == user.id).all()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_todo(todo: todo.Todo, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()

    new_todo = models.Todo(title=todo.title,
                           description=todo.description,
                           priority=todo.priority,
                           complete=todo.complete,
                           owner_id=user.id)
    db.add(new_todo)
    db.commit()
    db.refresh(new_todo)

    return new_todo


@router.get("/{todo_id}")
async def read_todo(todo_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    todo = db.query(models.Todo) \
        .filter(models.Todo.id == todo_id) \
        .filter(models.Todo.id == user.id) \
        .first()
    if todo is None:
        raise_http_exception()
    return todo


@router.put("/{todo_id}/", status_code=status.HTTP_202_ACCEPTED)
async def update_todo(todo_id: int, todo: todo.Todo, user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()

    todo_model = db.query(models.Todo) \
        .filter(models.Todo.id == todo_id) \
        .filter(models.Todo.owner_id == user.id) \
        .first()
    if todo is None:
        raise_http_exception()
    todo_model.title = todo.title
    todo_model.description = todo.description
    todo_model.priority = todo.priority
    todo_model.complete = todo.complete

    db.add(todo_model)
    db.commit()
    db.refresh(todo_model)

    return todo_model


@router.delete("/{todo_id}")
async def delete_todo(todo_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()

    todo_model = db.query(models.Todo) \
        .filter(models.Todo.id == todo_id) \
        .filter(models.Todo.owner_id == user.id) \
        .first()
    if todo_model is None:
        raise_http_exception()
    db.query(models.Todo).filter(models.Todo.id == todo_id).delete()
    db.commit()
    return todo_model


def raise_http_exception():
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
