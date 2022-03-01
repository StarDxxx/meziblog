from typing import List

from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select

from database import Post, PostCreate, PostRead, engine


router = APIRouter(
    prefix='/post',
    tags=['posts']
)

@router.post("s", response_model=PostRead)
def create_post(post: PostCreate):
    with Session(engine) as session:
        db_post = Post.from_orm(post)
        session.add(db_post)
        session.commit()
        session.refresh(db_post)
        return db_post


@router.get("s", response_model=List[Post])
def read_posts():
    with Session(engine) as session:
        posts = session.exec(select(Post)).all()
        return posts


@router.get("/{post_id}", response_model=PostRead)
def read_post(post_id: int):
    with Session(engine) as session:
        post = session.get(Post, post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        return post