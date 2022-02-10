from typing import Dict, List


def match(string, candidates) -> str:
    for c in candidates:
        if c[0].lower() in string.lower() or c[1].lower() in string.lower():
            return c
    for c in candidates:
        if string.lower() in c[0].lower() or string.lower() in c[1].lower():
            return c
    return [None, None]


def format_entry(entry: Dict[str, str], journals: List[Dict[str, str]], conferences: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    """ Produces a dictionary in format column_name: {type: x, value: y} for each value in the entry"""

    ########## VENUE ################################
    conference_tuple = [ [c['short'], c['name']] for c in conferences]

    # Select the conference shortname based on proceedings
    if entry['Item type'] == 'Journal Article':
        if 'Full journal' in entry.keys() and entry['Full journal']:
            venue = [j['short'] for j in journals if j['name'] == entry['Full journal'].strip()]
        else:
            venue = [j['short'] for j in journals if j['name'] == entry['Journal'].strip()]
        if not venue:
            venue = [entry['Journal'].strip()[:100]]
    elif entry['Item type'] == 'Conference Paper':
        venue = [
            c['short'] for c in conferences if c['name'] == match(
            entry['Proceedings title'].strip().replace('{','').replace('}',''), conference_tuple
        )[1]]
        if not venue:
            venue = [entry['Proceedings title'].strip()[:100]]
    elif entry['Item type'] == 'Preprint Manuscript':
        if "openreview" in entry['URLs'].strip().split(';')[0]:
            venue = ["OpenReview"]
        else:
            venue = [entry['Archive prefix'].strip()]
    elif entry['Item type'] == 'Book Chapter':
        venue = [entry['Book title'].strip()]
    else:
        venue = []

    # Arxiv links are privileged
    links = [x for x in entry['URLs'].strip().split(';')]
    arxiv_links = [x for x in links if 'arxiv' in x]
    if len(arxiv_links) > 0:
        selected_link = arxiv_links[0]
        venue.append('arXiv')
    else:
        selected_link = links[0]

    # Multichoice don't accept commas and maybe other punctuation, too
    for i, v in enumerate(venue):
        exclude = set([','])
        venue[i] = ''.join(ch for ch in v if ch not in exclude)

    ###################################################

    ############## DATE #################################

    date = ''
    if 'Date published' in entry.keys():
        if entry['Date published'].strip() != '':
            date = entry['Date published'].strip()

    if date == '':
        if 'Publication year' in entry.keys():
            if entry['Publication year'].strip() != '':
                date = entry['Publication year'].strip() + '-01-01'
    
    if len(date) > 10: # YYYY-MM-DD....
        date = date[:10]

    if len(date) == 4: # YYYY
        date = entry['Publication year'].strip() + '-01-01'
    
    if len(date) == 7: # YYYY-MM
        date = date + '-01'
    
    if date == '':
        date = '2000-01-01'

    ######################################################


    all_labels = [x.strip() for x in entry['Labels filed in'].strip().split(';')]
    all_folders = [x.strip() for x in entry['Folders filed in'].strip().split(';')]

    if len(all_labels) == 1 and len(all_labels[0]) == 0:
        all_labels = []
    if len(all_folders) == 1 and len(all_folders[0]) == 0:
        all_folders = []

    # categories = [x for x in all_labels if ' - ' not in x]
    # methods = [x.split(' - ')[1] for x in all_labels if ' - ' in x]

    formatted_entry = {
        'Item type':  {'type': 'select',       'value': entry['Item type'].strip()},
        'Authors':    {'type': 'multi_select', 'value': entry['Authors'].strip().split(',')},
        'Title':      {'type': 'title',        'value': entry['Title'].strip().replace('{','').replace('}','')},
        'Venues':     {'type': 'multi_select', 'value': venue},
        'Date':       {'type': 'date',         'value': date},
        'Link':       {'type': 'url',          'value': selected_link},
        'Labels': {'type': 'multi_select', 'value': all_labels}, #, 'color': [COLOR_MAP[cat]['color'] for cat in categories]}
        'Folders': {'type': 'multi_select', 'value': all_folders}
    }

    # if "reading-list" in all_labels:
    status_value = 'to-be-read'

    formatted_entry['Status'] = {'type': 'select', 'value': status_value}

    filtered_formatted_entry = formatted_entry.copy()
    keys_delete = []
    for key, value in filtered_formatted_entry.items():
        if value["value"] in ['', "", [], [''], [""]]:
            keys_delete.append(key)
    
    for key in keys_delete:
        del filtered_formatted_entry[key]

    return formatted_entry, filtered_formatted_entry
