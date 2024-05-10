# README

## Local development

You can develop inside docker container, or using local python interpreter,
if you prefer local python, then create `.invoke` file in the root with the
following content

```
[Project]
interpreter = local
```

By default we assume you will develop inside docker container, but if you don't
want to use a Docker, just create virtualenv and then (once activated)

```bash
pip install -r requirements/development.txt
```

## Async celery

If you plan to develop and debug async tasks with celery, pls create virtualhost
inside rabbitmq container and grant user permissions as shown below

```bash
$ docker-compose run rabbitmq
$ docker-compose exec rabbitmq rabbitmqctl add_vhost "jlp_backend-development"
$ docker-compose exec rabbitmq rabbitmqctl add_user jlp_backend_user manager
$ docker-compose exec rabbitmq rabbitmqctl set_permissions -p "jlp_backend-development" jlp_backend_user ".*" ".*" ".*"
```

If however you started the development with `inv project.init` these
operations are already completed

You may need to adjust `CELERY` settings in `config/settings/development.py`
as needed

## CLI

There are bunch of commands available for your using `inv` command, just type
next command to list all available commands:

```bash
$ inv -l
```

### Stripe Settings


By default, creation of stripe objects are disabled. This means you can create lawyers through factories without creation instances such as  `CustomerProxy`, `SubscriptionProxy` 

```python
# local.py
STRIPE_ENABLED = False
```
But for the correct work of registering attorneys, you need to create or synchronize subscription plan

Sync from existing stripe plans
```bash
./manage.py djstripe_sync_plans_from_stripe
```
Creation via CLI

`Attention`: You need to run this command carefully, and using a separate stripe application, different from the DEV environment
 
```bash
./manage.py create_subcriptions_for_attorneys
```

## Secrets

Secret | Description
-- | --
AWS_ACCESS_KEY_ID | AWS IAM Access Key Id
AWS_SECRET_ACCESS_KEY | AWS IAM Secret Access Key
DEV_ECR_REPOSITORY | ECR Repository (Dev)

## Actions Workflows

### Development (dev.yml)
1. Check out repository
2. Configure AWS credentials
3. Log into ECR
4. Build, tag, and deploy backend Docker image to ECR

Happy Coding!
