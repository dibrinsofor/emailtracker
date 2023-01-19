## emailtracker

<p align="center">
  <img width="460" src="assets/logo%20for%20md.png">
</p>

emailtracker allows users detect whether or not mail in their inbox is being tracked. It offers support for emails (multi-part and plain text MIMEs) sent over the IMAP protocol. It allows you to determine:
- What companies are tracking you.
- How they do it? through blank pixels, clickable links, etc.
- Whether or not your data is sent over secure protocols. 
- Infers what information they may be collecting.

### installation
- (recommended) activate a virtual env
  - `python -m virtualenv venv`
  - `venv\scripts\activate` 
- run build script `python build.py -s` to setup development environment
<!-- - install the project dependencies in `requirements.txt`
  - `pip install -r requirements.txt
- setup local registry of known adtracking companies:
  - `python companies.py` -->
<!-- - setup sqlite db
  - run `flask shell` in your terminal. *it imports the app context for `db.engine commands`*
  - run `db.create_all()` -->

### using
- to run:
  - `python build.py -f (debug)` to setup environment and run the app, or
  - `flask --debug run` 

You can also setup the environment and spin up the server by running `python build.py` with no flags.

#### Third-Party app passwords
To generate third-party app passwords, use these links: [Gmail](https://www.lifewire.com/get-a-password-to-access-gmail-by-pop-imap-2-1171882) and [Yahoo](https://www.esofttools.com/blog/how-to-generate-third-party-app-passwords-in-yahoo-account/).


<!-- #### Sample Output

```txt
===========Mail[b'1']===========
Subject:     Last Chance: Save 20% on Ader404
Sender's Email Address: <waltervan@mail.jpg.com>
Sender's Mail Server: mta.mail.acw.com. [136.222.180.666]
Links found:
http://click.mail.kaptest.com/open.aspx?ffcb10-fe9313737c64007974-fdfd15707263067f77167472-fe901372766605757d-ff931375-fe2b127170610779761d70-ff061674756407&d=70178&bmt=0
Images found:
http://image.mail.kaptest.com/lib/fe901372766605757d/m/1/d6c8056a-36cf-4589-ad99-4d8beb56c491.png
https://image.s4.exct.net/lib/fe911573736c007d7d/m/2/24b84e22-8d38-4d6c-98db-80812ca4de5f.png
Tracking Links found: 
<img src="http://click.mail.kaptest.com/open.aspx?ffcb10-fe9313737c64007974-fdfd15707263067f77167472-fe901372766605757d-ff931375-fe2b127170610779761d70-ff061674756407&d=70178&bmt=0" width="1" height="1" alt="">
```
### Contributing

From suggestions, code refactors to tests, we accept small contributions. Things to note:
- Style guide: [PEP8](https://peps.python.org/pep-0008/)
- Use clear, informative commit messages
 -->

### License
This project is available under the MIT License. [Here](LICENSE)
