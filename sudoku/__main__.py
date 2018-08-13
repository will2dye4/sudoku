import argparse
import sys


def parse_args(args):
    # TODO
    parser = argparse.ArgumentParser()
    return parser.parse_args(args)


def main():
    args = parse_args(sys.argv[1:])
    print('Running main with args:', args)


if __name__ == '__main__':
    main()
