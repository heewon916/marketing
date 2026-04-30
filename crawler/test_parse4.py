import re
with open('iframe_debug.html', 'r', encoding='utf-8') as f:
    text = f.read()

items = text.split('li class=\"UEzoS')[1:2]
for item in items:
    ids = re.findall(r'(\d{6,})', item)
    print('Potential IDs:', ids)
