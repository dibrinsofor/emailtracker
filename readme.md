## EmailTracker

solution built for [Prof. Danny Huang](https://scholar.google.com/citations?user=B-Zb3joAAAAJ&hl=en)

blog posts on how to generate passwords for third party apps:

- [Gmail](https://www.lifewire.com/get-a-password-to-access-gmail-by-pop-imap-2-1171882)
- [Yahoo](https://www.esofttools.com/blog/how-to-generate-third-party-app-passwords-in-yahoo-account/)

### How to use (after forking repo)

1. clone and install dependencies in `requirements.txt` using `pip install -r requirements.txt`.
2. create a `.env` file and copy paste the sample text from the `.env_sample` file.
3. enter newly generated third party app password from email client for added security (or you can just use your regular email and password).
4. navigate to the file's location and run the script from terminal using `python testimap.py`.
5. after running successfully, open `email_dump.txt` to see generated email data.

### Sample Output

```txt
===========Mail[b'7']===========
Subject:     How was it for you?
Sender's Email Address: <no-reply@reviews.co.uk>
Links found:
http://www.sportsdirect.com/
http://www.reviews.co.uk/front/unsubscribe?id=0ffe9f54e8499494398943d298effdc3&eid=201135444&sign=c449811c4dcbe2057a59cba34786e2cf
http://www.reviews.co.uk/tracking/email/201135444
Images found:
https://dash.reviews.co.uk/img/upload/8574/images/sportdirect-logo.png
https://dash.reviews.co.uk/img/upload/8574/images/how-was-it-for-you2.jpg
https://dash.reviews.co.uk/img/upload/8574/images/signature.png
```
