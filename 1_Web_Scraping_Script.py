import asyncio
import glob
import math
import os
import time

from playwright.async_api import async_playwright

# The URL of the webpage to scrape
url = 'https://sedeaplicaciones.minetur.gob.es/RPC_Consulta/FrmConsulta.aspx'

# The path where the CSV files will be saved
path = "files"

# The time to wait after clicking a link on the page
wait_time = 2

# The delimiter to use between cells in the CSV files
cell_delim = ';'

# The delimiter to use between frequency values in the CSV files
frequency_delim = ','

# The CSS selector for the "current page" element on the webpage
current_page_selector = "#MainContent_gridConcesiones > tbody > tr:last-child > td > table > tbody > tr > td > span"

async def main():
    """
    The main function that runs the web scraper.
    """

    # Initialize Playwright
    async with async_playwright() as playwright:

        # Open a new browser context
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()

        # Navigate to the form page and wait for the page to load
        page = await context.new_page()
        await page.goto(url)

        # Get the values for each option in the "Comunidad" dropdown
        options = await page.query_selector_all("#MainContent_cmbComunidad option")
        comunidad_values = {}
        for i in range(1, len(options)):
            value = await options[i].get_attribute("value")
            name = await options[i].inner_text()
            comunidad_values[value] = name

        # Save the values to a CSV file
        with open("cmbComunidad.csv", "w", encoding="UTF-8") as f:
            for key in comunidad_values.keys():
                name = comunidad_values[key]
                f.write(f"{key},{name}\n")

        # Create the directory for the CSV files if it doesn't exist
        if not os.path.exists(path):
            os.mkdir(path)

        # Process each "Comunidad" in the dropdown
        for comunidad_value in comunidad_values.keys():
            await process_comunidad(comunidad_value, comunidad_values[comunidad_value], await context.new_page())

        # Merge the CSV files into a single file
        with open("table.csv", "w", encoding="UTF-8") as target:
            files = glob.glob("files/**/*.csv")
            for file in files:
                with open(file, encoding="UTF-8") as source:
                    target.writelines(source.readlines())


async def process_comunidad(comunidad_value, comunidad_label, page):
    """
    Process the data for a given "Comunidad" in the dropdown.

    Args:
        comunidad_value (str): The value of the "Comunidad" in the dropdown.
        comunidad_label (str): The label of the "Comunidad" in the dropdown.
        page (Page): The Playwright page object for the current context.
    """

    # Create a folder for the community if it does not exist yet
    comunidad_path = path + os.sep + comunidad_value
    if not os.path.exists(comunidad_path):
        os.mkdir(comunidad_path)

    # Check if all pages for the community have been processed already
    page_count_file = f"{comunidad_path}/.page_count"
    files = glob.glob(f"{comunidad_path}/*.csv")
    if os.path.exists(page_count_file):
        with open(page_count_file, "r") as comunidad_file:
            count = int(comunidad_file.readline())
            if count == len(files):
                return

    print(f"Retrieve data for comunidad: {comunidad_label} {comunidad_value}")

    # Go to the web page for the community
    await page.goto(url)

    # Find the form elements on the page and fill in the form
    form = await page.query_selector(".formulario")

    # Choose the "Servicio Fijo" radio button
    await form.wait_for_selector("#MainContent_rblTipoServicio_1")
    await page.click("input[type='radio'][id='MainContent_rblTipoServicio_1']")
    await page.wait_for_selector("#MainContent_cmbComunidad")

    # Select the community in the form
    await page.get_by_label('Comunidad').select_option(value=comunidad_value)

    # Click the "Buscar" button to submit the form
    await page.click("input[type='submit'][id='MainContent_btnBuscar']")

    # Process the first page of search results
    current_page = 1
    await process_page(page, comunidad_value, current_page)

    # Save the number of search result pages for the community to a file
    with open(page_count_file, "w") as comunidad_file:
        page_count = str(await get_page_count(page))
        comunidad_file.write(page_count)

    # Process the remaining search result pages
    while bool(True):

        # Wait for the search results table to appear
        await page.wait_for_selector("#MainContent_gridConcesiones")

        # Get the number of search result pages
        pages_count = await get_page_count(page)

        # Stop if all pages have been processed already
        if current_page == pages_count:
            break

        # Skip a page if it has already been processed
        if os.path.exists(await get_file_name(comunidad_value, current_page)) and not current_page % 10 == 1:
            continue

        # Click the link for the next page of search results
        selector = f"#MainContent_gridConcesiones a[href*='Page${current_page}']"
        link = await page.wait_for_selector(selector)
        await link.click()
        time.sleep(wait_time)

        # Check that the page has actually changed
        actual_page = await get_current_page(page)
        if current_page != actual_page:
            current_page -= 1
            time.sleep(wait_time)
            continue

        # Process the current page of search results
        await process_page(page, comunidad_value, current_page, pages_count)

    # Merge all CSV files for the community into one file
    with open(f"{path}/{comunidad_value}.csv", "w", encoding="UTF-8") as comunidad_file:
        for page in glob.glob(f"{comunidad_path}//*.csv"):
            with open(page, "r", encoding="UTF-8") as page_file:
                comunidad_file.writelines(page_file.readlines())


