from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlmodel import Session, select
from pydantic import EmailStr

from database import UserRead, User, UserUpdate, get_session
from config import ADMINS_EMAILS

from oauth import get_current_user

from typing import List


router = APIRouter(
    prefix="/user", tags=["users"]
)


@router.get("s", response_model=List[UserRead], status_code=status.HTTP_200_OK)
async def read_users(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, lte=100),
    _=Depends(get_current_user)
):
    users = session.exec(select(User).offset(offset).limit(limit)).all()
    return users


@router.get("/me", response_model=UserRead, status_code=status.HTTP_200_OK)
async def read_current_user(current_user=Depends(get_current_user)):
    return current_user


@router.get("/{user_email}", response_model=UserRead, status_code=status.HTTP_200_OK)
async def read_user(*, session: Session = Depends(get_session), user_email: EmailStr, _=Depends(get_current_user)):
    statement = select(User).where(User.email == user_email)
    results = session.exec(statement)
    user = results.first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch(
    "/{user_email}", response_model=UserRead, status_code=status.HTTP_202_ACCEPTED
)
async def update_user(
    *, session: Session = Depends(get_session), user_email: EmailStr, user: UserUpdate, current_user=Depends(get_current_user)
):
    if current_user.email not in ADMINS_EMAILS:
        raise HTTPException(status_code=403, detail="Not allowed")
    statement = select(User).where(User.email == user_email)
    results = session.exec(statement)
    db_user = results.first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    user_data = user.dict(exclude_unset=True)
    for key, value in user_data.items():
        setattr(db_user, key, value)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@router.delete("/{user_email}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    *,
    session: Session = Depends(get_session),
    user_email: EmailStr,
    current_user=Depends(get_current_user)
):
    if current_user.email not in ADMINS_EMAILS:
        raise HTTPException(status_code=403, detail="Not allowed")
    statement = select(User).where(User.email == user_email)
    results = session.exec(statement)
    user = results.first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(user)
    session.commit()
    return {"ok": True}
