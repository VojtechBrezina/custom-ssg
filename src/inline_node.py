from abc import ABC, abstractmethod
from .util import indent, generate_tag
from .node import MarkdownNode, MarkdownNodeWithChildren, PageMetadata, to_html_entities
from .context import Context

class PlainTextNode(MarkdownNode):
    def __init__(self):
        self.content = ''

    def parse(self, source: str, pos: int, _parse_inline) -> int:
        while not (
            pos >= len(source) or
            source[pos] in '*_`[]' or
            source[pos:].startswith('![') or
            source[pos:].startswith('~~')
        ):
            if source[pos].isspace():
                if len(self.content) == 0 or self.content[-1] != ' ':
                    self.content += ' '
            else:
                self.content += source[pos]
            pos += 1
        return pos

    def get_text(self):
        return self.content

    def generate(self, context) -> str:
        return self.content

    def nested_repr(self, n):
        return f'{indent(n)}Plain({repr(self.content)})\n'

class SimpleWrapperNode(MarkdownNodeWithChildren):
    def __init__(self, mark_length, tag, name):
        super().__init__()
        self.mark_length = mark_length
        self.tag = tag
        self.name = name

    def parse(self, source: str, pos: int, parse_inline) -> int:
        style = source[pos:pos+self.mark_length]
        pos += self.mark_length
        while pos < len(source):
            if source[pos:].startswith(style):
                pos += self.mark_length
                break
            child, pos = parse_inline(source, pos)
            self.children.append(child)
        return pos

    def generate(self, context) -> str:
        return generate_tag(self.tag, {}, super().generate(context))

    def nested_repr(self, n):
        result =  f'{indent(n)}{self.name}:\n'
        result += super().nested_repr(n)
        return result


class BoldNode(SimpleWrapperNode):
    def __init__(self):
        super().__init__(2, 'strong', 'Bold')

class ItalicNode(SimpleWrapperNode):
    def __init__(self):
        super().__init__(1, 'i', 'Italic')

class StrikeOutNode(SimpleWrapperNode):
    def __init__(self):
        super().__init__(2, 'del', 'StrikeOut')

class CodeNode(MarkdownNode):
    def __init__(self):
        self.content = ''

    def parse(self, source: str, pos: int, _parse_inline) -> int:
        pos += 1
        while source[pos] != '`':
            self.content += source[pos]
            pos += 1
        pos += 1
        return pos

    def get_text(self):
        return self.content

    def generate(self, context) -> str:
        return generate_tag('code', {}, [
            to_html_entities(self.content)
        ])

    def nested_repr(self, n):
        return f'{indent(n)}Code({repr(self.content)})\n'

class AnchorNode(MarkdownNodeWithChildren):
    def __init__(self):
        super().__init__()
        self.href = ''

    def parse(self, source: str, pos: int, parse_inline) -> int:
        pos += 1
        while True:
            if source[pos] == ']':
                pos += 2
                break
            child, pos = parse_inline(source, pos)
            self.children.append(child)
        while True:
            if source[pos] == ')':
                pos += 1
                break
            self.href += source[pos]
            pos += 1
        return pos

    def generate(self, context) -> str:
        converted_href = ''
        if (
            self.href.startswith('http://') or
            self.href.startswith('https://') or
            self.href.endswith('/')
        ):
            converted_href = self.href
        elif self.href.startswith('asset://'):
            converted_href = context.get_asset_path(self.href.removeprefix('asset://'))
        else:
            converted_href = self.href.removesuffix('.md') + '.html'
        return generate_tag(
            'a',
            {'href': converted_href},
            super().generate(context)
        )

    def nested_repr(self, n):
        result =  f'{indent(n)}Anchor(href="{self.href}"):\n'
        result += super().nested_repr(n)
        return result

class ImageNode(MarkdownNode):
    def __init__(self):
        self.src = ''
        self.alt = None
        self.title = None

    def parse(self, source: str, pos: int, parse_inline) -> int:
        pos += 2
        while True:
            if source[pos] == ']':
                pos += 2
                break
            if self.alt is None:
                self.alt = ''
            self.alt += source[pos]
            pos += 1
        title = False
        junk = False
        while True:
            if title:
                if source[pos] == '"':
                    title = False
                    junk = True
                else: 
                    if self.title is None:
                        self.title = ''
                    self.title += source[pos]
            else:
                if source[pos] == ')':
                    pos += 1
                    break
                elif source[pos] == '"':
                    title = True
                elif not junk and  not source[pos].isspace():
                    self.src += source[pos]
            pos += 1
        return pos

    def get_text(self):
        return self.alt

    def generate(self, context) -> str:
        src = context.get_asset_path(self.src)

        attrs = {} 
        if src is not None:
            attrs['src'] = src
        if self.alt is not None:
            attrs['alt'] = self.alt
        if self.title is not None:
            attrs['title'] = self.title
        return generate_tag('img', attrs)

    def nested_repr(self, n):
        result = f'{indent(n)}Image(src="{self.src}"'
        if self.alt is not None:
            result += f', alt="{self.alt}"'
        if self.title is not None:
            result += f', title="{self.title}"'
        result +=  ')\n'
        return result
