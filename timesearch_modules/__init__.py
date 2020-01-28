import argparse
import sys

from . import exceptions

# NOTE: Originally I wanted the docstring for each module to be within their
# file. However, this means that composing the global helptext would require
# importing those modules, which will subsequently import PRAW and a whole lot
# of other things. This made TS very slow to load which is okay when you're
# actually using it but really terrible when you're just viewing the help text.
DOCSTRING = '''
Timesearch
The subreddit archiver

The basics:
1. Collect a subreddit's submissions
    > timesearch.py get_submissions -r subredditname

2. Collect the comments for those submissions
    > timesearch.py get_comments -r subredditname

3. Stay up-to-date
    > timesearch.py livestream -r subredditname


Commands for collecting:
{get_submissions}
{get_comments}
{livestream}
{getstyles}
{getwiki}

Commands for processing:
{offline_reading}
{index}
{breakdown}
{mergedb}

TO SEE DETAILS ON EACH COMMAND, RUN
> timesearch.py <command>
'''

MODULE_DOCSTRINGS = {
    'breakdown': '''
breakdown:
    Give the comment / submission counts for users in a subreddit, or
    the subreddits that a user posts to.

    Automatically dumps into a <database>_breakdown.json file
    in the same directory as the database.

    > timesearch.py breakdown -r subredditname <flags>
    > timesearch.py breakdown -u username <flags>

    flags:
    -r "test" | --subreddit "test":
        The subreddit database to break down.

    -u "test" | --username "test":
        The username database to break down.

    --sort "name" | "submissions" | "comments" | "total_posts"
        Sort the output.
''',

    'get_comments': '''
get_comments:
    Collect comments on a subreddit or comments made by a user.

    > timesearch.py get_comments -r subredditname <flags>
    > timesearch.py get_comments -u username <flags>

    flags:
    -s "t3_xxxxxx" | --specific "t3_xxxxxx":
        Given a submission ID, t3_xxxxxx, scan only that submission.

    -l "update" | --lower "update":
        If a number - the unix timestamp to start at.
        If "update" - continue from latest comment in db.
        Default: update

    -up 1467460221 | --upper 1467460221:
        If a number - the unix timestamp to stop at.
        If not provided - stop at current time.
        Default: current time

    --dont_supplement:
        If provided, trust the pushshift data and do not fetch live copies
        from reddit.

    -v | --verbose:
        If provided, print extra information to the screen.
''',

    'getstyles': '''
getstyles:
    Collect the stylesheet, and css images.

    > timesearch.py getstyles -r subredditname
''',

    'getwiki': '''
getwiki:
    Collect all available wiki pages.

    > timesearch.py getwiki -r subredditname
''',

    'mergedb': '''
mergedb:
    Copy all new posts from one timesearch database into another.

    > timesearch mergedb --from redditdev1.db --to redditdev2.db

    flags:
    --from:
        The database file containing the posts you wish to copy.

    --to:
        The database file to which you will copy the posts.
        The database is modified in-place.
        Existing posts will be ignored and not updated.
''',

    'livestream': '''
livestream:
    Continously collect submissions and/or comments.

    > timesearch.py livestream -r subredditname <flags>
    > timesearch.py livestream -u username <flags>

    flags:
    -r "test" | --subreddit "test":
        The subreddit to collect from.

    -u "test" | --username "test":
        The redditor to collect from.

    -s | --submissions:
        If provided, do collect submissions. Otherwise don't.

    -c | --comments:
        If provided, do collect comments. Otherwise don't.

    If submissions and comments are BOTH left unspecified, then they will
    BOTH be collected.

    -v | --verbose:
        If provided, print extra information to the screen.

    -w 30 | --wait 30:
        The number of seconds to wait between cycles.

    -1 | --once:
        If provided, only do a single loop. Otherwise go forever.
''',

    'offline_reading': '''
offline_reading:
    Render submissions and comment threads to HTML via Markdown.

    > timesearch.py offline_reading -r subredditname <flags>
    > timesearch.py offline_reading -u username <flags>

    flags:
    -s "t3_xxxxxx" | --specific "t3_xxxxxx":
        Given a submission ID, t3_xxxxxx, render only that submission.
        Otherwise render every submission in the database.
''',

    'index': '''
index:
    Dump submission listings to a plaintext or HTML file.

    > timesearch.py index -r subredditname <flags>
    > timesearch.py index -u username <flags>

    flags:
    -r "test" | --subreddit "test":
        The subreddit database to dump

    -u "test" | --username "test":
        The username database to dump

    --html:
        Write HTML files instead of plain text.

    --offline:
        The links in the mash will point to the files generated by
        offline_reading. That is, `../offline_reading/fullname.html` instead
        of `http://redd.it/id`. This will NOT trigger offline_reading to
        generate the files now, so you must run that tool separately.

    -st 50 | --score_threshold 50:
        Only mash posts with at least this many points.
        Applies to ALL mashes!

    --all:
        Perform all of the mashes listed below.

    --date:
        Perform a mash sorted by date.

    --title:
        Perform a mash sorted by title.

    --score:
        Perform a mash sorted by score.

    --author:
        For subreddit databases only.
        Perform a mash sorted by author.

    --sub:
        For username databases only.
        Perform a mash sorted by subreddit.

    --flair:
        Perform a mash sorted by flair.

    examples:
        `timesearch index -r botwatch --date`
        does only the date file.

        `timesearch index -r botwatch --score --title`
        does both the score and title files.

        `timesearch index -r botwatch --score --score_threshold 50`
        only shows submissions with >= 50 points.

        `timesearch index -r botwatch --all`
        performs all of the different mashes.
''',

    'get_submissions': '''
get_submissions:
    Collect submissions from the subreddit across all of history, or
    Collect submissions by a user (as many as possible).

    > timesearch.py get_submissions -r subredditname <flags>
    > timesearch.py get_submissions -u username <flags>

    -r "test" | --subreddit "test":
        The subreddit to scan. Mutually exclusive with username.

    -u "test" | --username "test":
        The user to scan. Mutually exclusive with subreddit.

    -l "update" | --lower "update":
        If a number - the unix timestamp to start at.
        If "update" - continue from latest submission in db.
        Default: update

    -up 1467460221 | --upper 1467460221:
        If a number - the unix timestamp to stop at.
        If not provided - stop at current time.
        Default: current time

    --dont_supplement:
        If provided, trust the pushshift data and do not fetch live copies
        from reddit.

    -v | --verbose:
        If provided, print extra information to the screen.
''',
}

