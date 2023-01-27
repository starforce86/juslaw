# Release checks

Please don't forget to update corresponding services configs on a new deploys
to development, staging or production envs.

All required for different envs firebase, stripe, docusign, quickbooks urls
and credentials you can find in ``docs/environments/environments.rst`` file. 


### Firebase rules

You will need to update it if there were some changes related to `chats`
access and participants (`chats` app).


### Stripe subscriptions or connected account settings. 

If there are some changes in `finance` app, probably you may need to perform
some updates for Stripe service.
 
If there were some changes related to `subscriptions` workflow - you may need
to update its related settings - ``products``, ``plans``, ``webhooks``
(`Endpoints receiving events from your account`). 

If there were some changes in ``direct deposits`` workflow - you may need to
update related to ``connected`` account settings:

- `Settings / Connect settings` - add capabilities and
`Express account` country (`Availability`), add oauth2 url (`Integration`),
customize connected account form (`Branding`)

- ``webhooks`` - add or update `Endpoints receiving events from Connect
applications`

All related to stripe `webhooks` may be created with a management command
```bash
./manage.py create_webhooks 
```
But if you created new stripe webhook - don't forget to update its related keys
in vault.


### Docusign configuration

You will need to update it if there were some changes in ``electronic signing``
workflow (`esign` app). So you may need to update ``redirect URIs`` in
dashboard `Integration -> API and Keys`.


### QuickBooks

You will need to update it if there were some changes in ``accounting`` app
related to invoices export workflow. So you may need to update `keys` or
`redirect URIs` in ``Keys & OAuth`` dashboard section.


# Release steps

Please follow these steps to make new staging, production release:

1. Release branch preparation

- If you are going to deploy new stage release - create a separate
`release-x.y` branch with a release changes only from `develop` branch.

    ```bash
    git checkout develop
    git checkout -b release-x.y
    ```

- If you are going to deploy new production release - you should already have
prepared and tested `release` branch from stage environment. All you need to do
is to merge current `release` branch to `master` branch and add git tag on a
latest `master` branch commit.

     ```bash
    git checkout master
    git merge release-x.y
    git tag -a 'v.X.Y.Z' -m 'Release X.Y.Z'
    ```

2. Run tests and linters before deploy and fix appeared issues if it is needed.

```bash
inv linters.all
inv tests.run
```

3. If everything is ok you can push your changes to repository.
- for stage release you can do just
    ```bash
    git push origin release-x.y
    ```

- for production release you can do just
    ```bash
    git push origin master && git push origin master --tags
    ```

4. After successful changes pushing you may go to repository and check that
everything is correctly pushed (check tag and new release branch). If
everything is ok, you can go to corresponding `Jenkins` project and start its
building.

5. Don't forget to update version in ``changelog.md``.
