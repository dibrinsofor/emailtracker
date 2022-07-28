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
===========Mail[b'1']===========
Subject:     Last Chance: Save 20% on Ader404
Sender's Email Address: <waltervan@mail.jpg.com>
Sender's Mail Server: mta.mail.kaptest.com. [136.222.180.666]
Links found:
http://click.mail.kaptest.com/open.aspx?ffcb10-fe9313737c64007974-fdfd15707263067f77167472-fe901372766605757d-ff931375-fe2b127170610779761d70-ff061674756407&d=70178&bmt=0
http://click.mail.kaptest.com/?qs=0206c98dd2344e71cf406d6eca9cc33432677b78649b27490f4bc4c33e74fc010134eff9222611019ffef65b807de04631ff438bf8a2cdc9
Images found:
http://image.mail.kaptest.com/lib/fe901372766605757d/m/1/255a7900-85b3-4a54-b281-0ca6e8646923.png
http://image.mail.kaptest.com/lib/fe901372766605757d/m/1/d6c8056a-36cf-4589-ad99-4d8beb56c491.png
https://image.s4.exct.net/lib/fe911573736c007d7d/m/2/24b84e22-8d38-4d6c-98db-80812ca4de5f.png
Tracking Links found: 
<img src="http://click.mail.kaptest.com/open.aspx?ffcb10-fe9313737c64007974-fdfd15707263067f77167472-fe901372766605757d-ff931375-fe2b127170610779761d70-ff061674756407&d=70178&bmt=0" width="1" height="1" alt="">
<img src="http://click.mail.kaptest.com/open.aspx?ffcb10-fe9313737c64007974-fdfd15707263067f77167472-fe901372766605757d-ff931375-fe2b127170610779761d70-ff061674756407&d=70178&bmt=0" width="1" height="1" alt="">
```