OLD_COMMAND_ALIASES = {
    'timesearch': 'get_submissions',
    'commentaugment': 'get_comments',
    'redmash': 'index',
}


def docstring_preview(text):
    '''
    Return the brief description at the top of the text.
    User can get full text by looking at each specifically.
    '''
    return text.split('\n\n')[0]

def listget(li, index, fallback=None):
    try:
        return li[index]
    except IndexError:
        return fallback

def indent(text, spaces=4):
    spaces = ' ' * spaces
    return '\n'.join(spaces + line if line.strip() != '' else line for line in text.split('\n'))

docstring_headers = {
    key: indent(docstring_preview(value))
    for (key, value) in MODULE_DOCSTRINGS.items()
}

DOCSTRING = DOCSTRING.format(**docstring_headers)

####################################################################################################
####################################################################################################

def breakdown_gateway(args):
    from . import breakdown
    breakdown.breakdown_argparse(args)

def get_comments_gateway(args):
    from . import get_comments
    get_comments.get_comments_argparse(args)

def getstyles_gateway(args):
    from . import getstyles
    getstyles.getstyles_argparse(args)

def getwiki_gateway(args):
    from . import getwiki
    getwiki.getwiki_argparse(args)

def livestream_gateway(args):
    from . import livestream
    livestream.livestream_argparse(args)

def mergedb_gateway(args):
    from . import mergedb
    mergedb.mergedb_argparse(args)

def offline_reading_gateway(args):
    from . import offline_reading
    offline_reading.offline_reading_argparse(args)

def index_gateway(args):
    from . import index
    index.index_argparse(args)

def get_submissions_gateway(args):
    from . import get_submissions
    get_submissions.get_submissions_argparse(args)


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()

p_breakdown = subparsers.add_parser('breakdown')
p_breakdown.add_argument('--sort', dest='sort', default=None)
p_breakdown.add_argument('-r', '--subreddit', dest='subreddit', default=None)
p_breakdown.add_argument('-u', '--user', dest='username', default=None)
p_breakdown.set_defaults(func=breakdown_gateway)

p_get_comments = subparsers.add_parser('get_comments', aliases=['commentaugment'])
p_get_comments.add_argument('-r', '--subreddit', dest='subreddit', default=None)
p_get_comments.add_argument('-s', '--specific', dest='specific_submission', default=None)
p_get_comments.add_argument('-u', '--user', dest='username', default=None)
p_get_comments.add_argument('-v', '--verbose', dest='verbose', action='store_true')
p_get_comments.add_argument('--dont_supplement', dest='do_supplement', action='store_false')
p_get_comments.add_argument('-l', '--lower', dest='lower', default='update')
p_get_comments.add_argument('-up', '--upper', dest='upper', default=None)
p_get_comments.set_defaults(func=get_comments_gateway)

