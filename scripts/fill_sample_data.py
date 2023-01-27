"""Simple script to fill DB with project sample data."""
from random import choice

from apps.business import factories as business_factories
from apps.documents import factories as documents_factories
from apps.forums import factories as forums_factories
from apps.news import factories as news_factories
from apps.promotion import factories as promotion_factories
from apps.social import factories as chats_factories

# business
MATTERS_COUNT = 5
MATTER_TOPICS_COUNT = 2
MATTER_TOPICS_POSTS_COUNT = 3
VOICE_CONSENT_COUNT = 1
INVOICE_COUNT = 3
TIME_BILLING_COUNT_PER_INVOICE_COUNT = 3
CHECKLIST_ENTRY_COUNT = 3

# chats
CHATS_COUNT = 3
CHATS_PARTICIPANTS_COUNT = 3

# documents
MATTER_FOLDER_COUNT = 3
ATTORNEY_FOLDER_COUNT = 2

# forums
TOPICS_COUNT = 5
FOLLOWED_TOPIC_COUNT = 3
USER_STATS_COUNT = 3

# news
NEWS_COUNT = 5

# promotion
ATTORNEY_EVENTS_COUNT = 2

print('Creating `business`...')
matters = business_factories.FullMatterFactory.create_batch(size=MATTERS_COUNT)
for i in range(MATTERS_COUNT//2):
    matter = choice(matters)
    matter.lead = None
    matter.save()

for matter in matters:
    business_factories.VoiceConsentFactory.create_batch(
        matter=matter, size=VOICE_CONSENT_COUNT
    )
    topics = business_factories.MatterTopicFactory.create_batch(
        matter=matter,
        size=MATTER_TOPICS_COUNT
    )
    for topic in topics:
        business_factories.MatterPostFactory.create_batch(
            topic=topic,
            author=choice([matter.attorney.user, matter.client.user]),
            size=MATTER_TOPICS_POSTS_COUNT
        )

for i in range(INVOICE_COUNT):
    invoice = business_factories.InvoiceFactory(matter=choice(matters))
    time_billings = business_factories.BillingItemFactory.create_batch(
        matter=invoice.matter,
        size=TIME_BILLING_COUNT_PER_INVOICE_COUNT
    )
    for tb in time_billings:
        tb.invoices.add(*[invoice])

attorneys = [matter.attorney for matter in matters]
clients = [matter.client for matter in matters]

for i in range(CHECKLIST_ENTRY_COUNT):
    business_factories.ChecklistEntryFactory(attorney=choice(attorneys))

print('Creating `chats`...')
chats = chats_factories.GroupChatFactory.create_batch(
    size=CHATS_COUNT,
    creator=choice(attorneys).user
)

print('Creating `documents`...')
for client in clients:
    documents_factories.PrivateFolderFactory(owner=client.user)

for matter in matters:
    documents_factories.MatterFolderFactory.create_batch(
        matter=matter,
        owner=None,
        size=MATTER_FOLDER_COUNT
    )

all_users = [c.user for c in clients] + [a.user for a in attorneys]

print('Creating `forums`...')
topics = []
for i in range(TOPICS_COUNT):
    post_first = forums_factories.PostFactory(author=choice(all_users))
    last_post = forums_factories.PostFactory(
        author=choice(all_users), topic=post_first.topic
    )
    topics.append(post_first.topic)


print('Creating `news`...')
news_factories.NewsFactory.create_batch(size=NEWS_COUNT)


print('Creating `promotion`...')
for attorney in attorneys:
    promotion_factories.EventFactory.create_batch(
        attorney=attorney, size=ATTORNEY_EVENTS_COUNT
    )
