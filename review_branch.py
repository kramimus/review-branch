#!/usr/bin/env python

'''
    Copyright 2011, Mark G. Whitney

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.


Given some set of ticket numbers, go through the git log on the
current branch, looking for the pattern: #<number> in the commit
messages.  For all the commits with messages that match one of the
given ticket numbers, pull those commits onto a new local branch named
based on the ticket numbers.  The branch name will be
"num1|num2|..._review".  The branch will start from the commit before
the first commit associated with the tickets.

The script works by cherry picking the commits for the original branch
to the new one, if there are conflicts, it will ignore them, check in
the conflicted change as-is, and keep going.

Once you are done with your code review, you would probably want to
delete the newly created review branch.
'''


import argparse
import git
import re
import sys


def get_commit_list(repo, tickets):
    """ Generate list of commits whose messages mention one of the
    given tickets
    """
    ticket_nums = "|".join(str(tic) for tic in tickets)
    ticket_re = re.compile("\#(%s)" % ticket_nums)

    commits = []
    for commit in repo.iter_commits():
        if (ticket_re.search(commit.message)):
            commits.append(commit)

    commits.reverse()
    return commits


def create_branch(repo, tickets, commits):
    """ Create review branch, switch to that branch, cherry pick
    commits over to it
    """
    ticket_nums = "|".join([str(tic) for tic in tickets])
    ticket_re = re.compile("\#(%s)" % ticket_nums)

    root = commits[0].parents[0]

    branch_name = "%s_review" % ticket_nums
    branch = repo.create_head(path=branch_name, commit=root)
    branch.checkout()

    for commit in commits:
        print commit.hexsha
        try:
            repo.git.cherry_pick(commit.hexsha)
        except git.GitCommandError:
            repo.git.add(".")
            repo.git.commit(C=commit.hexsha)

    print "You are now on branch %s" % branch_name
    print "The root commit you branched off at was %s" % root.hexsha
    print "To view changes for this ticket, try one of these:"
    print "  git log -u --stat %s..HEAD" % root.hexsha
    print "  git diff -u --stat %s..HEAD" % root.hexsha



def options():
    parser = argparse.ArgumentParser(description='git code reviewer')
    parser.add_argument('--repo',
                        type=str,
                        default='.',
                        help='path to repository')
    parser.add_argument('tickets',
                        type=int,
                        nargs='+',
                        help='ticket number(s) for review')
    return parser.parse_args()

def main():
    args = options()
    repo = git.Repo(args.repo)
    commits = get_commit_list(repo, args.tickets)
    if not commits:
        sys.exit("no commits associated with ticket(s) %s" %
                 " ".join(str(tic) for tic in args.tickets))

    create_branch(repo, args.tickets, commits)

if __name__ == "__main__":
    main()
