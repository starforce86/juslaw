# DocuSign integration

For documents electronic signing JLP platform uses ``DocuSign``. Documents are
sent in DocuSign on a new matter creation or further matter documents updates.

To work with DocuSign attorney should have already existing DocuSign
account and provide all required by JLP consents.

**Note: DocuSign has a separate `sandbox` environment for testing purpose 
(https://demo.docusign.net/, accounts login and create -
https://account-d.docusign.com/). For production environment testing there
should be used https://www.docusign.net/ and https://account.docusign.com/**

When attorney has created DocuSign account there can be used following API
endpoints:

- GET `/esign/profiles/current/` - api method which gets esign account info for
current user, it designates whether user has consent or not (`has+consent`) and
in case of absent consent returns `obtain_consent_link`, following by which
user can provide all required by JLP consents.

- DELETE `/esign/profiles/current/` - possibility to reset all information
related to current esign account. When few users use the same ``docusign``
account, it will reset accounts for all users and make them provide `consents`
again.

- POST `/esign/envelopes/` - api method to create new docusign documents
(envelopes).

- GET `​/esign/envelopes/`, `/esign/envelopes/{id}/` - api method to get all
users envelopes list or details with its current status and `edit_link` if it
is needed.

## Known issues

There are following moments related to DocuSign:

- Currently there is a problem in DocuSign that it removes all envelopes for
`demo` accounts after 30 days and only `draft` envelopes in production
after 30 days too without any notifications and webhooks.

https://support.docusign.com/articles/How-long-does-DocuSign-store-my-documents

So the fix is app has a celery task, which:

    - deletes all envelopes older 30 days and move matter to `Draft` status
    for `development` and `staging`
    - deletes only `draft` envelopes older 30 days for `production`

- Also there are issues with releasing new DocuSign app - it should be created
from development env in `Integration -> API & Keys` section there is a
possibility to move some development app to a production with
``starting of activation check``. This operation is not fast and takes to 3 days
(in good situation may take 24h), but there are some requirements that should
be satisfied to send app on check - it should be called 20+ times and use
production docusign account.

https://developers.docusign.com/esign-soap-api/reference/introduction-changes/integration-keys

https://developers.docusign.com/esign-rest-api/guides/go-live
