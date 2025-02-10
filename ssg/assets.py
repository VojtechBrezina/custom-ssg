"""
Assets like stylesheets, images and scripts live in a special @assets
subdirectory and are hashed to make caching easy on simple servers.
"""

import shutil
import sys
import os

import hashlib


class AssetManager:
    """The class that remembers resolved paths."""

    def __init__(self, content_dir: str, output_dir: str) -> None:
        self.content_dir = content_dir
        self.asset_dir = os.path.join(output_dir, "@assets")

        self.lookup = {}

        os.makedirs(self.asset_dir, exist_ok=True)

    def translate(self, target: str) -> str:
        """
        Generate the asset for `target` and return its path relative to the
        output directory.
        """

        if target.startswith("http://") or target.startswith("https://"):
            return target

        if target in self.lookup:
            return self.lookup[target]

        with open(os.path.join(self.content_dir, target), "rb") as f:
            sha1 = hashlib.sha1()

            while True:
                data = f.read(1 << 16)
                if not data:
                    break
                sha1.update(data)

        resolved = f"{sha1.hexdigest()[-8:]}-{os.path.basename(target)}"
        shutil.copy(
            os.path.join(self.content_dir, target),
            os.path.join(self.asset_dir, resolved),
        )

        resolved = os.path.join("@assets", resolved)
        self.lookup[target] = resolved
        return resolved

    def clean_up(self):
        """Remove all unused assets from the output directory."""
        print("Asset clean up:")

        used = set(self.lookup.values())

        total = 0
        removed = 0

        for item in os.listdir(self.asset_dir):
            resolved_item = os.path.join(self.asset_dir, item)
            if not os.path.isfile(resolved_item):
                print(
                    f"Warning: Consider removing {resolved_item}, it should't be in the output."
                )
                continue

            total += 1
            if os.path.join("@assets", item) not in used:
                removed += 1
                print("-", item)
                os.remove(resolved_item)

        print(f"Removed {removed}/{total} ({len(used)} still in use)", file=sys.stderr)
