# App testing with `pytest`

## `conftest.py` files

This files used to create `common fixtures` for tests(fixtures you want to use in several files). 
They should be placed at `apps/app_name/tests`. 

## Plugin `pytest-django`

A useful plugin to test Django apps with pytest 
(Docs: https://pytest-django.readthedocs.io/en/latest/)

### Explanation of database fixtures

#### django_db_setup

This fixture that ensures that the test databases are created and available for use. It needs to
be used only once. So that's what we did in our main `conftest.py` file.

```python
import pytest

@pytest.fixture(scope='session', autouse=True)
def django_db_setup(django_db_setup):
    """Set up test db for testing."""
```

#### db and django_db_blocker

Every test that reads or writes into db needs to get database access. To do that we can:
* Mark test module with pytest mark -> `pytest.mark.django_db`
* Use fixture `db`

To give access to database for all tests we made this fixture in our main `conftest.py` file.

```python
import pytest

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Give all tests access to db."""
```

But since `db` fixture have scope of `fucntion`, it won't work for fixture with scope `session`
or `module`. In these case you need to use `django_db_blocker` fixture.

```python
import pytest

@pytest.fixture(scope='session')
def db_action(django_db_blocker):
    with django_db_blocker.unblock():
        # Do your thing
```

### Creating fixture with model instance
Let's say you need to create an `instance` of one model and reuse it several tests. To do this, you 
can write something like this:

```python
import pytest

@pytest.fixture(scope='session')
def attorney(django_db_blocker) -> Attorney:
    """Create attorney for testing."""
    with django_db_blocker.unblock():
        return AttorneyFactory()
``` 

### Parametrise model fixtures

If you want to use model `fixtures` in `@pytest.mark.parametrize` decorate, then first you need
to create a `fixture` that uses `fixtures` you want to use, inside that `fixture` create a `mapping`
and return fixture based on `request parameter` passed in `@pytest.mark.parametrize`

```python
import pytest

@pytest.fixture
def user(request, client: Client, attorney: Attorney) -> AppUser:
    """Fixture to use fixtures in decorator parametrize for AppUser object."""
    mapping = {
        'anonymous': None,
        'client': client.user,
        'attorney': attorney.user,
    }
    return mapping.get(request.param)

@pytest.mark.parametrize(
    argnames='user,',
    argvalues=(
        'anonymous',
        'client',
        'attorney',
    ),
    indirect=True
)
def test_get_list(user: AppUser,):
    """Test docs."""
```

To use `fixtures` with `normal data` in `@pytest.mark.parametrize` just create fixture with `argname` 
that just returns `request parameter`.

```python
import pytest

@pytest.fixture
def status_code(request) -> int:
    """Fixture to parametrize status codes."""
    return request.param

@pytest.mark.parametrize(
    argnames='user, status_code',
    argvalues=(
        ('anonymous', 401),
        ('client', 403),
        ('attorney', 200),
    ),
    indirect=True
)
def test_get_list(user: AppUser, status_code: int):
    """Test docs."""
```

## Plugin `pytest-xdist`

This plugin allows to run tests in parallel (Docs: https://docs.pytest.org/en/3.0.1/xdist.html)

To run tests in parallel just write this

```
pytest -n auto
```

If you want to specify the amount of used CPUs, you can replace `auto` with number, like this

```
pytest -n NUM
```

## Plugin `pytest-flake8` and `pytest-isort`

These two plugins check code style of app:
* `pytest-flake8`: https://pypi.org/project/pytest-flake8/ 
* `pytest-isort`: https://pypi.org/project/pytest-isort/ 

To run just `code style` check, write this

```
pytest --flake8 --isort -m "isort or flake8"
```

## Plugin `pytest-pycharm`

Plugin for `pytest` to enter `PyCharm` debugger on uncaught exceptions. To make it work, all
you need to do, is to launch `pytest` by `PyCharm` debugger.

## Plugin `pytest-picked`

Plugin for `pytest` which runs test files that are `not committed`. Simply add `--picked` to 
`pytest` command.

```
pytest --picked
```

## Plugin `pytest-django-queries`

Plugin for `pytest` for measuring the database query count of a `django` project. 
(Docs: https://pytest-django-queries.readthedocs.io/en/latest/).
It captures the `SQL` queries of marked tests to generate `reports` from them that can then 
be analyzed, proceeded and even integrated to `CIs` and `GitHub` as a peer reviewing tool (bot).

To capture all queries use add to conftest this auto fixture

```python
import pytest

@pytest.fixture(autouse=True)
def capture_query_performances(count_queries):
    """Fixture to capture performance of queries in tests."""
```

Or to capture performance for particular test

```python
import pytest

@pytest.mark.count_queries
def test_query_performances():
    """Do your thing."""

def test_query_performances(count_queries):
    """Do your thing."""
```

To get report all you need to do is:
* Simply run `pytest`
* Use `django-queries show` to display results into console or `django-queries html` to create
html report file
* Use `django-queries backup` to create backup of run. After next run you can see differences
with `django-queries diff`
