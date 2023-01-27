from invoke import Exit, UnexpectedExit, task

from . import common, django, linters, tests

__all__ = (
    'gitmessage',
    'hooks',
    'pre_commit',
    'pre_push',
)


@task
def gitmessage(context):
    """Set default .gitmessage."""
    common.print_success("Deploy git commit message template")
    context.run('echo "[commit]" >> .git/config')
    context.run('echo "  template = .gitmessage" >> .git/config')


@task
def hooks(context):
    """Install git hooks."""
    common.print_success("GitHooks copy to .git")
    context.run('mkdir -p .git/hooks')
    context.run('cp .git-hooks/* .git/hooks/')
    context.run('chmod -R 755 .git/hooks/pre-commit')


@task
def pre_commit(context):
    """Perform pre commit check"""
    common.print_success('Perform pre-commit check')
    try:
        linters.all_git_staged(context)
    except Exit as e:
        common.print_error(
            'Style check failed\n'
            'Commit aborted due to errors - pls fix them first!'
        )
        raise e
    common.print_success('Wonderful JOB! Thank You!')


@task
def pre_push(context):
    """Perform pre push check"""
    common.print_success('Perform pre-push check')
    code_style_passed = True
    test_passed = True
    migrations_passed = True
    try:
        linters.all(context)
    except Exit:
        common.print_warn('Code style checks failed')
        code_style_passed = False
    try:
        tests.run_full(context)
    except UnexpectedExit:
        common.print_warn('Tests failed')
        test_passed = False
    try:
        django.check_new_migrations(context)
    except UnexpectedExit:
        common.print_warn('New migrations were added!\nPlease commit them!')
        migrations_passed = False
    if not all((test_passed, migrations_passed, code_style_passed)):
        common.print_error('Push aborted due to errors\nPLS fix them first!')
        raise Exit(code=1)
    common.print_success('Wonderful JOB! Thank You!')
