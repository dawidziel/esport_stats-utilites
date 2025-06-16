import re

def get_filename_url_to_open(site, filename, size=None):
    pattern = r'.*src\=\"(.+?)\".*'
    size = '|' + str(size) + 'px' if size else ''
    to_parse_text = '[[File:{}|link=%s]]'.format(filename, size)
    result = site.api('parse', title='Main Page',
                    text=to_parse_text, disablelimitreport=1)
    parse_result_text = result['parse']['text']['*']
    url = re.match(pattern, parse_result_text)[1]
    return url
