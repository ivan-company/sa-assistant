from typing import List
from pydantic import BaseModel


class AsanaUser(BaseModel):
    """
    A user in Asana.
    """
    gid: str
    name: str
    email: str
    workspace_gid: str | None = None
    workspace_name: str | None = None


class AsanaTeam(BaseModel):
    """
    A team in Asana.
    """
    gid: str
    name: str


class AsanaProject(BaseModel):
    """
    A project in Asana.
    """
    gid: str
    name: str
    followers: List[AsanaUser]


class AsanaSection(BaseModel):
    """
    A section in Asana.
    """
    gid: str
    name: str


class AsanaTask(BaseModel):
    """
    A task in Asana.
    """
    gid: str
    name: str
    notes: str
    assignee: AsanaUser | None = None
    section: AsanaSection | None = None
    completed: bool
    due_at: str | None = None
