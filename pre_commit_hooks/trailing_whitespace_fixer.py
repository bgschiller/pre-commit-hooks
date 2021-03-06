from __future__ import print_function

import argparse
import fileinput
import platform
import sys

from pre_commit_hooks.util import cmd_output

REMOVE_WHITESPACE = "sed -i '' -e 's/[[:space:]]*$//'"
if platform.system() != 'Darwin':
    REMOVE_WHITESPACE = REMOVE_WHITESPACE.replace("-i ''", '-i')


def quote_file(fname):
    return "'{}'".format(fname)


def _fix_file(filename, markdown=False):
    for line in fileinput.input([filename], inplace=True):
        # preserve trailing two-space for non-blank lines in markdown files
        if markdown and (not line.isspace()) and (line.endswith("  \n")):
            line = line.rstrip(' \n')
            # only preserve if there are no trailing tabs or unusual whitespace
            if not line[-1].isspace():
                print(line + "  ")
                continue

        print(line.rstrip())


def fix_trailing_whitespace(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--no-markdown-linebreak-ext',
        action='store_const',
        const=[],
        default=argparse.SUPPRESS,
        dest='markdown_linebreak_ext',
        help='Do not preserve linebreak spaces in Markdown'
    )
    parser.add_argument(
        '--markdown-linebreak-ext',
        action='append',
        const='',
        default=['md,markdown'],
        metavar='*|EXT[,EXT,...]',
        nargs='?',
        help='Markdown extensions (or *) for linebreak spaces'
    )
    parser.add_argument('filenames', nargs='*', help='Filenames to fix')
    args = parser.parse_args(argv)

    bad_whitespace_files = cmd_output(
        'grep', '-l', '[[:space:]]$', *args.filenames, retcode=None
    ).strip().splitlines()

    md_args = args.markdown_linebreak_ext
    if '' in md_args:
        parser.error('--markdown-linebreak-ext requires a non-empty argument')
    all_markdown = '*' in md_args
    # normalize all extensions; split at ',', lowercase, and force 1 leading '.'
    md_exts = ['.' + x.lower().lstrip('.')
               for x in ','.join(md_args).split(',')]

    # reject probable "eaten" filename as extension (skip leading '.' with [1:])
    for ext in md_exts:
        if any(c in ext[1:] for c in r'./\:'):
            parser.error(
                "bad --markdown-linebreak-ext extension '{0}' (has . / \\ :)\n"
                "  (probably filename; use '--markdown-linebreak-ext=EXT')"
                .format(ext)
            )

    if bad_whitespace_files:
        print('Trailing Whitespace detected in: {0}'.format(', '.join(bad_whitespace_files)))

        print('psst, you can fix this by running')
        print("    ", REMOVE_WHITESPACE, ' '.join(map(quote_file, bad_whitespace_files)))
        return 1
    else:
        return 0


if __name__ == '__main__':
    sys.exit(fix_trailing_whitespace())
