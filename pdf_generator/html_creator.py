import jinja2
import pdfkit
import asyncio
import time
from pyppeteer import launch
import os


template_loader = jinja2.FileSystemLoader('./')
template_env = jinja2.Environment(loader=template_loader)


def fill_template(data, temp='header.html'):
    """
    Fills the template with values and returns string with the html code
    :param data: dict - variables dictionary to be filled into the template
    :param temp: desired template name
    :return: str - string containing the html code
    """
    path_base = os.getcwd()
    path = path_base + "\\templates"
    os.chdir(path)
    template = template_env.get_template(temp)
    html_str = template.render(data)
    os.chdir(path_base)
    return html_str


def render_pdf(html_str, filename, path=str(os.getcwd())):
    """
    Creates pdf file from html string
    :param path: where to save ("C:\\projects")
    :param html_str: str - html file to be rendered to pdf document
    :param filename: str - name of the pdf file ("filename.pdf")
    :return: None
    """
    path_wkhtmltopdf = str(os.getcwd()) + "\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"
    if not os.path.exists(path_wkhtmltopdf):
        print("No module wkhtmltopdf")
        exit()
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

    options = {
        'javascript-delay': '10000',
        'page-size': 'A4',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
        'encoding': "UTF-8",
        'enable-local-file-access': None,
        'no-outline': None
    }
    pdfkit.from_string(html_str, path + "\\" + filename + ".pdf", configuration=config, options=options)


async def __save_png(html_str, png_path=os.getcwd() + '\\' + "outputpng.png", selector='canvas'):
    # Launch a headless browser with pyppeteer
    browser = await launch(headless=True)
    # Open a new page in the browser
    page = await browser.newPage()
    # Navigate to the HTML file containing Chart.js
    if selector == 'canvas':
        await page.setContent(html_str)
    else:
        await page.goto(html_str)
    await page.waitForSelector(selector)
    # Get the Chart.js canvas element
    canvas_element = await page.querySelector(selector)
    # Get the size of the canvas element
    canvas_size = await canvas_element.boundingBox()
    time.sleep(2)
    # Take a screenshot of the canvas element as a PNG image
    png_data = await canvas_element.screenshot()
    # Write the PNG data to a file
    with open(png_path, 'wb') as file:
        file.write(png_data)
        # Close the browser
    await browser.close()


def save_image(html_str, png_path=os.getcwd() + '\\' + "outputpng.png", selector='canvas'):
    """
    synchronously saves png file with graph
    :param selector: name of element to save
    :param html_str: str - html code containing javascript for graph generation
    :param png_path: str - path where to save the png file
    :return: str - path of the saved png
    """
    asyncio.get_event_loop().run_until_complete(__save_png(html_str, png_path, selector=selector))
    return png_path


def add_graphical_header(data):
    """
    creates graphical png representation of protocol data
    :param data: list - [test_count, test_passed, test_failed, test_unspecified, test_blocked, test_notapplicable, test_other]
    :return: str - path of the saved png of graph
    """
    template_vars = {
        "passed": data[0],
        "failed": data[1],
        "notapplicable": data[4],
        "blocked": data[3],
        "unspecified": data[2],
        "other": data[5]
    }
    html_str = fill_template(template_vars, temp="pass_rate_template.html")
    return save_image(html_str)


if __name__ == "__main__":
    temp_variables = {}
    html_string = fill_template(temp_variables, temp="test.html")
    render_pdf(html_string, "htmlcreator_run")
