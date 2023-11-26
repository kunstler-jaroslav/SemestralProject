import PySimpleGUI as sg
from backlog_generator import BacklogGenerator, WorkItemType
from testcase_generator import TestcaseGenerator

keys = []
value_list = []
sg.theme('Default')
items = [item.name for item in WorkItemType]

# Create layout for URL and PAT input
layout_credentials = [
    [sg.Column([[sg.Text('Enter the URL:')],
                [sg.InputText(key='url')]], element_justification='c'), sg.Sizer(60, 0),
     sg.Column([[sg.Text('Enter the PAT:')],
                [sg.InputText(key='pat')]], element_justification='c')],
    [sg.Column([[sg.Button('Set', size=(8, 1)), sg.Button('Load', size=(8, 1))]], element_justification='c', justification='center')],
    [sg.HorizontalSeparator()]
]


# Write URL and PAT to file on 'Set' button click
def save_credentials(url, pat):
    if url != '' and pat != '':
        with open('credentials.txt', 'w') as f:
            f.write(url + '\n')
            f.write(pat)
            f.close()

    # Load URL and PAT from file on startup


def load_credentials():
    try:
        with open('credentials.txt', 'r') as f:
            url = f.readline().rstrip()
            pat = f.readline().rstrip()
        return url, pat
    except FileNotFoundError:
        return '', ''


def save_settings(vals):
    for k in vals:
        keys.append(k)
        value_list.append(vals[k])
    with open('settings.txt', 'w') as f:
        f.truncate(0)  # need '0' when using r+
        for i in range(len(value_list)):
            if type(value_list[i]) == str:
                f.write(keys[i] + "#-#" + value_list[i] + '\n')
        f.close()


def load_settings():
    value_list.clear()
    keys.clear()
    try:
        with open('settings.txt', 'r') as f:
            i = 0
            for line in f:
                components = line.rstrip().split('#-#')
                keys.append(components[0])
                value_list.append(components[1])
                i += 1
        return keys, value_list
    except FileNotFoundError:
        return [], []


report_methods = ["Overview", "Full report"]
layout_basic = [
    [sg.Column([[sg.Text('File name:'), sg.Sizer(40, 0), sg.InputText(key='report_file_name', size=21)]], element_justification='c')],
    [sg.Column([[sg.Text('Select a folder:'), sg.Sizer(13, 0), sg.InputText(key='report_path', size=21), sg.FolderBrowse(key='report_folder')]],
               element_justification='c')],
    [sg.Column([[sg.Text('Report type:'), sg.Sizer(30, 0), sg.DropDown(values=report_methods, size=(20, 5), enable_events=True, key='dropdown_report', readonly=True)]], element_justification='c')],
    [sg.Column([[sg.Text('Test plan:'), sg.Sizer(44, 0), sg.InputText(key='test_plan', size=21)]], element_justification='c')],
    [sg.Column([[sg.Text('Test suite:'), sg.Sizer(40, 0), sg.InputText(key='test_suite', size=21)]], element_justification='c')],
    [sg.Column([[sg.Text('Test case:'), sg.Sizer(39, 0), sg.InputText(key='test_case', size=21)]], element_justification='c')],
    [sg.Sizer(0, 98)],
    [sg.Column([[sg.Sizer(100, 0), sg.Button('Generate report')]], element_justification='c')]
]

