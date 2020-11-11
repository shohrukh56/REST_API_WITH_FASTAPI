import bcrypt
from sqlalchemy.orm import Session

import models
import schemas


def get_user_by_username(db: Session, username: str):
    return db.query(models.UserInfo).filter(models.UserInfo.username == username).first()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    db_user = models.UserInfo(username=user.username, password=str(hashed_password, "utf-8"), fullname=user.fullname)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def check_username_password(db: Session, user: schemas.UserAuthenticate):
    db_user_info: models.UserInfo = get_user_by_username(db, username=user.username)
    return bcrypt.checkpw(user.password.encode('utf-8'), db_user_info.password.encode("utf-8"))


def create_new_contact(db: Session, contact: schemas.ContactBase):
    db_contact = models.Contacts(phone=contact.phone)
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact


def get_all_contacts(db: Session):
    return db.query(models.Contacts).all()


def get_contact_by_id(db: Session, contact_id: int):
    return db.query(models.Contacts).filter(models.Contacts.id == contact_id).first()


def delete_contact_by_id(db: Session, contact_id: int):
    return db.query(models.Contacts).delete(models.Contacts.id == contact_id).first()


def update_contact_by_id(db: Session, contact_id: int):
    return db.query(models.Contacts).update(models.Contacts.id == contact_id).first()
