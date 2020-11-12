import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError
from sqlalchemy.orm import Session
from starlette import status
import pymysql

pymysql.install_as_MySQLdb()
import crud
import models
import schemas
from app_utils import decode_access_token
from crud import get_user_by_username
from database import engine, SessionLocal
from schemas import UserInfo, TokenData

models.Base.metadata.create_all(bind=engine)

ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()


# Dependency


def get_db():
    db = None
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/authenticate")


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(data=token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except PyJWTError:
        raise credentials_exception
    user = get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


@app.post("/user", response_model=schemas.UserInfo)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)


@app.post("/authenticate", response_model=schemas.Token)
def authenticate_user(user: schemas.UserAuthenticate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user is None:
        raise HTTPException(status_code=400, detail="Username not existed")
    else:
        is_password_correct = crud.check_username_password(db, user)
        if is_password_correct is False:
            raise HTTPException(status_code=400, detail="Password is not correct")
        else:
            from datetime import timedelta
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            from app_utils import create_access_token
            access_token = create_access_token(
                data={"sub": user.username}, expires_delta=access_token_expires)
            return {"access_token": access_token, "token_type": "Bearer"}


@app.post("/contact", response_model=schemas.Contact)
async def create_new_contact(blog: schemas.ContactBase, current_user: UserInfo = Depends(get_current_user)
                             , db: Session = Depends(get_db)):
    return crud.create_new_contact(db=db, contact=blog)


@app.get("/contact")
async def get_all_contacts(current_user: UserInfo = Depends(get_current_user)
                           , db: Session = Depends(get_db)):
    return crud.get_all_contacts(db=db)


@app.get("/contact/{contact_id}")
async def get_contact_by_id(contact_id, current_user: UserInfo = Depends(get_current_user)
                            , db: Session = Depends(get_db)):
    return crud.get_contact_by_id(db=db, contact_id=contact_id)


@app.delete("/contact/{contact_id}")
async def delete_contact_by_id(contact_id, current_user: UserInfo = Depends(get_current_user),
                               db: Session = Depends(get_db)):
    return crud.delete_contact_by_id(db=db, contact_id=contact_id)


@app.patch("/contact/{contact_id}")
async def update_contact_by_id(contact_id, contact: schemas.ContactBase,
                               current_user: UserInfo = Depends(get_current_user)
                               , db: Session = Depends(get_db)):
    return crud.update_contact_by_id(db=db, phone=contact.phone, contact_id=contact_id)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8081)
