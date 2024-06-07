from abc import ABC, abstractmethod
from typing import List

from .util import indent, generate_tag
from .node import MarkdownNode, MarkdownNodeWithChildren, PageMetadata, to_html_entities
from .node import detect_paragraph_break, detect_list_item
from .context import PageMetadata, Context

def parse_block_content(content, parse_inline) -> List[MarkdownNode]:
    pos = 0
    result = []
    while pos < len(content):
        child, pos = parse_inline(content, pos)
        result.append(child)
    return result

class HeadingNode(MarkdownNodeWithChildren):
    def __init__(self):
        super().__init__()
        self.level = 0

    def parse(self, source: str, pos: int, parse_inline) -> int:
        content = ''
        while source[pos] == '#':
            self.level += 1
            pos += 1
        pos += 1
        while pos < len(source) and source[pos] != '\n':
            content += source[pos]
            pos += 1
        self.children.extend(parse_block_content(content, parse_inline))
        return pos

    def update_metadata(self, target: PageMetadata) -> None:
        if self.level == 1:
            target.title = self.get_text()
        super().update_metadata(target)

    def generate(self, context) -> str:
        return generate_tag(f'h{self.level}', {}, super().generate(context))

    def nested_repr(self, n: int):
        result =  f'{indent(n)}Heading(level={self.level}):\n'
        result += super().nested_repr(n)
        return result

class ParagraphNode(MarkdownNodeWithChildren):
    def __init__(self):
        super().__init__()

    def parse(self, source: str, pos: int, parse_inline) -> int:
        content = ''
        while pos < len(source):
            has_break, break_pos = detect_paragraph_break(source, pos)
            if has_break:
                pos = break_pos
                break
            content += source[pos]
            pos += 1
        self.children.extend(parse_block_content(content, parse_inline))
        return pos

    def generate(self, context) -> str:
        return generate_tag(f'p', {}, [super().generate(context).strip()])

    def nested_repr(self, n: int):
        result =  f'{indent(n)}Paragraph:\n'
        result += super().nested_repr(n)
        return result

class HorizontalRuleNode(MarkdownNode):
    def parse(self, source: str, pos: int, parse_inline) -> int:
        while source[pos] == '-':
            pos += 1
        return pos

    def get_text(self):
        return ''

    def generate(self, context) -> str:
        return generate_tag(f'hr', {})

    def nested_repr(self, n: int):
        result =  f'{indent(n)}HorizontalRule\n'
        return result

class ListItemNode(MarkdownNodeWithChildren):
    def __init__(self):
        super().__init__()

    def parse(self, source: str, pos: int, parse_inline) -> int:
        content = ''
        while pos < len(source):
            detected, _ordered =  detect_list_item(source, pos)
            if detected:
                break
            has_break, break_pos = detect_paragraph_break(source, pos)
            if has_break:
                break
            content += source[pos]
            pos += 1
        self.children.extend(parse_block_content(content, parse_inline))
        return pos

    def generate(self, context) -> str:
        return generate_tag(f'li', {}, super().generate(context))

    def nested_repr(self, n: int):
        result =  f'{indent(n)}ListItem:\n'
        result += super().nested_repr(n)
        return result

class ListNode(MarkdownNodeWithChildren):
    def __init__(self, ordered: bool, depth: int = 0):
        super().__init__()
        self.ordered = ordered
        self.depth = depth

    def parse(self, source: str, pos: int, parse_inline) -> int:
        while True:
            has_break, break_pos = detect_paragraph_break(source, pos)
            if has_break:
                if self.depth == 0:
                    pos = break_pos
                break

            has_list, ordered = detect_list_item(source, pos)
            if not has_list:
                break

            next_depth = 0
            while pos + next_depth < len(source) and source[pos + next_depth].isspace():
                next_depth += 1

            if next_depth > self.depth:
                child = ListNode(ordered, next_depth)
                pos = child.parse(source, pos, parse_inline)
                self.children.append(child)
                continue
            if next_depth < self.depth:
                break

            if ordered != self.ordered:
                break

            while pos < len(source) and source[pos].isspace():
                pos += 1

            if self.ordered:
                while source[pos] != '.':
                    pos += 1
            else:
                pos += 1
            pos += 1

            child = ListItemNode()
            pos = child.parse(source, pos, parse_inline)
            self.children.append(child)
        return pos

    def generate(self, context):
        return generate_tag('ol' if self.ordered else 'ul', {}, super().generate(context))

    def nested_repr(self, n: int):
        result =  f'{indent(n)}List(ordered={self.ordered}, depth={self.depth}):\n'
        result += super().nested_repr(n)
        return result

class BlockQuoteNode(MarkdownNodeWithChildren):
    def __init__(self):
        super().__init__()

    def parse(self, source: str, pos: int, parse_inline) -> int:
        content = ''
        pos += 2
        while pos < len(source):
            if source[pos:].startswith('\n> '):
                pos += 3
            elif source[pos] == '\n':
                break
            content += source[pos]
            pos += 1
        self.children.extend(parse_block_content(content, parse_inline))
        return pos

    def generate(self, context) -> str:
        return generate_tag(f'blockquote', {}, super().generate(context))

    def nested_repr(self, n: int):
        result =  f'{indent(n)}BlockQuote:\n'
        result += super().nested_repr(n)
        return result

class CodeBlockNode(MarkdownNode):
    def __init__(self, fenced: bool):
        self.content = ''
        self.fenced = fenced

    def parse(self, source: str, pos: int, _parse_inline) -> int:
        if self.fenced:
            while pos < len(source) and source[pos] != '\n':
                pos += 1
            pos += 1
            while pos < len(source) and not source[pos:].startswith('```'):
                self.content += source[pos]
                pos += 1
            pos += 3
            while pos < len(source) and source[pos] != '\n':
                pos += 1
        else:
            pos += 4
            while True:
                while pos < len(source) and source[pos] != '\n':
                    self.content += source[pos]
                    pos += 1
                self.content += source[pos]
                pos += 1
                if source[pos:].startswith(' ' * 4):
                    pos += 4
                else:
                    break
        self.content = self.content[:-1]
        return pos

    def get_text(self):
        return self.content

    def generate(self, context) -> str:
        return generate_tag('code', {}, [
            generate_tag('pre', {}, [
                to_html_entities(self.content)
            ])
        ])

    def nested_repr(self, n):
        return f'{indent(n)}CodeBlock({repr(self.content)})\n'
