import re
with open('iframe_debug.html', 'r', encoding='utf-8') as f:
    text = f.read()

items = text.split('li class=\"UEzoS')[1:2]
for item in items:
    attrs = re.findall(r'(\S+=\"[^\"]*\")', item)
    for attr in attrs:
        if 'data' in attr or 'href' in attr or 'id' in attr:
            print(attr)
