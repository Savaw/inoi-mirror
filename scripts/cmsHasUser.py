#!/usr/bin/python3
import argparse
import sys

from cms import utf8_decoder
from cms.db import SessionGen, User


def has_user(username):
    with SessionGen() as session:
        try:
            user = session.query(User).filter(User.username == username).first()
            if user is None:
                return 0
            return 1
        except:
            return 0


def main():
    parser = argparse.ArgumentParser(description="Checks that a user exists in CMS or not!")
    parser.add_argument("username", action="store", type=utf8_decoder,
                        help="username used to log in")

    args = parser.parse_args()

    print(has_user(args.username))

    return 0


if __name__ == "__main__":
    sys.exit(main())
