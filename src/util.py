def indent(n: int):
    return ' ' * (4 * n)

def generate_tag(tag: str, attrs: dict, children: list = []):
    attr_result = ''
    for key in attrs:
        attr_result += f' {key}="{attrs[key]}"'

    if tag in ['img', 'hr', 'meta', 'link']:
        return f'<{tag}{attr_result}>'
    else:
        content = ''.join(children)
        return f'<{tag}{attr_result}>{content}</{tag}>'
