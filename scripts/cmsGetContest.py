import argparse
import json

from cms.db import SessionGen, Contest, Task, Participation


def main():
    parser = argparse.ArgumentParser(
        description="Prints the data of a CMS contest",
    )
    parser.add_argument(
        'contest_id',
        type=int,
        help='Id of the contest',
    )
    args = parser.parse_args()
    cid = args.contest_id
    data = {
        'success': False,
        'name': '',
        'participants': 0,
        'tasks': list(),
    }

    with SessionGen() as session:
        contest = Contest.get_from_id(cid, session)
        if contest is None:
            print(json.dumps(data))
            return 1

        data['name'] = contest.name
        data['participants'] = session.query(Participation).filter(
            Participation.contest_id == cid
        ).count()

        tasks = session.query(Task).filter(
            Task.contest_id == cid
        ).all()
        for task in tasks:
            data['tasks'].append({
                'name': task.name,
                'title': task.title,
            })

    data['success'] = True
    print(json.dumps(data))
    return 0


if __name__ == '__main__':
    exit(main())
