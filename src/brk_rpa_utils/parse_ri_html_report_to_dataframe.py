import io
import re

import pandas as pd
from bs4 import BeautifulSoup  # BeautifulSoup4
from loguru import logger


def parse_ri_html_report_to_dataframe(mhtml_path) -> None:
    """
    Parses an mhtml file downloaded from Rollobaseret Indgang.
    The default download calls the file xls, but it is a kind of html file.

    ## Usage
    mhtml_path = Path(folder_data_session / 'test.html')

    df_mhtml = parse_ri_html_report_to_dataframe(mhtml_path)
    """
    try:
        # Read MHTML file
        with open(mhtml_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Find the HTML part of the file
        match = re.search(r'<html.*<\/html>', content, re.DOTALL)
        if not match:
            raise ValueError("No HTML content found in the file")
        html_content = match.group(0)

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_content, 'lxml')

        # Find all tables within the parsed HTML
        tables = soup.find_all('table')
        if not tables:
            raise ValueError("No tables found in the HTML content")

        # Select the largest table based on character count
        largest_table = max(tables, key=lambda table: len(str(table)))

        # Convert the largest HTML table to a pandas DataFrame
        df_mhtml = pd.read_html(io.StringIO(str(largest_table)), decimal=',', thousands='.', header=None)
        if not df_mhtml:
            raise ValueError("Failed to parse the largest table into a DataFrame")

        df_mhtml = df_mhtml[0]
        df_mhtml.columns = df_mhtml.iloc[0]
        df_mhtml = df_mhtml.drop(0)
        df_mhtml.reset_index(drop=True, inplace=True)
        df_mhtml.rename(columns={'Slut F-periode': 'date', 'Lønart': 'lonart', 'Antal': 'antal'}, inplace=True)

        # Convert 'date' column to datetime
        df_mhtml['date'] = pd.to_datetime(df_mhtml['date'], format='%d%m%Y')
        df_mhtml['antal'] = pd.to_numeric(df_mhtml['antal'])
        return df_mhtml

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return None
