import os
from azure.devops.connection import Connection
from azure.devops.v7_1.work import WorkClient
from msrest.authentication import BasicAuthentication
from azure.devops.v7_1.work.models import TeamContext
from azure.devops.v7_1.work_item_tracking import WorkItemTrackingClient
from datetime import datetime
from enum import Enum
import html_creator
import requests
import base64
import re


# TODO: Item types not working in get_items_of_type
#     function is using the types value, which is correct according to debug mode, but the function
#     work_client.get_backlog_level_work_items is unable to find it


class WorkItemType(Enum):
    Feature = 'Microsoft.FeatureCategory'
    Epic = 'Microsoft.EpicCategory'
    Task = 'Microsoft.TaskCategory'
    Bug = 'Microsoft.BugCategory'


class BacklogGenerator:

    def __init__(self, pat, org_url, save_path, project, team):
        self.PAT = pat
        self.ORG_URL = org_url
        self.credentials = BasicAuthentication('', pat)
        self.connection = Connection(base_url=org_url, creds=self.credentials)
        self.core_client = self.connection.clients.get_core_client()
        self.work_client = WorkClient(org_url, self.credentials)
        self.work_item_client = WorkItemTrackingClient(org_url, self.credentials)
        self.save_path = save_path
        self.set_team_context(project, team)
        self.team_context = None
        self.encoded_pat = base64.b64encode(str.encode(f":{pat}")).decode("utf-8")
        self.red = []
        if self.set_team_context(project_data=project, team=team) == 1:
            raise ValueError("Project name '{}' or team name '{}' are wrong".format(project, team))

    # ------- Team context -------
    def __test_team_context(self):
        ret = 0
        try:
            self.work_client.get_backlog_level_work_items(self.team_context, WorkItemType.Epic.value)
        except Exception as e:
            print(f"An error occurred with team context: {e}")
            ret = 1
        return ret

    def set_team_context(self, project_data, team="MF Stack Development"):
        """

        :param project_data: name or id of project
        :param team: name of team
        :return: 1/0 - success + working/failed - not working
        """
        get_projects_response = self.core_client.get_projects()
        while get_projects_response is not None:
            for project in get_projects_response:
                if str(project_data) == project.name or str(project_data) == str(project.id):
                    self.team_context = TeamContext(project=project.name, project_id=project.id,
                                                    team=team)
            if type(get_projects_response) is not list and get_projects_response.continuation_token is not None and \
                    get_projects_response.continuation_token != "":
                # Get the next page of projects
                get_projects_response = self.core_client.get_projects(
                    continuation_token=get_projects_response.continuation_token)
            else:
                # All projects have been retrieved
                get_projects_response = None
        if self.team_context is None:
            print("ERROR - project not found")
        return self.__test_team_context()

    def __get_all_data(self, item_type: WorkItemType):
        work_items = self.work_client.get_backlog_level_work_items(self.team_context, item_type.value)
        data_array = []
        for i in range(len(work_items.work_items)):
            data = self.work_item_client.get_work_item(work_items.work_items[i].target.id, expand="Relations")
            data_array.append(data)
        return data_array

    def __run_type_id_filter(self, top_type: WorkItemType, top):
        work_items = self.work_client.get_backlog_level_work_items(self.team_context, top_type.value)
        for i in range(len(work_items.work_items)):
            if str(work_items.work_items[i].target.id) in top:
                pass

    def __get_by_id(self, item_id):
        data = self.work_item_client.get_work_item(item_id, expand="Relations")
        return data

    def __hierarchy_run(self, top, tag_filters=None, work_item_types=None) -> str:
        """
        Recursive iteration goes through the hierarchy with given start item ID
        :param top: the top item ID
        :param tag_filters: array of tags (str) ["TAG1", "TAG2", ...]
        :param work_item_types: array of types to get from the hierarchy [WorkItemType.Epic, WorkItemType.Feature ..]
               if empty, take all
        :return: str - html string
        """
        data = self.__get_by_id(top)
        html_str = ""
        take = False
        if work_item_types is not None:
            val = self.__get_from(data.fields, 'System.WorkItemType')
            for wit in work_item_types:
                if wit.name == val:
                    take = True
        else:
            take = True
        if take and data.id not in self.red:
            html_str = self.__data_to_html([data], tag_filters=tag_filters)

        if data.relations is not None and data.id not in self.red:
            self.red.append(data.id)
            html_child = ""
            for i in range(len(data.relations)):
                if data.relations[0].attributes['name'] == 'Child':
                    url = data.relations[i].url
                    match = re.search(r'/(\d+)$', url)
                    if match:
                        number = int(match.group(1))
                        print(number)
                        html_child += self.__hierarchy_run(number, tag_filters=tag_filters,
                                                           work_item_types=work_item_types)
            html_str += html_child

        return html_str

    @staticmethod
    def __get_from(data_dictionary, name):
        res = (data_dictionary.get(name) if name in data_dictionary else None)
        return res

    def __data_to_html(self, data, tag_filters=None):
        """
        Takes take work items and formate them in html string
        :param data: array of work items [work item 1, ..]
        :param tag_filters: array of tags (str) ["TAG1", "TAG2", ...]
        :return: str - html string
        """
        html_str = ""
        for log in data:
            tags = str(self.__get_from(log.fields, 'System.Tags'))
            target_date = self.__get_from(log.fields, 'Microsoft.VSTS.Scheduling.TargetDate')
            if target_date is not None:
                template = "epic.html"
                target_date = datetime.fromisoformat(target_date)
                target_date = target_date.replace(tzinfo=None)
                left = target_date - datetime.now().replace(second=0, microsecond=0)
            else:
                template = "epic_notime.html"
                target_date = "-"
                left = "-"
            assigned = self.__get_from(log.fields, 'System.AssignedTo')
            if assigned is not None:
                assigned = assigned['displayName']

            temp_data = {
                "title": str(self.__get_from(log.fields, 'System.Title')),
                "done": str(self.__get_from(log.fields, 'System.BoardColumnDone')),
                "priority": str(self.__get_from(log.fields, 'Microsoft.VSTS.Common.Priority')),
                "target_date": str(target_date),
                "left": str(left),
                "reason": str(self.__get_from(log.fields, 'System.Reason')),
                "description": str(self.__get_from(log.fields, 'System.Description')),
                "state": str(self.__get_from(log.fields, 'System.State')),
                "assigned_to": str(assigned),
                "tags": str(self.__get_from(log.fields, 'System.Tags')),
                "work_item_type": str(self.__get_from(log.fields, 'System.WorkItemType'))
            }
            res = True
            if tag_filters is None:
                html_str += html_creator.fill_template(temp_data, template)
            else:
                for filter_tag in tag_filters:
                    if filter_tag not in tags:
                        res = False
                if res:
                    html_str += html_creator.fill_template(temp_data, template)
        return html_str

    def send_request(self, url):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.encoded_pat}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return None

    def get_items_of_type(self, item_type: WorkItemType, filename, tag_filter=None):
        data = self.__get_all_data(item_type)
        html_string = self.__data_to_html(data, tag_filters=tag_filter)
        html_creator.render_pdf(html_string, filename, path=self.save_path)
        return 0

    def get_hierarchy(self, top, filename="Hierarchy", tag_filters=None, work_item_types=None):
        """
        Saves pdf with hierarchy of work items (Epic, Feature ...), as specified on method call
        :param top: ID of the top level work item
        :param filename: name of pdf file to save
        :param tag_filters: array of tags (str) ["TAG1", "TAG2", ...]
        :param work_item_types: array of types to get from the hierarchy [WorkItemType.Epic, WorkItemType.Feature ..]
               if empty, take all
        :return: None
        """
        self.red = []
        html_str = self.__hierarchy_run(top, tag_filters=tag_filters, work_item_types=work_item_types)
        html_creator.render_pdf(html_str, filename, path=self.save_path)
        self.red = []
        return 0


if __name__ == "__main__":
    PAT = "<PAT>"
    ORG_URL = 'https://czprga99034srv.ad001.siemens.net:8446/DefaultCollection/'
    generator = BacklogGenerator(PAT, ORG_URL, save_path=str(os.getcwd()), project='DistributedIO',
                                 team="MF Stack Development")

    # Works only for types Epic, Feature, Task - reason unknown
    generator.get_items_of_type(WorkItemType.Bug, "backlog_bug")

    # Works for any type(s)
    # generator.get_hierarchy(39733, work_item_types=[WorkItemType.Epic, WorkItemType.Feature, WorkItemType.Bug], filename='Bug_hierarchy')

    # Feel free to specify other WorkItemType values in class WorkItemType
