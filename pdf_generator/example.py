from testcase_generator import TestcaseGenerator
from backlog_generator import BacklogGenerator, WorkItemType
import os


def run_backlog():
    PAT = '<PAT>'
    ORG_URL = 'https://czprga99034srv.ad001.siemens.net:8446/DefaultCollection/'
    generator = BacklogGenerator(PAT, ORG_URL, save_path=str(os.getcwd()), project='DistributedIO',
                                 team="MF Stack Development")
    # Works only for types Epic, Feature, Task - reason unknown
    ret_type = generator.get_items_of_type(WorkItemType.Feature, "backlog_all_feature")
    # Works for any type(s)
    ret_hie = generator.get_hierarchy(39733, work_item_types=[WorkItemType.Epic, WorkItemType.Feature,
                                                              WorkItemType.Bug], filename='backlog_hierarchy')

    # Results
    print("get_items_of_type: {}".format("successful" if ret_type == 0 else "failed"))
    print("get_hierarchy: {}".format("successful" if ret_hie == 0 else "failed"))


def run_testcase():
    PAT = '3t47soint3lnek3blilcrpgeelrbgfvv5lrw4iswfeavpqbe7x7q'
    ORG_URL = 'https://czprga99034srv.ad001.siemens.net:8446/DefaultCollection/'
    gen = TestcaseGenerator(PAT, ORG_URL, save_path=str(os.getcwd()))

    ret_over = gen.generate_overview(plan="ET 200AL IO-Link DIQ4-DQ4 Test Plan", file_name="report_overview")
    ret_full = gen.generate_full_report(plan="ET 200AL IO-Link DIQ4-DQ4 Test Plan", file_name="report_full")

    # Results
    print("Overview: {}".format("successful" if ret_over == 0 else "failed"))
    print("Full report: {}".format("successful" if ret_full == 0 else "failed"))


if __name__ == "__main__":
    run_testcase()
    run_backlog()
