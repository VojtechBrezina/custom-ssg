import os
import sys
import random
import shutil
import re

from .util import indent, generate_tag
from .node import PageMetadata

class Context:
    def __init__(self, in_path, out_path, parse_all, parent = None):
        self.parent = parent
        self.in_path = in_path
        self.out_path = out_path
        self.depth = 0 if parent is None else parent.depth + 1
        self.parse_all = parse_all
        self.children = []

        if parent is None:
            self.used_ids = set()
            if os.path.exists(out_path):
                shutil.rmtree(out_path)
            os.mkdir(out_path)
            self.static_path = os.path.join(out_path, '_static')
            os.mkdir(self.static_path)
        else:
            self.static_path = parent.static_path

        print(f'{indent(self.depth)}Scanning {in_path}')
        sep_index = in_path[::-1].find(os.path.sep)
        if sep_index == -1:
            dirname = in_path
        else:
            dirname = in_path[::-1][:sep_index][::-1]

        template_path = os.path.join(self.in_path, '_template.md')
        self.template = '{{content}}'
        if os.path.isfile(template_path):
            print(f'{indent(self.depth)}- Found template')
            with open(template_path, 'r', encoding='UTF-8') as f:
                self.template = f.read()
            self.template = self.convert(self.template)
        if parent is not None:
            self.template = re.sub(
                r'(<p>\{\{content\}\}</p>)|(\{\{content\}\})',
                parent.template, self.template
            )

        self.styles = '' if self.parent is None else self.parent.styles
        styles_path = os.path.join(self.in_path, '_styles')
        if os.path.isdir(styles_path):
            bundle_name = f'{dirname}-{self.generate_id()}.css'
            bundle_path = os.path.join( self.static_path, bundle_name)
            print(f'{indent(self.depth)}- Found styles, generating {bundle_name}')
            self.styles += generate_tag('link', {
                'rel': 'stylesheet',
                'type': 'text/css',
                'href': f'/_static/{bundle_name}'
            })
            with open(bundle_path, 'w') as bundle_file:
                for stylesheet in os.listdir(styles_path):
                    path = os.path.join(styles_path, stylesheet)
                    print(f'{indent(self.depth)}  - {stylesheet}')
                    print(f'/* {path} */', file=bundle_file)
                    with open(path, 'r') as stylesheet_file:
                        print(stylesheet_file.read(), file=bundle_file)

        static_source_path = os.path.join(self.in_path, '_static')
        self.unused_assets = {}
        self.asset_names = {}
        if os.path.isdir(static_source_path):
            print(f'{indent(self.depth)}- Collecting static assets')
            for (dirpath, dirnames, filenames) in os.walk(static_source_path):
                for asset in filenames:
                    full_path = os.path.join(dirpath, asset)
                    asset_path = full_path.removeprefix(
                        os.path.join(self.in_path, '_static') + os.path.sep
                    )
                    print(f'{indent(self.depth)}  - {asset_path}')
                    self.unused_assets[asset_path] = full_path

    def convert(self, source: str, file_name = None, metadata = None) -> str:
        nodes = self.parse_all(source)
        if file_name is not None:
            with open(os.path.join(self.out_path, file_name.removesuffix('.md') + '.log'), 'w') as f:
                for node in nodes:
                    print(repr(node), file=f)

        if metadata is not None:
            for node in nodes:
                node.update_metadata(metadata)

        return ''.join(map(lambda node: node.generate(self), nodes))

    def get_asset_path(self, path):
        if path in self.unused_assets:
            converted_name = os.path.basename(path)
            suffix = ''
            dot_index = path[::-1].find('.')
            if dot_index != -1:
                suffix = path[::-1][:dot_index + 1][::-1]
            converted_name = converted_name.removesuffix(suffix)
            converted_name = f'{converted_name}-{self.generate_id()}{suffix}'
            print(f'{indent(self.depth)}  - Convert asset {path} -> {converted_name}')
            self.asset_names[path] = converted_name
            shutil.copy(self.unused_assets[path], os.path.join(self.static_path, converted_name))
            del self.unused_assets[path]

        if path in self.asset_names:
            return f'/_static/{self.asset_names[path]}'
        elif self.parent is not None:
            return self.parent.get_asset_path(path)
        else:
            print(f'{indent(self.depth)}  - Missing asset {path}')
            return None

    def generate_id(self):
        if self.parent is not None:
            return self.parent.generate_id()

        result = ''
        while True:
            result = ''.join(random.choices('0123456789abcdef', k=8))
            if result not in self.used_ids:
                break
        return result

    def make_child(self, dir):
        child = Context(os.path.join(self.in_path, dir), os.path.join(self.out_path, dir), self.parse_all, self)
        self.children.append(child)
        return child

    def convert_file(self, file_name: str):
        in_file = os.path.join(self.in_path, file_name)
        converted_file_name = file_name.removesuffix('.md') + '.html'
        out_file = os.path.join(self.out_path, converted_file_name)
        print(f'{indent(self.depth)}- Converting {in_file} to {out_file}', file=sys.stderr)

        source = ''
        with open(in_file, 'r', encoding='UTF-8') as f:
            source = f.read()

        metadata = PageMetadata(in_file)
        result = self.convert(source, file_name, metadata)
        result = self.template.replace('<p>{{content}}</p>', result).replace('{{content}}', result)

        output = '<!doctype html>' + generate_tag('html', {}, [
            generate_tag('head', {}, [
                generate_tag('title', {}, [metadata.title]),
                generate_tag('meta', {'charset': 'utf-8'}),
                self.styles
            ]),
            result
        ])

        with open(out_file, 'w') as f:
            print(output, end='', file=f)

    def process(self):
        print(f'{indent(self.depth)}Processing {self.in_path}')
        os.makedirs(self.out_path, exist_ok=True)

        dirs = []
        files = []
        for item in os.listdir(self.in_path):
            if item.startswith('_'):
                continue
            path = os.path.join(self.in_path, item)
            if os.path.isfile(path):
                files.append(item)
            elif os.path.isdir(path):
                dirs.append(item)

        for file in files:
            self.convert_file(file)

        for dir in dirs:
            child = self.make_child(dir)
            child.process()
