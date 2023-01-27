# Uploading files to s3 bucket

## S3 direct upload destinations

* `user_avatars`: For uploading avatars of users. Allowed types `image/jpeg` and `image/png`.
Max size of file `20 MB`.
* `documents`: For uploading users' documents. User must be `authenticated`. Max size of file is `20 MB`.
* `esign`: For uploading documents related to `docusign`. User must be `authenticated`.
Allowed files: `.doc`, `.docm`, `.docx`, `.dot`, `.dotm`, `.dotx`, `.htm`, `.html`, `.msg`, `.pdf`, `.rtf`, `.txt`,
`.wpd`, `.xps`, `.bmp`, `.gif`, `.jpg`, `.jpeg`, `.png`, `.tif`, `.tiff`, `.pot`, `.potx`, `.pps`,
`.ppt`, `.pptm`, `.pptx`, `.csv`, `.xls`, `.xlsm`, `.xlsx`
(https://support.docusign.com/en/guides/ndse-user-guide-supported-file-formats).
Max size of file is `25 MB`.
* `chats_images`: For storing `firebase` chats images. User must be `authenticated`.
Max size of file is `20 MB`.

## Uploading workflow
To get upload params you need make a request `POST /s3direct/get_params/` with body:
```json
    {
      "dest": "user_avatars",
      "filename": "string",
      "content_type": "string"
    }
```
Where `dest` is chosen destination of file(where file will be saved), `filename` is name of file,
and `content_type` is content type of file. On success will receive upload params:
```json
{
    "policy": "string",
    "success_action_status": 201,
    "x-amz-credential": "string",
    "x-amz-date": "date",
    "x-amz-signature": "string",
    "x-amz-algorithm": "AWS4-HMAC-SHA256",
    "form_action": "https://s3.saritasa.io/jlp-dev",
    "key": "documents/026bccc1-6528-4c91-8cda-5a937305819c/photo_2019-06-30_18-08-16.jpg",
    "acl": "public-read",
    "Content-Disposition": "attachment"
}
```
Then you need to send this data with `file` as `form data` to `form_action`(is upload URL) via
post request. On success you will receive a `link` to a uploaded file, which can use in 
others endpoints.
