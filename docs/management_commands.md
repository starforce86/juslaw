# Management commands

## Finance

### create_product_and_plans

This command will create two default plans in `db` and `stripe`
`Be careful with this one`. You will definitely will need to use it one
we deploying on new `environment`.

```bash
python3 manage.py create_product_and_plans
```

### create_webhook

This command will create required webhooks in `stripe` depending on defined
`--type` argument (webhook of `subscriptions` type for subscriptions workflow
or webhook of `deposits` type for direct deposits workflow). You can use it,
to create webhooks for testing (just specify `host` arg).

```bash
python3 manage.py create_webhook --type=subscriptions
```

```bash
python manage.py create_webhooks --type=subscriptions --host=https://bba89c5d.ngrok.io
```

## Forums

### recalculate_forum_stats

This command initiates full statistic recalculation in forum app.

```bash
python3 manage.py recalculate_forum_stats
```

### set_up_categories

This command sets up specialities, categories and fee_kinds. `Be careful with this one`. You will definitely will need to use it one
we deploying on new `environment`.

```bash
python3 manage.py set_up_categories
```

## dj-stripe

### djstripe_sync_plans_from_stripe

Syncs plans from stripe. It should be used in local stripe. 
So there wouldn't be any redundant plans.

```bash
python3 manage.py djstripe_sync_plans_from_stripe
```

## cities_light

### cities_light

Explanation of `cities_light` management command:

* Calling `cities_light` for first time, will download locations files
  and import location data in to our db. When called for second time it will
  check downloaded files, it there is update it'll update them and make
  import.
  Note: if you reset db and just called `cities_light`, it won't refill
  your db with locations

* `--force-import-all` will make cities_light to import of locations data from
  files, but it will not update location files

* `--force-all` will re-download locations files and do import of locations
  data from downloaded files

```bash
python3 manage.py cities_light
```

### create_fake_country

As fast alternative you can use our command that just creates fake data 
by using factories

```bash
python3 manage.py cities_light
```
