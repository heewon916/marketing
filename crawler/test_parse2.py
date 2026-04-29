import re
with open('iframe_debug.html', 'r', encoding='utf-8') as f:
    text = f.read()

items = text.split('li class=\"UEzoS')[1:3]
for item in items:
    print('--- ITEM ---')
    links = re.findall(r'href="([^"]+)"', item)
    print('Links:', links)
