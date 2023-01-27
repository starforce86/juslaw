# QuickBooks integration

JLP app has possibility of ``invoices`` exporting directly to attorneys
QuickBooks accounts. To make this work attorney should be registered in
`quickbooks` and have some available `company` there. 

To work with quickbooks in `dev` and `stage` envs use `sandbox` -
`https://developer.intuit.com/`. For `production` env there should be used
`https://www.intuit.com/`.

**Note: when quickbooks user is registered in ``sandbox`` he already has its
testing ``sandbox`` company, which may be used.**

After successful registration and company creation you can use ``accounting``
app API to export invoices:

- GET `/accounting/auth/url/` - api method to get oauth2 authorization url for
attorney. Attorney should go for it to successfully authenticate in QB.

- GET `/accounting/export/customers/` - api method which returns list of already
existing in QB `customers` which can be used as `invoice` recipients.

- POST `/accounting/export/invoice/` - api method to start invoice export to
already existing in QB customer taken from `/accounting/export/customers/` or
new customer (created by default).

**Note: QB doesn't allow to have 2 customers with the same names.**

After invoice's successful export, you may go to your company and check out
created invoices ``Sandbox -> `choose desired company` -> Sales -> Invoices``
and find exported invoice there.
