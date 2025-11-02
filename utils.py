import re
import markdown
import bleach

def check_password(password):
    if not len(password) >= 8 and len(password) <= 16:
        return False
    if not re.match(r'^[A-Za-z0-9_-]*$', password):
        return False
    return True

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