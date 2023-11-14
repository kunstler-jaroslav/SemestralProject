import datetime
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from azure.devops.v7_1.test_plan import TestPlanClient
from azure.devops.v7_1.test_results import TestResultsClient
import pprint
import html_creator
import os
from msrest.authentication import BasicAuthentication
import xml.etree.ElementTree as ET
import logging as logger
from bs4 import BeautifulSoup
import urllib.request
import certifi


class TestcaseGenerator:

    def __init__(self, pat, org_url='https://czprga99034srv.ad001.siemens.net:8446/DefaultCollection/',
                 save_path=str(os.getcwd())):
        super().__init__()
        self.PAT = pat
        self.ORG_URL = org_url
        self.credentials = BasicAuthentication('', pat)
        self.connection = Connection(base_url=org_url, creds=self.credentials)
        self.testclient = TestPlanClient(org_url, self.credentials)
        self.resultclient = TestResultsClient(org_url, self.credentials)
        self.core_client = self.connection.clients.get_core_client()
        self.save_path = save_path
        self.__image_number = 0

    #  ---------- Helpers ------------
    @staticmethod
    def __sort_points(points):
        points.sort(key=lambda x: x.results.last_result_details.date_completed.replace(second=0, microsecond=0,
                                                                                       tzinfo=None) + datetime.timedelta(
            minutes=1))
        points.reverse()
        return points

    @staticmethod
    def __code_detection(result):
        """
        Translates test case result into code
        :param result: str - test case result in
        :return: int - code of result
        """
        ret_case_code = 5
        if result == "passed":
            ret_case_code = 0
        elif result == "failed":
            ret_case_code = 1
        elif result == "unspecified":
            ret_case_code = 2
        elif result == "blocked":
            ret_case_code = 3
        elif result == "notApplicable":
            ret_case_code = 4
        return ret_case_code

    @staticmethod
    def __delete_png(path):
        if os.path.exists(path):
            os.remove(path)

    def __get_suit_link(self, suite, testplan, project):
        link = self.ORG_URL + str(project.name) + "/_apis/testplan/Plans" + str(testplan.id) + "/Suites/" + str(suite.id)
        return link

    #  ---------- Full report ------------
    @staticmethod
    def get_case_steps_str(response):
        """
        Creates test steps html string
        :return: str - html string
        """
        if response is None:
            return ""
        root = ET.fromstring(response)
        # iterate over the 'step' elements
        string = """<p><strong>STEPS</strong></p>
        <table style="border-collapse: collapse; width: 100%;" border="0">
                                    <tbody>
                                    <tr>
                                    <td style="width: 5%;">ID</td>
                                    <td style="width: 20%;">Step type</td>
                                    <td style="width: 75%;">Description</td>
                                    </tr>
                                    </tbody>
                                    </table>
                                    <hr />"""
        for step in root.findall('step'):
            # get the 'id', 'type', and 'parameterizedString' elements
            step_id = step.get('id')
            step_type = step.get('type')
            parameterized_strings = step.findall('parameterizedString')
            if parameterized_strings[0].text is not None:
                desc = str(parameterized_strings[0].text.strip())
            else:
                desc = "None"
            # print the information for this step
            string = string + f"""<table style="border-collapse: collapse; width: 100%;" border="0">
                                    <tbody>
                                    <tr>
                                    <td style="width: 5%;">{step_id}</td>
                                    <td style="width: 20%;">{step_type}</td>
                                    <td style="width: 75%;">{desc}</td>
                                    </tr>
                                    </tbody>
                                    </table>"""
        return string

    @staticmethod
    def get_latest_results(points):
        """
        Creates last results html string
        :return: str - html string
        """
        string = """<p><strong>LATEST TEST OUTCOMES</strong></p><hr />"""
        for point in points[:5]:
            temp_vars = {
                "outcome": str(point.results.outcome),
                "tester": str(point.tester.display_name),
                "configuration": str(point.configuration.name),
                "date_completed": str(point.results.last_result_details.date_completed.replace(second=0, microsecond=0,
                                                                                               tzinfo=None) +
                                      datetime.timedelta(minutes=1)),
                "run_by": str(point.results.last_result_details.run_by.display_name),
                "build_number": str(point.results.last_run_build_number),
                "duration": str(point.results.last_result_details.duration)
            }
            string = string + html_creator.fill_template(temp_vars, temp="test_result.html")
        return string

    def process_image(self, description):
        soup = BeautifulSoup(description, 'html.parser')
        img_tag = soup.find('img')
        img_link = img_tag['src']
        html_creator.save_image(img_link, png_path=os.getcwd() + '\\' + "img{}.png".format(self.__image_number),
                                selector='img')
        img_tag['src'] = os.getcwd() + '\\' + "img{}.png".format(self.__image_number)
        html_with_new_img = str(soup)
        self.__image_number += 1
        return html_with_new_img

    def get_testcase_detail_str(self, testcase, points, project_id):
        """
        Creates detailed test case html string
        :param project_id:
        :param testcase: obj - testcase object
        :param points: list - list of points (results)
        :return: str - html string
        """
        description = next((str(field.get('System.Description')) for field in
                            testcase.work_item.work_item_fields if
                            'System.Description' in field), None)
        if description is not None and "img" in description:
            description = self.process_image(description)

        temp_vars = {"test_case_id": str(testcase.work_item.id),
                     "test_case_name": str(testcase.work_item.name),
                     "assigned_to": next(
                         (str(field.get('System.AssignedTo')) for field in testcase.work_item.work_item_fields if
                          'System.AssignedTo' in field), None),
                     "state": next((str(field.get('System.State')) for field in testcase.work_item.work_item_fields if
                                    'System.State' in field), None),
                     "automation_status": next((str(field.get('Microsoft.VSTS.TCM.AutomationStatus')) for field in
                                                testcase.work_item.work_item_fields if
                                                'Microsoft.VSTS.TCM.AutomationStatus' in field), None),
                     "case_link": str(testcase.links.additional_properties['_self']['href']),
                     "case_description": description}
        string = html_creator.fill_template(temp_vars, temp="full_testcase.html")
        # if len(points) > 0:
        #     log_store_attachments = resultclient.get_test_run_log_store_attachments(str(project_id),
        #                                                                             int(points[0].results.last_test_run_id))
        #     print(log_store_attachments)

        string = string + self.get_case_steps_str(
            next((str(field.get('Microsoft.VSTS.TCM.Steps')) for field in testcase.work_item.work_item_fields if
                  'Microsoft.VSTS.TCM.Steps' in field), None))
        string = string + self.get_latest_results(points)
        return string

    def get_test_suite_detail_str(self, project_id, testplan_id, suite, sl):
        """
        Calls get_testcase_detail_str to get its parts
        :return: str - html string
        """
        print("    Test suit ID: " + str(suite.id) + "   Name: " + str(suite.name))
        temp_vars = {
            "test_suite_id": str(suite.id),
            "test_suite_name": str(suite.name),
            "type": str(suite.suite_type),
            "configurations": str(suite.default_configurations),
            "suite_link": str(sl)
        }

        string = html_creator.fill_template(temp_vars, temp="full_suite.html")

        testcaselist = self.testclient.get_test_case_list(project_id, testplan_id, suite.id)
        for testcase in testcaselist:
            points = self.testclient.get_points_list(project_id, testplan_id, suite.id,
                                                     test_case_id=testcase.work_item.id)
            points = self.__sort_points(points)
            string = string + self.get_testcase_detail_str(testcase, points, project_id)
            print("        Testcase ID: " + str(testcase.work_item.id) + "   Name: " + str(testcase.work_item.name))
        return string

    def get_test_plan_detail_str(self, project, testplan):
        """
        Calls get_test_suite_detail_str to get its parts
        :return: str - html string
        """
        temp_vars = {
            "test_plan_id": str(testplan.id),
            "test_plan_name": str(testplan.name),
            "owner": str(testplan.owner),
            "state": str(testplan.state),
            "iteration": str(testplan.iteration),
            "area_path": str(testplan.area_path),
            "test_plan_description": str(testplan.description)
        }
        string = html_creator.fill_template(temp_vars, temp="full_testplan.html")
        testsuits = self.testclient.get_test_suites_for_plan(project.name, testplan.id)
        for suite in testsuits[1:]:
            string = string + self.get_test_suite_detail_str(project.id, testplan.id, suite,
                                                             self.__get_suit_link(suite, testplan, project))
        return string

    def get_full_report(self, project, testplan, full_suite="", full_testcase="", filename=""):
        if filename == "":
            filename = "report" + str(testplan.id) + str(full_suite) + str(full_testcase) + str(datetime.datetime)
        testsuites = self.testclient.get_test_suites_for_plan(project.name, testplan.id)
        if full_suite == "" and full_testcase == "":  # full testplan
            # get_overview(project, testplan, filename="temporary.pdf", automated=False)
            result = self.get_test_plan_detail_str(project, testplan)
            print("RENDERING PDF")
            html_creator.render_pdf(result, filename=filename, path=self.save_path)
        elif full_testcase == "":  # full suite
            for suite in testsuites[1:]:
                if str(suite.id - 0) == full_suite or str(suite.name) == full_suite:
                    print("Suite found")
                    result = self.get_test_suite_detail_str(project.id, testplan.id, suite,
                                                            self.__get_suit_link(suite, testplan, project))
                    html_creator.render_pdf(result, filename=filename, path=self.save_path)
        else:  # just test case
            for suit in testsuites[1:]:
                testcaselist = self.testclient.get_test_case_list(project.id, testplan.id, suit.id)
                for testcase in testcaselist:
                    if str(testcase.work_item.id) == full_testcase or str(testcase.work_item.name) == full_testcase:
                        print("Testcase found")
                        points = self.testclient.get_points_list(project.id, testplan.id, suit.id,
                                                                 test_case_id=testcase.work_item.id)
                        result = self.get_testcase_detail_str(testcase, points, project.id)
                        html_creator.render_pdf(result, filename=filename, path=self.save_path)

    #  ---------- Overview report ------------
    def set_case_vars(self, points, testcase):
        """
        Prepares variables to be filled into html case format
        :param points: History of test case results
        :param testcase: All testcases from this suit
        :return: dict, bool, bool, int - vars for html, _, _, _
        """
        ret_suit = True
        ret_plan = True
        if len(points) > 0:
            ret_case_code = self.__code_detection(str(points[0].results.outcome))
            col = '#000000'
            if ret_case_code == 0:
                col = '#00ff00'
            elif ret_case_code == 1:
                col = '#ff0000'
                ret_plan = False
                ret_suit = False

            temp_vars = {"test_case_id": str(testcase.work_item.id),
                         "test_case_name": str(testcase.work_item.name),
                         "test_case_result": str(points[0].results.outcome),
                         "case_color": col,
                         "case_link": str(points[0].links.additional_properties['testCases']['href'])}

            return temp_vars, ret_suit, ret_plan, ret_case_code
        else:
            return False, False, False, 0

    def set_case_vars_auto(self, points, testcase):
        """
        Prepares variables to be filled into html case format
        :param points: History of test case results
        :param testcase: All testcases from this suit
        :return: dict, bool, bool, int - vars for html, _, _, _
        """
        ret_suit = True
        ret_plan = True
        if len(points) > 0:
            ret_case_code = self.__code_detection(str(points[0].results.outcome))
            col = '#000000'
            if ret_case_code == 0:
                col = '#00ff00'
            elif ret_case_code == 1:
                col = '#ff0000'
                ret_plan = False
                ret_suit = False
            if points[0].is_automated:
                automated = "Automated"
                auto_col = "#00ff00"
            else:
                automated = "Not automated"
                auto_col = "#000000"

            temp_vars = {"test_case_id": str(testcase.work_item.id),
                         "test_case_name": str(testcase.work_item.name),
                         "test_case_result": str(points[0].results.outcome),
                         "case_color": col,
                         "case_link": str(points[0].links.additional_properties['testCases']['href']),
                         "automated_color": auto_col,
                         "test_case_automated": automated}
            return temp_vars, ret_suit, ret_plan, ret_case_code
        else:
            return False, False, False, 0

    def set_suit_vars(self, suite, suit_res, testplan, project):
        """
        Prepares variables to be filled into html suite format
        :param suite: Current suit
        :param suit_res: bool - result if suit passed or not
        :param testplan: Testplan which the suit is part of
        :param project: Which project is the test suite part of
        :return: dict - variables to be filled into html format
        """
        suit_result = "passed"
        col = '#00ff00'
        if not suit_res:
            col = '#ff0000'
            suit_result = "failed"
        link = self.__get_suit_link(suite, testplan, project)
        temp_vars = {"test_suit_id": str(suite.id),
                     "test_suit_name": str(suite.name),
                     "test_suit_result": suit_result,
                     "suit_color": col,
                     "suit_link": link}
        return temp_vars

    @staticmethod
    def set_plan_vars(testsuits, plan_res, testplan):
        """
        Prepares variables to be filled into html plan format
        :param testsuits: List of test suites in this plan
        :param plan_res: did the plann pass or fail
        :param testplan: current test plan
        :return: dict - variables to be filled into html format
        """
        plan_result = "passed"
        col = '#00ff00'
        if not plan_res:
            col = '#ff0000'
            plan_result = "failed"
        temp_vars = {"test_plan_id": str(testplan.id),
                     "test_plan_name": str(testsuits[0].name),
                     "test_plan_result": plan_result,
                     "plan_color": col}
        return temp_vars

    def get_overview(self, project, testplan, filename="", automated=False):
        """
        Function runs the process of overview pdf file creation
        :param project: Project to create the overview for
        :param testplan: Testplan to create the overview for
        :param filename: str - Name of pdf file to save
        :param automated: bool - Get information about which test case is automated
        :return: None
        """
        data = [0, 0, 0, 0, 0, 0]
        testcase_count = 0

        if filename == "":
            filename = "overview" + str(testplan.id) + str(datetime.datetime)
        html_string = ""
        plan_res = True
        testsuits = self.testclient.get_test_suites_for_plan(project.name, testplan.id)
        plan_html = ""

        for suit in testsuits[1:]:
            print("    Test suite ID: " + str(suit.id) + "   Name: " + str(suit.name))
            suit_html = ""
            suit_res = True
            testcaselist = self.testclient.get_test_case_list(project.id, testplan.id, suit.id)

            # All testcases to html
            for testcase in testcaselist:
                points = self.testclient.get_points_list(project.id, testplan.id, suit.id,
                                                         test_case_id=testcase.work_item.id)
                # Fill test case variables
                if len(points) > 0:
                    points = self.__sort_points(points)

                    if not automated:
                        temp_vars, temp_suit, temp_plan, result = self.set_case_vars(points, testcase)
                        if temp_vars:
                            suit_html += html_creator.fill_template(temp_vars, temp="template_case.html")
                    else:
                        temp_vars, temp_suit, temp_plan, result = self.set_case_vars_auto(points, testcase)
                        if temp_vars:
                            suit_html += html_creator.fill_template(temp_vars, temp="template_case_auto.html")
                    if not temp_plan:
                        plan_res = False
                    if not temp_suit:
                        suit_res = False
                    if temp_vars:
                        testcase_count += 1
                        data[result] += 1

            # Fill test suite details
            if not automated:
                plan_html += html_creator.fill_template(self.set_suit_vars(suit, suit_res, testplan, project),
                                                        temp="template_suite.html")
            else:
                plan_html += html_creator.fill_template(self.set_suit_vars(suit, suit_res, testplan, project),
                                                        temp="template_suite_auto.html")
            plan_html += suit_html

        # Fill test plan details
        html_string += html_creator.fill_template(self.set_plan_vars(testsuits, plan_res, testplan),
                                                  temp="template_plan.html")
        html_string += plan_html
        path = html_creator.add_graphical_header(data)
        header_str = html_creator.fill_template(
            {"path": path, "cases": testcase_count, "passed": data[0], "failed": data[1], "notapplicable": data[4],
             "blocked": data[3], "unspecified": data[2], "other": data[5]}, "header.html")
        html_string = "<html>" + header_str + "<br><br>" + html_string + "</html>"
        html_creator.render_pdf(html_string, filename, path=self.save_path)
        self.__delete_png(path)

    #  ---------- Runners ------------
    def generate_overview(self, plan="", file_name=""):
        """
        Generates overview of testplan
        :param plan: Name/ID of testplan
        :param file_name: str - file to save in
        :return: 0/1 success/failed
        """
        logger.info("Generating overview of {} to {}".format(plan, self.save_path + "/" + file_name))
        get_projects_response = self.core_client.get_projects()
        index = 0
        while get_projects_response is not None:
            for project in get_projects_response:
                pprint.pprint("[" + str(index) + "] " + project.name + " " + str(project.id))
                testplans = self.testclient.get_test_plans(project.name)
                for testplan in testplans:
                    pprint.pprint(testplan.name + " " + str(testplan.id))
                    if testplan.name == str(plan) or str(testplan.id) == str(plan) or str(
                            self.testclient.get_test_suites_for_plan(project.id, testplan.id)[0].id) == str(plan):
                        self.get_overview(project, testplan, filename=file_name)
                        return 0

                index += 1
            if type(get_projects_response) is not list and get_projects_response.continuation_token is not None and \
                    get_projects_response.continuation_token != "":
                # Get the next page of projects
                get_projects_response = self.core_client.get_projects(
                    continuation_token=get_projects_response.continuation_token)
            else:
                # All projects have been retrieved
                get_projects_response = None
        return 1

    def generate_full_report(self, plan="", suite="", testcase="", file_name=""):
        """
        Generates full report for the specified range
        :param plan: Name/ID of testplan
        :param suite: Name/ID of test suite
        :param testcase: Name/ID of test case
        :param file_name: str - file to save in
        :return: 0/1 success/failed
        """
        logger.info(
            "Generating full report of {} {} {} to {}".format(plan, suite, testcase, self.save_path + "/" + file_name))
        get_projects_response = self.core_client.get_projects()
        index = 0
        ret = 0
        while get_projects_response is not None:
            for project in get_projects_response:
                pprint.pprint("[" + str(index) + "] " + project.name + " " + str(project.id))
                testplans = self.testclient.get_test_plans(project.name)
                for testplan in testplans:
                    pprint.pprint(testplan.name + " " + str(testplan.id))
                    if testplan.name == str(plan) or str(testplan.id) == str(plan) or str(
                            self.testclient.get_test_suites_for_plan(project.id, testplan.id)[0].id) == str(plan):
                        self.get_full_report(project, testplan, suite, testcase, file_name)
                        ret = 0
                        break
                index += 1
            if type(get_projects_response) is not list and get_projects_response.continuation_token is not None and \
                    get_projects_response.continuation_token != "":
                # Get the next page of projects
                get_projects_response = self.core_client.get_projects(
                    continuation_token=get_projects_response.continuation_token)
            else:
                # All projects have been retrieved
                get_projects_response = None
        if self.__image_number > 0:
            for i in range(self.__image_number):
                self.__delete_png(os.getcwd() + '\\' + "img{}.png".format(i))
        return ret


if __name__ == "__main__":
    PAT = '<PAT>'
    ORG_URL = 'https://czprga99034srv.ad001.siemens.net:8446/DefaultCollection/'
    gen = TestcaseGenerator(PAT, ORG_URL, save_path=str(os.getcwd()))

    ret_over = gen.generate_overview(plan="ET 200AL IO-Link DIQ4-DQ4 Test Plan", file_name="objover")
    ret_full = gen.generate_full_report(plan="ET 200AL IO-Link DIQ4-DQ4 Test Plan", file_name="fullobj")
    print("Overview: {}".format("successful" if ret_over == 0 else "failed"))
    print("Full report: {}".format("successful" if ret_full == 0 else "failed"))
