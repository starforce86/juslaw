#Different project-related files

##`firestore-rules`

File with Firestore related rules for an app, it restricts permissions for
client users (with custom JWT token from backend) on separate branches:

1. Only chat participants (client or attorney) can get, create, update and
delete chat info and inner posts collection (`/chats/{chat_id}`)

2. User can get only it's own chats or chats where it's participant in users 
statistics collection (`/users/{user_id}/chats/{chats_id}`).

3. User can get chat's messages collection (`chats/{chat_id}/messages/{message_id}/`).

You can check out rules workflow here:
https://firebase.google.com/docs/firestore/security/get-started

#### Deploy rules

1. Go to Firebase console `https://console.firebase.google.com` and select
`JusLaw Platform` project.

2. Go to `Database` service, open its `Rules` and copy whole contents of
``firestore-rules.js`` there.

3. `Publish` new changes.

##`web-firebase-snippet.js`

It is a snippet which allows to test base Firebase functionality in local,
like:

- login with custom JWT token
- get chats and user statistics data
- check out permissions
- etc.
