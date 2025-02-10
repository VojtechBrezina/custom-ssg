"""A custom SSG based on Pandoc markdown"""

import argparse
import os
import sys

from ssg.generator import Generator


def build_arg_parser():
    """Define CLI options."""

    parser = argparse.ArgumentParser(prog="ssg")
    parser.add_argument("-C", "--workdir", default=".", dest="workdir")

    subparsers = parser.add_subparsers(title="Actions", required=True)

    build_parser = subparsers.add_parser("build", help="Update the website.")
    build_parser.set_defaults(action="build")

    return parser


def main():
    """Entrypoint"""

    args = build_arg_parser().parse_args(sys.argv[1:])

    generator = Generator(os.path.abspath(args.workdir))

    match args.action:
        case "build":
            generator.build()


if __name__ == "__main__":
    main()
