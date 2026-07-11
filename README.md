# OSWE-Prep

**Curated resources, PoC patterns, case studies, and methodology guides for Offensive Security WEB-300 (OSWE).**

> **New to the repo?** Start with the **[OSWE Study Roadmap](OSWE-Study-Roadmap.md)** — an 8-week structured plan with topic priorities, lab recommendations, daily habits, and milestones mapped to the content here.
>
> **Hands-on today?** `cd labs && ./labctl.sh up` — see **[labs/README.md](labs/README.md)**. Full doc map: **[DOCUMENTATION.md](DOCUMENTATION.md)**.

This repo is documentation + production-quality Python PoC examples + Docker teaching labs following consistent skeletons. All content is for authorized labs, CTFs, and OSWE exam preparation only.

---

## Start Here

| Resource | Why It Matters | Link |
|----------|----------------|------|
| Study Roadmap | 8-week plan, priorities, how to use everything in this repo | [OSWE-Study-Roadmap.md](OSWE-Study-Roadmap.md) |
| Progress Tracker | Honest readiness checklist by vuln class | [Progress-Tracker.md](Progress-Tracker.md) |
| Exam-Day Runbook | Time boxes, pivot rules, pre-exam ops | [Exam-Day-Runbook.md](Exam-Day-Runbook.md) |
| Lab Setup Matrix | Skill → lab/PoC pairing | [Lab-Setup-Matrix.md](Lab-Setup-Matrix.md) |
| **Docker Labs** | One-command vulnerable apps for every major class | [labs/README.md](labs/README.md) |
| Documentation index | Map of all guides, labs, drills, and PoCs | [DOCUMENTATION.md](DOCUMENTATION.md) |
| PoC Methodology | The reusable skeleton + patterns used in all examples | [Building a Reusable OSWE PoC Skeleton.md](Building%20a%20Reusable%20OSWE%20PoC%20Skeleton.md) |
| Exploit Writing | Practical `requests` patterns, stages, context objects | [Exploit Writing for OSWE.md](Exploit%20Writing%20for%20OSWE.md) |
| Complete PoC Guide | Navigation + how the different examples and advanced skeleton fit together | [COMPLETE-POC-GUIDE.md](COMPLETE-POC-GUIDE.md) |

**Core Exam Topics (High Priority)**: SQLi→RCE (all DBs + second-order + blind), Deserialization (Java/.NET/PHP/Node), File Upload bypasses→RCE, XSS→privileged action→RCE, PHP Type Juggling, SSTI, XXE.

See the Roadmap for the recommended order and time boxes.

### Study system (practice + exam ops)

| Resource | Why It Matters | Link |
|----------|----------------|------|
| Report snippets | Exam-style Markdown sections | [Report-Snippet-Templates.md](Report-Snippet-Templates.md) |
| Speed drills | Timed skill builders | [Speed-Drills.md](Speed-Drills.md) |
| Cold-start drills | Scenario cards without solutions first | [drills/Cold-Start-Drills.md](drills/Cold-Start-Drills.md) |
| Study log | Session diary + weak areas | [study-log/](study-log/) |
| Sink cheatsheet | 15-min white-box greps by language | [guides/Dangerous-Sinks-Cheatsheet.md](guides/Dangerous-Sinks-Cheatsheet.md) |
| Chain decision trees | “I found X → next Y” pivots | [guides/Chain-Decision-Trees.md](guides/Chain-Decision-Trees.md) |

### Methodology guides

| Topic | Guide |
|-------|-------|
| Code review checklists | [guides/Code-Review-Checklists.md](guides/Code-Review-Checklists.md) |
| Advanced SQLi | [guides/Advanced-SQLi-Techniques.md](guides/Advanced-SQLi-Techniques.md) |
| Blind SQLi automation | [guides/Blind-SQLi-Automation.md](guides/Blind-SQLi-Automation.md) |
| Postgres SQLi → RCE | [guides/Postgres-SQLi-to-RCE.md](guides/Postgres-SQLi-to-RCE.md) |
| Java deserialization | [guides/Java-Deserialization-Methodology.md](guides/Java-Deserialization-Methodology.md) |
| .NET deserialization | [guides/DotNet-Deserialization-Guide.md](guides/DotNet-Deserialization-Guide.md) |
| PHP deserialization | [guides/PHP-Deserialization-Patterns.md](guides/PHP-Deserialization-Patterns.md) |
| PHP type juggling | [guides/PHP-Type-Juggling-Methodology.md](guides/PHP-Type-Juggling-Methodology.md) |
| XSS → RCE chaining | [guides/XSS-to-RCE-Chaining.md](guides/XSS-to-RCE-Chaining.md) |
| File upload → RCE | [guides/File-Upload-to-RCE.md](guides/File-Upload-to-RCE.md) |
| LFI → RCE | [guides/LFI-to-RCE.md](guides/LFI-to-RCE.md) |
| XXE | [guides/XXE-Attack-Vectors.md](guides/XXE-Attack-Vectors.md) |
| SSTI | [guides/SSTI-Exploitation-Guide.md](guides/SSTI-Exploitation-Guide.md) |
| Dangerous sinks | [guides/Dangerous-Sinks-Cheatsheet.md](guides/Dangerous-Sinks-Cheatsheet.md) |
| Chain trees | [guides/Chain-Decision-Trees.md](guides/Chain-Decision-Trees.md) |