backlog_methods = ["Hierarchy", "Types"]
layout_advanced = [
    [sg.Column([[sg.Text('File name:'), sg.Sizer(40, 0), sg.InputText(key='backlog_file_name', size=21)]], element_justification='c')],
    [sg.Column([[sg.Text('Select a folder:'), sg.Sizer(13, 0), sg.InputText(key='backlog_path', size=21), sg.FolderBrowse(key='backlog_folder')]],
               element_justification='c')],
    [sg.Column([[sg.Text('Structure:'), sg.Sizer(43, 0), sg.DropDown(values=backlog_methods, size=(20, 5), enable_events=True, key='dropdown_backlog', readonly=True)]], element_justification='c')],
    [sg.Column([[sg.Text('Team name:'), sg.Sizer(30, 0), sg.InputText(key='team_name', size=21)]],
               element_justification='c')],
    [sg.Column([[sg.Text('Project name:'), sg.Sizer(21, 0), sg.InputText(key='project_name', size=21)]],
               element_justification='c')],

    [sg.Column([[sg.Text('Root item ID:'), sg.Sizer(25, 0), sg.InputText(key='root_item_id', size=21)]], element_justification='c')],
    [sg.Column([[sg.Text('Tag filters:'), sg.Sizer(41, 0), sg.InputText(key='tag_filters', size=21)]], element_justification='c')],
    [sg.Column([[sg.Text('Work item types:', pad=((5, 5), (5, 35))), sg.Sizer(2, 0), sg.Listbox(values=items, size=(20, 3), enable_events=True, key='listbox', select_mode='multiple')]], element_justification='l', vertical_alignment='top')],
    [sg.Column([[sg.Sizer(100, 0), sg.Button('Generate backlog')]], element_justification='c')]
]

# Create left and right layouts with credentials layout at the top
left_layout = [
    [sg.Text('Report generator', font=('Helvetica', 14), justification='center')],
    [sg.Column(layout_basic, element_justification='l')]
]

right_layout = [
    [sg.Text('Backlog generator', font=('Helvetica', 14), justification='center')],
    [sg.Column(layout_advanced, element_justification='l', justification='left')]
]

down_layout = [
    [sg.Column([[sg.Button('Load settings'), sg.Button('Save settings')]], element_justification='c')]
]

layout = [
    [sg.Column(layout_credentials, element_justification='c', vertical_alignment='top')],
    [sg.Column(left_layout, element_justification='c', vertical_alignment='top'), sg.VerticalSeparator(),
     sg.Column(right_layout, element_justification='c', vertical_alignment='top')],
    [sg.HorizontalSeparator()],
    [sg.Column(down_layout, element_justification='c', vertical_alignment='top', justification='center')]
]

window = sg.Window('Dev-Ops export', layout)
backlog_gen = None
report_gen = None

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED:
        break

        # Handle the 'Set' button event
    if event == 'Set':
        url = values['url']
        pat = values['pat']
        save_credentials(url, pat)

    if event == 'Load':
        url, pat = load_credentials()
        window['url'].update(url)
        window['pat'].update(pat)

    if event == "Save settings":
        save_settings(values)
        value_list.clear()
        keys.clear()

    if event == "Load settings":
        keys, value_list = load_settings()
        for i in range(len(keys)):
            key, value = keys[i], value_list[i]
            if "folder" not in key:
                window[key].update(value)
        value_list.clear()
        keys.clear()

    # Handle the 'Generate report' button event
    if event == 'Generate report':
        print(values)
        if report_gen is None:
            report_gen = TestcaseGenerator(values['pat'], values['url'], values['report_path'])
        if values['dropdown_report'] == "Overview":
            report_gen.generate_overview(file_name=values['report_file_name'], plan=values['test_plan'])
        elif values['dropdown_report'] == "Full report":
            report_gen.generate_full_report(file_name=values['report_file_name'], plan=values['test_plan'],
                                            suite=values['test_suite'], testcase=values['test_case'])

    # Handle the 'Generate backlog' button event
    if event == 'Generate backlog':
        if backlog_gen is None:
            backlog_gen = BacklogGenerator(values['pat'], values['url'], values['backlog_path'], str(values['project_name']).strip(), str(values['team_name']).strip())

        flt = values['tag_filters']
        filters = flt.split(',')
        for flt in filters:
            flt.strip()

        items = []
        for val in values['listbox']:
            for it in WorkItemType:
                if it.name == val:
                    items.append(it)
        print(items)

        if values['dropdown_backlog'] == "Hierarchy":
            backlog_gen.get_hierarchy(values['root_item_id'], values['backlog_file_name'], tag_filters=filters, work_item_types=items)

        elif values['dropdown_backlog'] == "Types":
            if len(items) == 1:
                backlog_gen.get_items_of_type(items[0], values['backlog_file_name'], tag_filter=filters)
            else:
                print("Select just one Work ItemT ype")

window.close()
