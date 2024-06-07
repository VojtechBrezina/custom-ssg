from abc import ABC, abstractmethod

class PageMetadata:
    def __init__(self, path):
        self.title = path

class MarkdownNode(ABC):
    @abstractmethod
    def parse(self, source: str, pos: int, parse_inline) -> int:
        pass

    def update_metadata(self, target: PageMetadata) -> None:
        pass

    @abstractmethod
    def get_text(self) -> str:
        pass

    @abstractmethod
    def generate(self, context) -> str:
        pass

    @abstractmethod
    def nested_repr(self, n: int):
        pass

    def __repr__(self):
        return self.nested_repr(0)

class MarkdownNodeWithChildren(MarkdownNode):
    def __init__(self):
        self.children = []

    def update_metadata(self, target: PageMetadata) -> None:
        for node in self.children:
            node.update_metadata(target)

    def get_text(self) -> str:
        return ''.join(map(lambda node: node.get_text(), self.children))

    def generate(self, context) -> str:
        return ''.join(map(lambda node: node.generate(context), self.children))

    def nested_repr(self, n: int):
        result =  ''
        for child in self.children:
            result += child.nested_repr(n + 1)
        return result

def detect_paragraph_break(source: str, pos: int) -> (bool, int | None):
    if pos >= len(source) or source[pos] != '\n':
        return False, None
    pos += 1
    while pos < len(source) and source[pos].isspace() and source[pos] != '\n':
        pos += 1
    return pos < len(source) and source[pos] == '\n', pos + 1

def detect_list_item(source: str, pos: int) -> (bool, bool | None):
    while pos < len(source) and source[pos] == ' ':
        pos += 1

    if pos >= len(source):
        return False, None

    if source[pos:].startswith('* ') or source[pos:].startswith('- '):
        return True, False

    if not source[pos].isdigit():
        return False, None
    pos += 1

    while pos < len(source) and source[pos].isdigit():
        pos += 1

    if pos >= len(source):
        return False, None

    if source[pos:].startswith('. '):
        return True, True
    return False, None

def to_html_entities(text: str) -> str:
    return text.replace('<', '&lt;').replace('>', '&gt;')
