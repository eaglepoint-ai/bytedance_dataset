# models.py
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String)
    createdAt = Column(DateTime)

class Folder(Base):
    __tablename__ = "folders"
    id = Column(String, primary_key=True)
    name = Column(String)
    ownerId = Column(String, ForeignKey("users.id"))
    parentId = Column(String, ForeignKey("folders.id"), nullable=True)
    createdAt = Column(DateTime)

class File(Base):
    __tablename__ = "files"
    id = Column(String, primary_key=True)
    name = Column(String)
    folderId = Column(String, ForeignKey("folders.id"))
    ownerId = Column(String, ForeignKey("users.id"))
    createdAt = Column(DateTime)

class Permission(Base):
    __tablename__ = "permissions"
    id = Column(String, primary_key=True)
    userId = Column(String, ForeignKey("users.id"))
    resourceType = Column(String)  # file | folder
    resourceId = Column(String)
    level = Column(String)  # view | comment | edit | owner
    createdAt = Column(DateTime)
