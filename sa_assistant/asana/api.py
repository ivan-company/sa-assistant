from typing import List
import asana
from asana.rest import ApiException

from .models import AsanaProject, AsanaSection, AsanaTask, AsanaUser


class AsanaAPI:
    def __init__(self, api_token: str, team_id: str):
        configuration = asana.Configuration()
        configuration.access_token = api_token
        self.team_id = team_id

        self.client = asana.ApiClient(configuration)
        self.projects = self.get_projects_by_team(self.team_id)

    def get_user(self, user_gid="me") -> AsanaUser:
        api = asana.UsersApi(self.client)
        try:
            me = api.get_user(user_gid, {})
            return AsanaUser(
                gid=me['gid'],
                name=me['name'],
                email=me['email'],
                workspace_gid=me['workspaces'][0]["gid"],
                workspace_name=me['workspaces'][0]["name"]
            )
        except ApiException as e:
            print("Exception when calling UsersApi->get_user: %s\n" % e)

    def get_tasks_list(self, workspace_gid: str, user_gid="me"):

        api = asana.UserTaskListsApi(self.client)

        task_list = api.get_user_task_list_for_user(
            user_gid, workspace_gid, {})

        task_api = asana.TasksApi(self.client)
        tasks = task_api.get_tasks_for_user_task_list(
            task_list['gid'], {
                'opt_fields': 'name,owner,notes',
                'completed_since': 'now'
            })

        return list(tasks)

    def get_projects_by_team(self, team_gid: str) -> List[AsanaProject]:
        api = asana.ProjectsApi(self.client)
        projects = api.get_projects_for_team(team_gid, {
            'opt_fields': 'name,followers.email,followers.name'
        })
        return [AsanaProject(
            gid=p['gid'],
            name=p['name'],
            followers=[AsanaUser(
                gid=f['gid'],
                name=f['name'],
                email=f['email']
            ) for f in p['followers']]
        ) for p in projects]

    def get_tasks_by_project(self, project_gid: str) -> List[AsanaTask]:
        api = asana.TasksApi(self.client)
        tasks = api.get_tasks_for_project(project_gid, {
            'opt_fields': 'name,assignee.name,assignee.email,notes,memberships.section.name,due_at,completed',
            'completed_since': 'now'
        })
        # print(list(tasks)[0])
        return [AsanaTask(
            gid=t['gid'],
            name=t['name'],
            notes=t['notes'],
            assignee=AsanaUser(
                gid=t['assignee']['gid'],
                name=t['assignee']['name'],
                email=t['assignee']['email']
            ) if t.get('assignee') else None,
            section=AsanaSection(
                gid=t['memberships'][0]['section']['gid'],
                name=t['memberships'][0]['section']['name']
            ) if t.get('memberships') else None,
            completed=t['completed'],
            due_at=t['due_at']
        ) for t in tasks]

    def get_projects_with_users(self, user_emails: List[str]) -> List[AsanaProject]:
        """
        Returns the list of projects that have all the given users as followers.
        """
        results = []
        for project in self.projects:
            if (set(user_emails).issubset(set(f.email for f in project.followers))):
                results.append(project)
        return results
