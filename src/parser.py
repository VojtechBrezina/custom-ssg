from .inline_node import *
from .block_node import *
from .node import detect_paragraph_break, detect_list_item
from typing import List

def parse_inline(source: str, pos: int) -> (MarkdownNode, int):
    result = None
    if source[pos:].startswith('**') or source[pos:].startswith('__'):
        result = BoldNode()
    elif source[pos:].startswith('~~'):
        result = StrikeOutNode()
    elif source[pos:].startswith('!['):
        result = ImageNode()
    elif source[pos] in '*_':
        result = ItalicNode()
    elif source[pos] == '`':
        result = CodeNode()
    elif source[pos] == '[':
        result = AnchorNode()
    else:
        result = PlainTextNode()

    pos = result.parse(source, pos, parse_inline)
    return result, pos

def parse_block(source: str, pos: int) -> (MarkdownNode, int):
    while (
        pos < len(source) and source[pos].isspace() and
        not source[pos:].startswith(' ' * 4)
    ):
        pos += 1

    has_list, list_is_ordered = detect_list_item(source, pos)

    if has_list:
        result = ListNode(list_is_ordered)
    elif (
        source[pos:].startswith('# ') or
        source[pos:].startswith('## ') or
        source[pos:].startswith('### ') or
        source[pos:].startswith('#### ') or
        source[pos:].startswith('##### ') or
        source[pos:].startswith('###### ')
    ):
        result = HeadingNode()
    elif source[pos:].startswith('---'):
        result = HorizontalRuleNode()
    elif source[pos:].startswith('> '):
        result = BlockQuoteNode()
    elif source[pos:].startswith(' ' * 4):
        result = CodeBlockNode(False)
    elif source[pos:].startswith('```'):
        result = CodeBlockNode(True)
    else:
        result = ParagraphNode()

    pos = result.parse(source, pos, parse_inline)
    return result, pos

def parse_all(source: str) -> List[MarkdownNode]:
    result = []
    pos = 0
    while pos < len(source):
        block, pos = parse_block(source, pos)
        result.append(block)
    return result
