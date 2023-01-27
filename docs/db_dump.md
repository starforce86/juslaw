# Making dev database dump

## Getting data from dev db

All you need to do is to use this command below. It will prompt you a password for db, you can get it 
from [vault](https://vault.saritasa.io/ui/vault/secrets/projects/show/jlp-backend-develop)

```bash
pg_dump -d jlp_dev -h postgres1.saritasa.io -U jlp_dev -f dev_db.sql -v
```

It will take a while, after that it will create a file `dev_db.sql`. It will be used to create db.

## Loading data into local db

Now all is left to do is to enter these commands below. `psql` will also prompt for password, use 
default for local env password `manager`.

```bash
python3 manage.py drop_test_database --noinput
python3 manage.py reset_db -c --noinput
psql -d jlp_dev -h postgres -U jlp_user -f dev_db.sql 
```