async def process_page(page, comunidad_value, current_page, page_count=0):
    """
        The function is desinged to process a single page of comunidad search results.
    """
    # Wait for the results page to load
    await page.wait_for_load_state()

    # Wait for the table with id "MainContent_gridConcesiones" to appear
    await page.wait_for_selector("#MainContent_gridConcesiones")

    # Find the table element on the page
    await page.query_selector("#MainContent_gridConcesiones")

    # Generate the filename for the current page
    page_file_name = await get_file_name(comunidad_value, current_page)

    # If the file already exists, skip this page and return
    if os.path.exists(page_file_name):
        print(f"Skip page {current_page} of {page_count}")
        return

    # If the file doesn't exist, print a message and start processing the page
    print(f"Retrieve page {current_page} of {page_count}")

    i = 1
    table_data = []

    # Process each row of the table
    while bool(True):

        # Find the table with id "MainContent_gridConcesiones"
        table = await page.query_selector("#MainContent_gridConcesiones")

        # Find all rows in the table
        rows = await table.query_selector_all("tr")

        # Subtract 2 from the row count if there is a current page selector,
        # indicating that there is pagination on the page
        if await page.query_selector(current_page_selector):
            rows_count -= 2

        # If we've processed all rows, exit the loop
        if i >= rows_count:
            break

        # Get the i-th row
        row = rows[i]

        # Find all cells in the row
        cells = await row.query_selector_all("td, th")

        # Extract the text content of each cell in the row
        data = []
        for cell in cells:
            text = await cell.inner_text()
            data.append(text.strip())

        # Extract the frequency data for this row and append it to the row data
        frequency = await extract_frequency(page, i - 1)
        data.append(frequency_delim.join(frequency))

        # Append the row data to the table data list
        table_data.append(data)

        # Move on to the next row
        i += 1

    # Write the table data to a CSV file
    with open(page_file_name, "w", encoding="UTF-8") as f:
        for row in table_data:
            f.write(cell_delim.join(row) + "\n")


async def extract_frequency(page, i):
    # Click on the frequency link for the i-th row
    await page.click("#MainContent_gridConcesiones_lnkFrecuencias_" + str(i))

    # Wait for the frequency page to load
    await page.wait_for_load_state()
    await page.wait_for_selector("#MainContent_pnlCesionTransferencia")

    # Find the frequency table on the page
    table = await page.query_selector("#MainContent_gridFrecuencias")

    # Find all rows in the frequency table
    rows = await table.query_selector_all("tr")

    # Extract the frequency data from each row
    frequency = []
    for row in rows[1:]:
        cells = await row.query_selector_all("td")
        frequency.append(await cells[2].inner_text())
        frequency.append(await cells[3].inner_text())

    # Close the frequency popup window and wait for the page to load again
    await page.click("#MainContent_btnCerrar")
    await page.wait_for_load_state()

    # Return the frequency
    return frequency

async def get_page_count(page):
    """ 
       This function receives a page object as a parameter and returns the total number of pages available for the website.
       It first finds the element containing the number of results on the page by using a CSS selector.
       It then extracts the text from that element and calculates the total number of pages based on the fact that 10 results are displayed per page.
     """
    
    pages_selector = await page.wait_for_selector("#MainContent_lblTotal")
    pages_text = await pages_selector.inner_text()
    pages_count = math.ceil(int(pages_text.strip(' concesiones encontradas')) / 10)
    return pages_count


async def get_current_page(page):
    """
        The function receives a page object as a parameter and returns the current page number being displayed on the website. 
        It uses the current_page_selector variable to locate the element containing the current page number and extracts the text from it.
    """

    actual_page_selector = await page.wait_for_selector(current_page_selector)
    actual_page = await actual_page_selector.inner_text()
    return int(actual_page)


async def get_file_name(comunidad_value, page_no):
    """
        The function receives the name of the community and the page number as parameters and returns the name of the file to be created for the page.
    
    """
    return path + os.sep + comunidad_value + os.sep + str(page_no).rjust(3, "0") + ".csv"


async def get_page_refs(page):
    """
        The function receives a page object as a parameter and returns a list of URLs for each page of the website.
    
    """
    cells = await page.query_selector_all(
        "#MainContent_gridConcesiones > tbody > tr:last-child > td > table > tbody > tr > td > a")
    page_refs = []
    for cell in cells:
        href = await cell.get_attribute("href")
        page_refs.append(href)
    return page_refs


if __name__ == '__main__':
    print('Start ...')
    print(os.getcwd())
    asyncio.run(main())
    print('Finish')

