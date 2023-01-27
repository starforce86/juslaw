# FireStore Structure

### Chats collection 

Contains whole chat info, its participants identifiers, related Lead or Chat instance and posts.

**chats/{id}/**
```json
{
    "participants": [1, 2],
    "lead_id": 2,
    "chat_id": 1
}
```

- `participants` - ids of users participating in the chat (client and attorney
ids)
- `lead_id` - id of related to the chat lead in backend db
- `chat_id` - id of related to the chat in backend db

**permissions:**

Only chat participants (client or attorney) can `get`, `create`, `update` and
`delete` chat info and inner posts collection (`/chats/{chat_id}`).

### Messages collection 

Contains whole chat posts info.

**chats/{id}/messages/{id}/**
```json
{
    "id":  "4e6273a0-f343-496a-9c73-e4d21c33b4fc",
    "author_id":  1,
    "text":  "Hello",
    "type":  "text",
    "created": "2019-11-15 04:55:22.976492+00:00"
}
```

- `id` - id of a post in the chat
- `author_id` - id of a post author
- `text` - text of a message
- `type` - post type (`text` or `image`)
- `created` - datetime when post was created

**permissions:**

Only chat participants (client or attorney) can `get`, `create`, `update` and
`delete` chat info and inner posts collection (`/chats/{chat_id}/messages`).

### Users statistics collection

Contains information about chat for its participants. so each user has a list
of chats where he is participant and some identifiers like his last read
message and amount of unread messages and etc.

**users/{id}/chats/{id}/**
```json
{
    "count_unread": 11,
    "last_read_post": "QWmvqpCAo473DQdaB3ot",
    "last_chat_message_date": "1580201662297",
    "last_chat_message_text": "Sample text",
    "participants": [1, 2, 3]
}
```

- `count_unread` - amount of unread by user posts in the chat
- `last_read_post` - id of the last read by user post in this chat
- `last_chat_message_date` - timestamp when last read post was created
- `last_chat_message_text` - text of last message
- `another_participant_id` - id of another user, who takes part in chat(`deprecated`)
- `participants` - ids of participants of this chat

**permissions:**

User can get `its own` chat or chats, where it's a `participant` in users statistics collection 
(`/users/{user_id}/chats/{chat_id}`).

Permissions are defined in a ``artifacts/firestore-rules.js``.
