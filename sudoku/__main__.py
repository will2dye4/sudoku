import argparse
import os
import sys


def parse_args(args):
    # TODO
    parser = argparse.ArgumentParser()
    return parser.parse_args(args)


def main():
    args = parse_args(sys.argv[1:])
    print('Running main with args:', args)


def ku():
    if os.geteuid() != 0:
        print('ERROR! You are not root! Try running "sudo ku"')
        sys.exit(1)
    main()


if __name__ == '__main__':
    main()
