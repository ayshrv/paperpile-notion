"""Updates the target Notability database using a CSV exported from Paperpile

    How it works:

    - The CSV file must be extracted from Paperpile with the default export functionality.
    - If a paper with the same title is already in the Notability database, we update the fields that have changed except for the title.
"""

import csv
import yaml
import argparse

from typing import Dict, Any

from rich import print
from lib.notion import NotionDBInterface
from lib.preproc import format_entry

def hamming_distance(x, y):
    return sum(c1 != c2 for c1, c2 in zip(x, y))


def check_identical(entry: Dict[str, Dict[str, Any]], page: Dict[str, Any]) -> bool:
    for key, val in [(k,v) for k,v in page.items() if k not in ['id', 'Institutions', 'Date', 'Code', 'Venues', 'Status']]:
        # If the paper is marked as "Reading" in Notion and still "To Read" in Paperpile, it is not updated
        # if key == 'Status' and val == 'Reading' and key not in entry.keys():
        #     continue
        if isinstance(val, str):
            try:
                if entry[key]['value'] != val:
                    print(f"Found mismatching key '{key}' with values {entry[key]['value']} (Paperpile) and {val} (Notion)")
                    return False
            except KeyError:
                print(f"Attribute {key} found with value {val} in Notion, but missing in Paperpile.")
        elif isinstance(val, list):
            if any([x not in val for x in entry[key]['value']]):
                print(f"[bright_magenta]Found[/bright_magenta] mismatching key '{key}' with values {entry[key]['value']} (Paperpile) and {val} (Notion)")
                return False
    return True


def main(args: argparse.Namespace) -> None:
    """Main function"""
    # Load the configuration file
    with open(args.config, 'r') as ymlfile:
        cfg = yaml.safe_load(ymlfile)
    # Open CSV file
    csv_file = open(args.input, 'r+')
    csv_reader = csv.DictReader(csv_file)
    # Count length and reset pointer to beginning of file
    tot_input_values = len(list(csv_reader))
    csv_file.seek(0)
    # Query Notion database
    notion = NotionDBInterface(args.database, args.token)
    notion.query_database()
    print(f'[italic dark_orange3]Found {len(notion.pages)} pages on Notion and {tot_input_values} in the input dataset.[/italic dark_orange3]')
    # Iterate over CSV rows
    for i, row in enumerate(csv_reader):
        if i == 0:
            continue # Skip header
        # Remove BiBTeX capitalization
        row['Title'] = row['Title'].replace('{', '').replace('}','')
        matches = [
            hamming_distance(row['Title'].lower(), page['Title'].lower()) < args.max_distance
            for page in notion.pages
        ]
        matches_idxs = [i for i, val in enumerate(matches) if val]
        if len(matches_idxs) > 1:
            print(f'[dark_orange3]Skipping[/dark_orange3] [dodger_blue1]"{row["Title"]}"[/dodger_blue1]: multiple matches found.')
        else:
            match_curr_entry, curr_entry = format_entry(row, cfg['journals'], cfg['conferences'])

            # if match_curr_entry is None and curr_entry is None:
            #     print(f'[dark_orange3]Skipping[/dark_orange3] [dodger_blue1]"{row["Title"]}"[/dodger_blue1]: Link not available')
            #     continue

            if len(matches_idxs) == 0:
                print(f'[green]Adding[/green] [dodger_blue1]"{row["Title"]}"[/dodger_blue1]...')
                try:
                    notion.create_page(curr_entry)
                except ValueError as mess:
                    print(f"Value Error: {mess}")
            else:
                match = notion.pages[matches_idxs[0]]
                if not check_identical(match_curr_entry, match):
                    print(f'[bright_magenta]Updating[/bright_magenta] [dodger_blue1]{match["Title"]}[/dodger_blue1]...')
                    notion.update_page(match['id'], curr_entry)
                else:
                    print(f'[gold3]Skipping[/gold3] [dodger_blue1]"{row["Title"]}"[/dodger_blue1]: already in the Notion database.')
    print('\nDone!', ":tada:")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="CSV file to read", required=True)
    parser.add_argument("-c", "--config", help="Config file", required=True)
    parser.add_argument("-d", "--database", help="Database to update", required=True)
    parser.add_argument("-t", "--token", help="Notion API token", required=True)
    parser.add_argument("-m", "--max_distance", help="Maximum accepted Hamming distance for not filtering", default=1)
    args = parser.parse_args()
    main(args)