---

### Learning Material

| Order | Name | Link |
|--- | ----- | ----- |
| 1 | A Deep Dive into XXE | https://www.synack.com/blog/a-deep-dive-into-xxe-injection/ |
| 2 | Testing and Exploiting Java Deserialization | https://afinepl.medium.com/testing-and-exploiting-java-deserialization-in-2021-e762f3e43ca2 |
| 3 | Understanding Java Deserialization | https://nytrosecurity.com/2018/05/30/understanding-java-deserialization/ |
| 4 | Exploiting_and_Preventing_Deserialization_Vulnerabilities | https://owasp.org/www-chapter-vancouver/assets/presentations/2020-05_Exploiting_and_Preventing_Deserialization_Vulnerabilities.pdf |
| 5 | PHP Magic Tricks Type Juggling | https://owasp.org/www-pdf-archive/PHPMagicTricks-TypeJuggling.pdf |
| 6 | Paul's Security Weekly #572-  Type Juggling | https://www.youtube.com/watch?v=ASYuK01H3Po |
| 7 | Ippsec PHP Deserialization and PHAR Deserialization | https://www.youtube.com/watch?v=HaW15aMzBUM, https://www.youtube.com/watch?v=fHZKSCMWqF4 |
| 8 | Code that gets you pwn(s\|'d) - snyff | https://www.youtube.com/watch?v=BNHKlj-PMDc |
| 9 | Hacktricks SQL Injection | https://book.hacktricks.xyz/pentesting-web/sql-injection |
| 10 | Understanding PHP Object Injection | https://securitycafe.ro/2015/01/05/understanding-php-object-injection/ |
| 11 | Attacking .NET deserialization - Alvaro Muñoz | https://www.youtube.com/watch?v=eDfGpu3iE4Q |
| 12 | Hacktricks File Upload | https://book.hacktricks.xyz/pentesting-web/file-upload |
| 13 | PortSwigger Server-Side Template Injection | https://portswigger.net/research/server-side-template-injection |
| 14 | Friday the 13th: JSON Attacks (Black Hat) | https://www.blackhat.com/docs/us-17/thursday/us-17-Munoz-Friday-The-13th-Json-Attacks.pdf |
| 15 | WEB-300 OSWE Review (2025) - Jake Mayhew | https://medium.com/@jake.mayhew/web-300-oswe-review-offsec-web-expert-46074fbdb237 |
| 16 | The OSWE Guide (2026) - BRM | https://www.brunorochamoura.com/posts/oswe-guide/ |
| 17 | OffSec OSWE Review (2025) - Steflan | https://steflan-security.com/offsec-web-expert-oswe-review/ |
| 18 | OffSec AWAE/OSWE Review 2026 | https://rootshooter.medium.com/offsec-awae-oswe-review-2026-cad3c1e15946 |
| 19 | bmdyy OSWE-style Labs (tudo, testr, order, etc.) | https://github.com/bmdyy |

**Dedicated File Upload Resources** (critical for OSWE — many chains end here):
- Bypass techniques: double extension, content-type spoofing, magic bytes, case sensitivity, null byte (older PHP), .phar, polyglot files
- Finding writable directories + web root disclosure after upload
- See advanced-skeleton for upload step patterns and the Roadmap for dedicated practice week

### Practice Labs

**Note:** Only topics from the course will come up on the exam in most cases with slight variations.

| Order | Name | Type | Link |
|--- | ----- | ----- | --- |
| 1 | SECURECODE | VulnHub - Free | https://www.vulnhub.com/entry/securecode-1,651/ |
| 2 | Cryptobank1 | VulnHub - Free | https://www.vulnhub.com/entry/cryptobank-1,467/ |
| 3 | PentesterLab - SQLi to Shell - MySQL | Pentesterlab - Free | https://pentesterlab.com/exercises/from_sqli_to_shell/course |
| 4 | PentesterLab - SQLi to Shell 2 - MySQL | Pentesterlab - Free  | https://www.pentesterlab.com/exercises/from_sqli_to_shell_II/course |
| 5 | PentesterLab - SQLi to Shell - Postgres | Pentesterlab - Free  | https://pentesterlab.com/exercises/from_sqli_to_shell_pg_edition/course |
| 6 | Java Deserialization WebApp | GitHub - Free | https://github.com/hvqzao/java-deserialize-webapp |
| 7 | XSS and MySQL FILE | Pentesterlab - Free | https://pentesterlab.com/exercises/xss_and_mysql_file/course, https://sarthaksaini.com/2019/awae/xss-rce.html |
| 8 | Zors |  VulnHub - Free | https://www.vulnhub.com/entry/tophatsec-zorz,117/ |
| 9 | XXE-Study |  GitHub - Free | https://github.com/HLOverflow/XXE-study |
| 10 | GoSecure - Template Injection Workshop | Workshop - Free | https://gosecure.github.io/template-injection-workshop/, https://www.youtube.com/watch?v=I7xQZOvZzIw |
| 11 | GoSecure - XXE Workshop | Workshop - Free | https://gosecure.github.io/xxe-workshop/ |
| 12 | Pwnworks | .NET Deserialization Github - Free | https://github.com/abhisek/pwnworks/tree/master/challenges/dotnet-deserialization |
| 13 | dev/random/pipe | PHP Deserialization VulnHub - Free | https://www.vulnhub.com/entry/devrandom-pipe,124/ |
| 14 | bmdyy Labs (tudo, testr, order...) | GitHub - OSWE-style whitebox | https://github.com/bmdyy |
| 15 | Official WEB-300 Challenge Labs | OffSec course (required practice) | Complete all white-box + black-box labs and fully script chains |


### Vulnerability Writeups

Real world examples

| Order | Name | Link |
|--- | ----- | ----- |
| 1 | Reflected XSS to Account Takeover | https://medium.com/a-bugz-life/from-reflected-xss-to-account-takeover-showing-xss-impact-9bc6dd35d4e6 |
| 2 | dotCMS 5.1.5: Exploiting H2 SQL injection to RCE | https://blog.sonarsource.com/dotcms515-sqli-to-rce?redirect=rips |
| 3 | ATutor Authentication Bypass | https://rebraws.github.io/ATutorAuthBypass/ |





### Scripting

Python examples of pocs that can be used for write single click pocs

| Order | Name | Type | Link |
|--- | ----- | ----- | --- |
| 1 | Python requests documentation | https://docs.python-requests.org/en/master/ |
| 2 | HTB Scripts | https://github.com/s0j0hn/AWAE-OSWE-Prep |
| 3 | OutHackThem - Single Script Exploit | https://github.com/wetw0rk/AWAE-PREP/tree/master/Community%20Contributions%20%26%20Enhancements/Code%20Improvements/XSS%20and%20MySQL/OutHackThem%20-%20Single%20Script%20Exploit |
| 4 | SQLi scripts |  https://github.com/wetw0rk/AWAE-PREP/tree/master/Community%20Contributions%20%26%20Enhancements/Challenges/PortSwigger |
| 5 | A python based blind SQL injection exploitation script|  https://github.com/21y4d/blindSQLir |



 
### Cheat Sheets

| Order | Name |  Link |
|--- | ----- | ----- |
| 1 | reverse shell cheat sheet | https://highon.coffee/blog/reverse-shell-cheat-sheet/ |
| 2 | Payload All the Things | https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Upload%20Insecure%20Files, https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Insecure%20Deserialization |
| 3 | sql injection cheat sheet | https://portswigger.net/web-security/sql-injection/cheat-sheet |
| 4 | Java Deserialization Cheat Sheet | https://github.com/GrrrDog/Java-Deserialization-Cheat-Sheet/blob/master/README.md |
| 5 | Deserialization Cheat Sheet | https://github.com/OWASP/CheatSheetSeries/blob/master/cheatsheets/Deserialization_Cheat_Sheet.md |
| 6 | SQL Injection Cheat Sheet | https://www.netsparker.com/blog/web-security/sql-injection-cheat-sheet/#StringwithoutQuotes |
| 7 | PHP Object Injection Cheat Sheet | https://nitesculucian.github.io/2018/10/05/php-object-injection-cheat-sheet/ |



### Exam Resources and Reporting  
Exam related resources that might be useful

| Order |  Name | Link |
|--- | ----- | ---- | 
| 1 | Proctoring Student Manual | https://help.offensive-security.com/hc/en-us/articles/360050299352-Proctoring-Tool-Student-Manual |
| 2 | OSWE / WEB-300 Exam Guide | https://help.offensive-security.com/hc/en-us/articles/360046869951-WEB-300-Advanced-Web-Attacks-and-Exploitation-OSWE-Exam-Guide |
| 3 | Offsec Report Template Generator | https://github.com/noraj/OSCP-Exam-Report-Template-Markdown |
| 4 | oswe review - tips and tricks | https://www.youtube.com/watch?v=ElZ7fFE9Gr4 |
| 5 | OSWE Review (AWAE Course) | https://stacktrac3.co/oswe-review-awae-course/#Losing_Steam_and_Yolo%E2%80%99ing_It |
| 6 | Obligatory OSWE Retrospective (2025) | https://notateamserver.xyz/blog/oswe-review/ |
| 7 | OffSec Web Expert (OSWE) Review (2025) | https://steflan-security.com/offsec-web-expert-oswe-review/ |
| 8 | WEB-300 OSWE Review (2025) | https://medium.com/@jake.mayhew/web-300-oswe-review-offsec-web-expert-46074fbdb237 |
| 9 | OffSec AWAE/OSWE Review — 2026 | https://rootshooter.medium.com/offsec-awae-oswe-review-2026-cad3c1e15946 |


### HTB Writeups
Hackthebox writeups with vulnerabilities and exploitation paths similiar to lab and course content. Video walkthroughs of these writeups can also be found [here](https://www.youtube.com/c/ippsec/videos)

| Order | Machine Name | Vulnerability | Link |
|--- | ----- | ----- | --- |
| 1 | Popcorn | Insecure File Upload | https://0xdf.gitlab.io/2020/06/23/htb-popcorn.html |
| 2 | Vault | Insecure File Upload | https://0xrick.github.io/hack-the-box/vault/ |
| 3 | Arkham | Java Deserialization | https://0xrick.github.io/hack-the-box/arkham/ |
| 4 | Jsonl | .NET Deserialization | https://0xdf.gitlab.io/2020/02/15/htb-json.html |
| 5 | Cereal | Authentication Bypass | https://0xdf.gitlab.io/2021/05/29/htb-cereal.html |
| 6 | Celestial | Node Deserialization | https://0xdf.gitlab.io/2018/08/25/htb-celestial.html |
| 7 | Unattendedl | SQL Injection (MySQL) | https://0xrick.github.io/hack-the-box/unattended/|
| 8 | Ghoul | Zip Traversal | https://0xrick.github.io/hack-the-box/ghoul/ |
| 9 | Falafel | SQL Injection (MySQL), Type Juggling | https://0xdf.gitlab.io/2018/06/23/htb-falafel.html |
| 10 | Fighter | SQL Injection (MS-SQL) | https://fdlucifer.github.io/2020/06/03/fighter/ |



### Pre/Post-OSWE Resources

Good resources to learn before starting WEB-300/OSWE or for supplementary practice after finishing the exam. Many of these complement the core white-box chaining focus.

| Order | Name | Link |
|--- | ----- | ----- |
| 1 | Exploiting Second Order SQLi Flaws by using Burp & Custom Sqlmap Tamper | https://pentest.blog/exploiting-second-order-sqli-flaws-by-using-burp-custom-sqlmap-tamper/ |
| 2 | Pentesterlab Free | https://www.pentesterlab.com/exercises?only=free |
| 3 | Portswigger Websecurityacademy | https://portswigger.net/web-security/all-labs |
| 4 | How to Test Horizontal & Vertical Authorization Issues in Web Application | https://pentest.blog/how-to-test-horizontal-vertical-authorization-issues-in-web-application/ |
| 5 | OWASP Code Review Guide | https://owasp.org/www-pdf-archive/OWASP_Code_Review_Guide_v2.pdf/ |
| 6 | Security .NET Deserialization | https://www.slideshare.net/MSbluehat/dangerous-contents-securing-net-deserialization, https://www.youtube.com/watch?v=oxlD8VWWHE8 |
| 7 | Friday the 13th: JSON Attacks | https://www.youtube.com/watch?v=oUAeWhW5b8c |
| 8 | Hacker101 - Source Code Review | https://www.hacker101.com/sessions/source_review.html |


## PoC Development Guides

Comprehensive guides for building production-ready exploit scripts for OSWE.

| Order | Name | Link |
|-------|------|------|
| 0 | **OSWE Study Roadmap** (start here) | [Roadmap](OSWE-Study-Roadmap.md) |
| 1 | Building a Reusable OSWE PoC Skeleton | [Guide](Building%20a%20Reusable%20OSWE%20PoC%20Skeleton.md) |
| 2 | Exploit Writing for OSWE | [Guide](Exploit%20Writing%20for%20OSWE.md) |
| 3 | Complete PoC Guide | [Guide](COMPLETE-POC-GUIDE.md) |
| 4 | OSWE PoC Skeleton Guide | [Guide](OSWE-PoC-Skeleton-Guide.md) |
| 5 | Advanced PoC Skeleton | [Example](poc-examples/advanced-skeleton/) |
| 6 | File Upload to RCE | [Guide](guides/File-Upload-to-RCE.md) + [PoC](poc-examples/file-upload-rce/) |
| 7 | Exam-Day Runbook | [Exam-Day-Runbook.md](Exam-Day-Runbook.md) |
| 8 | Report Snippet Templates | [Report-Snippet-Templates.md](Report-Snippet-Templates.md) |

**File upload**: Full guide + stage-based PoC live under `guides/File-Upload-to-RCE.md` and `poc-examples/file-upload-rce/`.


## Vulnerability Case Studies

Detailed case studies documenting real-world vulnerabilities with exploitation chains. Many have been expanded with environment details, full chains, OSWE tips, and references to the corresponding rich PoC + Notes in `poc-examples/`. Use `notes/CASE-template.md` when adding your own.

See also the [Study Roadmap](OSWE-Study-Roadmap.md) for the recommended order to tackle them.

| Order | Application | Vulnerability Type | Link |
|-------|-------------|-------------------|------|
| 1 | Atmail 6.4 | XSS to RCE | [Study](Atmail-6.4-XSS-RCE-Study.md) + [Case](notes/ATMAIL-6.4.md) |
| 2 | ATutor 2.2.1 | Type Juggling | [Notes](notes/ATUTOR-2.2.1-TYPE-JUGGLING.md) |
| 3 | ATutor 2.2.1 | Authentication Bypass to RCE | [Notes](notes/ATUTOR-2.2.1-AUTH-RCE.md) |
| 4 | Bassmaster 1.5.1 | JavaScript Injection | [Notes](notes/BASSMASTER-1.5.1-JS-INJECTION.md) |
| 5 | DotNetNuke | Cookie Deserialization | [Notes](notes/DOTNETNUKE-COOKIE-DESERIALIZATION.md) |
| 6 | ManageEngine | SQL Injection to RCE | [Notes](notes/MANAGEENGINE-APPS-MANAGER-SQLI-RCE.md) |
| 7 | Generic .NET | ViewState Deserialization | [Notes](notes/DOTNET-VIEWSTATE-DESERIALIZATION.md) |
| 8 | Generic Java | Deserialization (Commons Collections) | [Notes](notes/JAVA-DESERIALIZATION-COMMONS-COLLECTIONS.md) |
| 9 | Generic PHP | Object Injection | [Notes](notes/PHP-OBJECT-INJECTION.md) |
| 10 | Generic Node.js | Deserialization | [Notes](notes/NODEJS-DESERIALIZATION.md) |
| 11 | Generic MSSQL | SQL Injection (xp_cmdshell) | [Notes](notes/MSSQL-SQLI-XP-CMDSHELL.md) |
| 12 | Generic | Second-Order SQL Injection | [Notes](notes/SECOND-ORDER-SQLI.md) |
| 13 | Generic Flask | SSTI (Jinja2) | [Notes](notes/SSTI-JINJA2-FLASK.md) |
| 14 | Generic XML Parser | XXE File Read/SSRF | [Notes](notes/XXE-FILE-READ-SSRF.md) |
| 15 | Generic Web App | File Upload to Webshell RCE | [Notes](notes/FILE-UPLOAD-TO-RCE.md) + [Guide](guides/File-Upload-to-RCE.md) + [PoC](poc-examples/file-upload-rce/) |


## Production-Ready PoC Examples

Working exploit scripts with documentation organized by vulnerability type.

### Deserialization Vulnerabilities

| Order | Type | Example | PoC | Notes |
|-------|------|---------|-----|-------|
| 1 | Java | Commons Collections | [PoC](poc-examples/java-deserialization-commons/) | [Notes](notes/JAVA-DESERIALIZATION-COMMONS-COLLECTIONS.md) |
| 2 | .NET | ViewState Deserialization | [PoC](poc-examples/dotnet-viewstate-deserialization/) | [Notes](notes/DOTNET-VIEWSTATE-DESERIALIZATION.md) |
| 3 | PHP | Object Injection | [PoC](poc-examples/php-object-injection/) | [Notes](notes/PHP-OBJECT-INJECTION.md) |
| 4 | Node.js | node-serialize | [PoC](poc-examples/nodejs-deserialization/) | [Notes](notes/NODEJS-DESERIALIZATION.md) |

### XSS to RCE Chains

| Order | Application | Vulnerability | PoC | Notes |
|-------|-------------|---------------|-----|-------|
| 1 | Atmail 6.4 | XSS to RCE | [PoC](poc-examples/atmail-xss-rce/) | [Study](Atmail-6.4-XSS-RCE-Study.md) |

### Authentication & Type Confusion

| Order | Application | Vulnerability | PoC | Notes |
|-------|-------------|---------------|-----|-------|
| 1 | ATutor 2.2.1 | Type Juggling | [PoC](poc-examples/atutor-type-juggling/) | [Notes](notes/ATUTOR-2.2.1-TYPE-JUGGLING.md) |

### JavaScript Injection

| Order | Application | Vulnerability | PoC | Notes |
|-------|-------------|---------------|-----|-------|
| 1 | Bassmaster 1.5.1 | JS Injection | [PoC](poc-examples/bassmaster-js-injection/) | [Notes](notes/BASSMASTER-1.5.1-JS-INJECTION.md) |

### SQL Injection

| Order | Type | Example | PoC | Notes |
|-------|------|---------|-----|-------|
| 1 | MSSQL | xp_cmdshell RCE | [PoC](poc-examples/mssql-sqli-xp-cmdshell/) | [Notes](notes/MSSQL-SQLI-XP-CMDSHELL.md) |
| 2 | MySQL | Second-Order SQLi | [PoC](poc-examples/second-order-sqli/) | [Notes](notes/SECOND-ORDER-SQLI.md) |
| 3 | PostgreSQL (ManageEngine-class) | Apps Manager SQLi → RCE | [PoC](poc-examples/manageengine-sqli/) | [Notes](notes/MANAGEENGINE-APPS-MANAGER-SQLI-RCE.md) |

### Template Injection

| Order | Type | Example | PoC | Notes |
|-------|------|---------|-----|-------|
| 1 | Jinja2 | Flask SSTI | [PoC](poc-examples/ssti-jinja2-flask/) | [Notes](notes/SSTI-JINJA2-FLASK.md) |

### XXE (XML External Entity)

| Order | Type | Example | PoC | Notes |
|-------|------|---------|-----|-------|
| 1 | XXE | File Read/SSRF | [PoC](poc-examples/xxe-file-read-ssrf/) | [Notes](notes/XXE-FILE-READ-SSRF.md) |

### File Upload to RCE

| Order | Type | Example | PoC | Notes | Guide |
|-------|------|---------|-----|-------|-------|
| 1 | Generic | Webshell via weak upload filters (PHP/ASPX/JSP) | [PoC](poc-examples/file-upload-rce/) | [Notes](notes/FILE-UPLOAD-TO-RCE.md) | [Guide](guides/File-Upload-to-RCE.md) |

**Key techniques covered**: double extension, magic bytes, Content-Type bypass, case tricks, null byte (legacy), combined, post-upload discovery, direct execution vs LFI trigger.

### PoC lab manuals (Notes.md)

High-depth manuals now include Java Commons, MSSQL, Atmail, ManageEngine, PHP POI, ATutor, Bassmaster, **Node deserial**, **.NET ViewState**, **XXE**, file upload, SSTI, and second-order SQLi. Prefer these over thin case shells when practicing hands-on.

---

## Security

Authorized security testing, CTF challenges, and OSWE exam preparation only. Do not include credentials, lab access tokens, or links to non-public resources.