p_getstyles = subparsers.add_parser('getstyles')
p_getstyles.add_argument('-r', '--subreddit', dest='subreddit')
p_getstyles.set_defaults(func=getstyles_gateway)

p_getwiki = subparsers.add_parser('getwiki')
p_getwiki.add_argument('-r', '--subreddit', dest='subreddit')
p_getwiki.set_defaults(func=getwiki_gateway)

p_livestream = subparsers.add_parser('livestream')
p_livestream.add_argument('-1', '--once', dest='once', action='store_true')
p_livestream.add_argument('-c', '--comments', dest='comments', action='store_true')
p_livestream.add_argument('-l', '--limit', dest='limit', default=None)
p_livestream.add_argument('-r', '--subreddit', dest='subreddit', default=None)
p_livestream.add_argument('-s', '--submissions', dest='submissions', action='store_true')
p_livestream.add_argument('-u', '--user', dest='username', default=None)
p_livestream.add_argument('-v', '--verbose', dest='verbose', action='store_true')
p_livestream.add_argument('-w', '--wait', dest='sleepy', default=30)
p_livestream.set_defaults(func=livestream_gateway)

p_mergedb = subparsers.add_parser('mergedb')
p_mergedb.add_argument('--from', dest='from_db_path', required=True)
p_mergedb.add_argument('--to', dest='to_db_path', required=True)
p_mergedb.set_defaults(func=mergedb_gateway)

p_offline_reading = subparsers.add_parser('offline_reading')
p_offline_reading.add_argument('-r', '--subreddit', dest='subreddit', default=None)
p_offline_reading.add_argument('-s', '--specific', dest='specific_submission', default=None)
p_offline_reading.add_argument('-u', '--user', dest='username', default=None)
p_offline_reading.set_defaults(func=offline_reading_gateway)

p_index = subparsers.add_parser('index', aliases=['redmash'])
p_index.add_argument('--all', dest='do_all', action='store_true')
p_index.add_argument('--author', dest='do_author', action='store_true')
p_index.add_argument('--date', dest='do_date', action='store_true')
p_index.add_argument('--flair', dest='do_flair', action='store_true')
p_index.add_argument('--html', dest='html', action='store_true')
p_index.add_argument('--score', dest='do_score', action='store_true')
p_index.add_argument('--sub', dest='do_subreddit', action='store_true')
p_index.add_argument('--title', dest='do_title', action='store_true')
p_index.add_argument('--offline', dest='offline', action='store_true')
p_index.add_argument('-r', '--subreddit', dest='subreddit', default=None)
p_index.add_argument('-st', '--score_threshold', dest='score_threshold', default=0)
p_index.add_argument('-u', '--user', dest='username', default=None)
p_index.set_defaults(func=index_gateway)

p_get_submissions = subparsers.add_parser('get_submissions', aliases=['timesearch'])
p_get_submissions.add_argument('-l', '--lower', dest='lower', default='update')
p_get_submissions.add_argument('-r', '--subreddit', dest='subreddit', default=None)
p_get_submissions.add_argument('-u', '--user', dest='username', default=None)
p_get_submissions.add_argument('-up', '--upper', dest='upper', default=None)
p_get_submissions.add_argument('-v', '--verbose', dest='verbose', action='store_true')
p_get_submissions.add_argument('--dont_supplement', dest='do_supplement', action='store_false')
p_get_submissions.set_defaults(func=get_submissions_gateway)

def main(argv):
    helpstrings = {'', 'help', '-h', '--help'}

    command = listget(argv, 0, '').lower()
    command = OLD_COMMAND_ALIASES.get(command, command)

    # The user did not enter a command, or entered something unrecognized.
    if command not in MODULE_DOCSTRINGS:
        print(DOCSTRING)
        if command == '':
            print('You are seeing the default help text because you did not choose a command.')
        elif command not in helpstrings:
            print('You are seeing the default help text because "%s" was not recognized' % command)
        return 1

    # The user entered a command, but no further arguments, or just help.
    argument = listget(argv, 1, '').lower()
    if argument in helpstrings:
        print(MODULE_DOCSTRINGS[command])
        return 1

    args = parser.parse_args(argv)
    try:
        args.func(args)
    except exceptions.DatabaseNotFound as e:
        message = str(e)
        message += '\nHave you used any of the other utilities to collect data?'
        print(message)
        return 1

    return 0

if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))