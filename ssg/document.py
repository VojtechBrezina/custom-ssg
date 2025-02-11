"""A document representation."""

import copy
import os
import sys
import xml.etree.ElementTree as ET

import html5lib


class Document:
    """A fully built document with all the metadata resolved."""

    def __init__(
        self,
        /,
        source_path: str,
        dest_path,
        output_dir,
        content_dir,
        metadata: dict,
        tree: ET.ElementTree | None,
    ):
        self.source_path = source_path
        self.dest_path = dest_path
        self.output_dir = output_dir
        self.content_dir = content_dir
        self.metadata = metadata
        self.tree = tree
        self.children: list[Document] = []
        self.parent = None

        if self.tree is not None:
            Document._apply_ligatures(self.tree.getroot())

    def finalize(self):
        """Propagate inherited links and scripts and run python scripts."""

        inherited_elements = []
        if self.tree is not None:
            inherited_elements.extend(self.tree.findall(".//*[@data-inherit]"))

        for child in self.children:
            if child.tree is not None:
                for element in inherited_elements:
                    element = copy.deepcopy(element)
                    child.tree.find(element.get("data-inherit")).append(element)
        for element in inherited_elements:
            element.attrib.pop("data-inherit")

        if self.tree is None:
            return

        for link in self.tree.findall(".//link"):
            link.set("href", self._relativize(link.get("href")))

        for script in self.tree.findall(".//script"):
            if script.get("type", None) == "text/python":
                if "src" in script.attrib:
                    with open(script.get("src"), "r", encoding="UTF-8") as f:
                        code = f.read()
                else:
                    code = script.text

                exec(code, {"document": self})  # pylint: disable=exec-used

            else:
                if "src" in script:
                    script.set("src", self._relativize(script.get("src")))

        for anchor in self.tree.findall(".//a"):
            if "href" in anchor.attrib:  # Anchors don't have to link anywhere.
                anchor.set("href", self._relativize(anchor.get("href")))

        for parent in self.tree.findall('.//script[@type="text/python"]/..'):
            for script in parent.findall('./script[@type="text/python"]'):
                parent.remove(script)
        for child in self.children:
            child.finalize()

    def _relativize(self, absolute_path):
        """
        Generate a relative path that uses slashes instead of the OS specific
        separator.
        """

        if absolute_path.startswith("http://") or absolute_path.startswith("https://"):
            return absolute_path

        if absolute_path.endswith(".md"):
            absolute_path = absolute_path.removesuffix(".md") + ".html"

        relative_path = os.path.relpath(
            os.path.join(self.output_dir, absolute_path),
            os.path.dirname(self.dest_path),
        )
        result = ""
        while relative_path != "":
            relative_path, basename = os.path.split(relative_path)

            if result == "":
                result = basename
            else:
                result = basename + "/" + result

        return result

    def write(self):
        """Write self and all children to disk."""
        for child in self.children:
            child.write()

        if self.tree is None or "draft" in self.metadata:
            return

        result = b"<!DOCTYPE html>" + html5lib.serialize(
            self.tree.getroot(),
            "etree",
            encoding="UTF-8",
            quote_attr_values="spec",
            strip_whitespace=True,
            omit_optional_tags=False,  # No, they are not optional for **serializers**
            inject_meta_charset=True,
        )

        os.makedirs(os.path.dirname(self.dest_path), exist_ok=True)
        with open(self.dest_path, "w", encoding="UTF-8") as f:
            f.write(result.decode("UTF-8"))

    @staticmethod
    def _apply_ligatures(element: ET.Element) -> None:
        def filter(text: str) -> str:
            return (
                text.replace("---", "\u2014")
                .replace("--", "\u2013")
                .replace("...", "\u2026")
            )

        if element.text is not None:
            element.text = filter(element.text)

        if element.tail is not None:
            element.tail = filter(element.tail)

        for child in element.findall("./*"):
            Document._apply_ligatures(child)
