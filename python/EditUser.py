from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import logging
import sys

from cms import utf8_decoder
from cms.db import SessionGen, User

logger = logging.getLogger(__name__)


def edit_user(first_name, last_name, username, password, email, timezone, preferred_languages):
    logger.info("Edit a user in the database.")
    with SessionGen() as session:
        user = session.query(User).filter(User.username == username).first()
        if user is None:
            logger.error("User %s does not exist!", username)
            return False
        if not first_name is None:
            user.first_name = first_name
        if not last_name is None:
            user.last_name = last_name
        if not email is None:
            user.email = email
        if not password is None:
            user.password = password
        session.commit()
        logger.info("User %s edited sucsessfully.", username)
        return True


def main():
    parser = argparse.ArgumentParser(description="Edit a user of CMS.")
    parser.add_argument("username", action="store", type=utf8_decoder,
                        help="username used to log in")
    parser.add_argument("-fn", "--firstname", action="store", type=utf8_decoder,
                        help="given name of the user")
    parser.add_argument("-ln", "--lastname", action="store", type=utf8_decoder,
                        help="family name of the user")
    parser.add_argument("-p", "--password", action="store", type=utf8_decoder,
                        help="password")
    parser.add_argument("-e", "--email", action="store", type=utf8_decoder,
                        help="email of the user")
    parser.add_argument("-t", "--timezone", action="store", type=utf8_decoder,
                        help="timezone of the user, e.g. Europe/London")
    parser.add_argument("-l", "--languages", action="store", type=utf8_decoder,
                        help="comma-separated list of preferred languages")

    args = parser.parse_args()

    return edit_user(args.firstname, args.lastname,
                     args.username, args.password, args.email,
                     args.timezone, args.languages)


if __name__ == "__main__":
    sys.exit(0 if main() is True else 1)
