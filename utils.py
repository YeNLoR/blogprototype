import re
import markdown
import bleach

def search_parser(search_string):
    search_dict = {}
    if not search_string:
        return search_dict
    for item in search_string.split(','):
        item = item.strip()
        if not item:
            continue
    parts = item.split(':',1)
    if len(parts) == 2:
        key = parts[0].strip()
        value = parts[1].strip()
        if key.lower() in['user', 'post', 'tags']:
            search_dict[key.lower()] = value
    return search_dict

def check_password(password):
    if not len(password) >= 8 and len(password) <= 16:
        return False
    if not re.match(r'^[A-Za-z0-9_-]*$', password):
        return False
    return True

def get_tag_list(tags_string):
    if not tags_string:
        return []
    tags_list = {
        tag.strip().lower()
        for tag in tags_string.split(',')
        if tag.strip()
    }
    return tags_list

def process_content(content):
    html_content = markdown.markdown(content)
    allowed_tags = [
        'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6' 'ul', 'ol', 'li', 'pre',
        'code', 'blockquote', 'a', 'strong', 'u', 's', 'del', 'em', 'img', 'br',
    ]
    allowed_attrs = {
        'a': ['href', 'title'],
        'img': ['src', 'alt'],
    }
    safe_content = bleach.clean(
        html_content,
        tags=allowed_tags,
        attributes=allowed_attrs,
        strip=True
    )
    return safe_content