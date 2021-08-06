from django.core.management.base import BaseCommand
from cms_register.models import Contest, Problem
from cms_register.utils import cms_get_contest_data


class Command(BaseCommand):
    help = 'Fetch problemset data from CMS and update database'

    def handle(self, *args, **options):
        for contest in Contest.objects.all():
            cdata = cms_get_contest_data(contest.cms_id)
            if cdata is None:
                print(f'Contest with id={contest.cms_id} not found')
                continue
            print(f'Update contest #{contest.cms_id}<{cdata.name}>')
            contest.cms_name = cdata.name
            contest.participants_count = cdata.participants
            contest.save()

            for pdata in cdata.problems:
                queryset = Problem.objects.filter(
                    contest=contest,
                    cms_name=pdata.name,
                )
                if queryset.count() == 0:
                    print(f'Add problem {pdata.name}')
                    problem = Problem(
                        contest=contest,
                        cms_name=pdata.name,
                        public_name=pdata.title,
                    )
                    problem.save()
                else:
                    problem = queryset.first()
                    if problem.public_name:
                        print(f'Skip problem {pdata.name}')
                    else:
                        print(f'Update problem {pdata.name}')
                        problem.public_name = pdata.title
                        problem.save()

        return
