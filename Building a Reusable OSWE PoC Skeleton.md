# 01 - Building a Reusable OSWE PoC Skeleton - Project Setup

One of the exam requirements for [Offensive Security's Advanced Web Attacks and Exploitation ](https://www.offsec.com/courses/web-300/)course is the creation of Proof of Concept (PoC) code that, when executed, exploits a web application to obtain a shell or retrieving the required proof.txt file. While students are free to choose what programming language they might use to create a PoC, Python is the dominant choice among both students and course mentors.

The course consists of many case studies of vulnerable applications and how each one had multiple points of exploitation that, when chained together, would allow complete compromise and remote code execution. After these case studies are completed, there are lab environments that are configured for white box testing. A debug machine with all the source code is provided and then a victim machine where students are expected to find exploit paths and practice writing PoCs that will allow the students to retrieve a series of proof flags on the victim machine and the last flag for each machine requires command execution on the machine.

When I started on the first "challenge lab", I realized that I didn't have a game plan for writing the code. I stepped back after starting the first challenge and looked at the big overall picture. What are some commonalities going to exist between all of these machines on the labs that would allow me to optimize my code writing so that I could have a baseline or skeleton script that I could always use as I went from challenge to challenge.

I started this course with experience programming in Perl, Java, along with a handful of other languages where my grasp was tenuous. Perl could have been an OK choice for creating the PoCs, but Python is really the language de jour just glancing at the course and the Discord channel. Given what I know now, one's Python skill by the end of the course should be at an intermediate level. Standard Python knowledge of making and parsing HTTP requests, reading and writing files, along with dealing with HTML. Full disclaimer: I didn't finish all the course modules due to having also gone through the HTB CWEE course material. I felt that certain sections of the course would be repeating knowledge I already had acquired. After the first challenge lab, I began working on the beginnings of a PoC skeleton which I continued to refine or even rebuild over the next few labs. By the time I had finished the fourth lab, my code base was pretty stable.

What I set out to accomplish was to create a scaffold that relied on Python standard libraries or well known libraries. I wanted external dependencies kept to a minimum as well as having an audit trail while the script was running. Sure you can insert print statements galore, but with a little work, one can create their own logging system that can be called like other libraries.

To that end, I always used [uv](https://docs.astral.sh/uv/) to initialize my challenge labs base directory. `uv` currently isn't a package one can install with `apt install`. Installation is fairly straightforward though. From a terminal, run:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

This will install `uv` in `$HOME/.local/bin/uv`. Let's say I configured a top level directory for my challenge labs like `$HOME/OSWE/ChallengeLabs`. I can `cd` to `ChallengeLabs` and then start the first lab project. For the sake of this and the rest of the articles, I'll be using the fictitious web application `Authrise` as the lab environment. Let's set this up so that by the end of this series we'll have a mostly or totally complete PoC skeleton written in Python. I use `uv` as a replacement for `pip + venv + poetry-style behavior`. `uv` keeps the skeleton reproducible across all labs. and will allow us to install various third-party dependencies in the virtual environment it creates.

The base of the project, from `$HOME/OSWE/ChallengeLabs`, is created by executing (remove `--vcs git` if you don't want version control):

```bash
❯ uv init --bare --no-readme --vcs git authrise
Initialized project `authrise` at `$HOME/OSWE/ChallengeLabs/authrise`
```

So the layout should be like this.

```bash
❯ tree -a authrise
authrise
├── .git
│   ├── HEAD
│   ├── config
│   ├── description
│   ├── hooks
│   │   ├── applypatch-msg.sample
│   │   ├── commit-msg.sample
│   │   ├── fsmonitor-watchman.sample
│   │   ├── post-update.sample
│   │   ├── pre-applypatch.sample
│   │   ├── pre-commit.sample
│   │   ├── pre-merge-commit.sample
│   │   ├── pre-push.sample
│   │   ├── pre-rebase.sample
│   │   ├── pre-receive.sample
│   │   ├── prepare-commit-msg.sample
│   │   ├── push-to-checkout.sample
│   │   ├── sendemail-validate.sample
│   │   └── update.sample
│   ├── info
│   │   └── exclude
│   ├── objects
│   │   ├── info
│   │   └── pack
│   └── refs
│       ├── heads
│       └── tags
├── .gitignore
└── pyproject.toml

```

`pyproject.toml` will currently contain a very basic structure which we'll fill in by editing or managing with `uv` over the course of these articles.

```bash
❯ cat pyproject.toml
[project]
name = "authrise"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = []
```

Keeping generated artifacts out of version control reduces noise and makes reviewing changes to your PoC much easier.

If you decide to use version control with git, now is a good time to configure `.gitignore` so that various artifacts won't end up in version control. I found this configuration a good starting off point. I'm using [VS Codium](https://vscodium.com/)for my IDE with various plugins. Your .gitignore might look significantly different.

```bash
# Python-generated files
__pycache__/
*.py[oc]
build/
dist/
wheels/
*.egg-info

# Virtual environments
.venv

# Environments
.env
env/

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# vscode
.vscode/
```

Given some thought to other pieces to start with, I created a few directories for storing logs, any items that might be saved from the exploit into archives, and a place to store screenshots. For notes, I created `Notes.md` in the root directory.

```bash
❯ touch Notes.md
❯ mkdir {Archives,Screenshots,Logs}
❯ tree
.
├── Archives
├── Logs
├── Notes.md
├── Screenshots
└── pyproject.toml

4 directories, 2 files

```

* Archives/ — saved artifacts from exploitation (responses, dumps, tokens)
* Logs/ — structured runtime logs for debugging and auditability
* Screenshots/ — exam-safe references when copying files is prohibited

This will be the directory structure for every lab and for the exam. We'll extend this in later articles by adding custom modules and building the PoC skeleton. I used `Notes.md` to save any information I thought might be relevant to understanding the web application presented. This would include POST request bodies along with responses, database table descriptions, etc... For the exam, copying code from the Offsec machines to your machine is strictly forbidden, so having screenshots is a good way to remind yourself where a certain vulnerability lies.

Up until now, I haven’t made mention of any Python code. What you name your script is largely a matter of preference. I tended to favor either `exploit.py` or the name of the target application. For this example, I’ll simply use `poc.py`.

Below is a deliberately minimal starting point:

```python
def main():
	print("Starting PoC")
	
if __name__ == "__main__":
    main()
```

This code does nothing interesting by design. Its purpose is simply to establish a consistent entry point that we will extend over time. As the series progresses, this file will grow to include context handling, structured logging, payload hosting, concurrency, and stage-based control flow. Each PoC requires configuration in order to run against a target. At a minimum, this includes details such as the target address, listening interfaces, and various feature or stage toggles. To support this, the next step is to make the project interactive by wiring up a flexible command-line interface using `argparse`.

We’ll also briefly look at using an environment file for configuration. While this can keep commands short, it comes with trade-offs. In the next article, I’ll show how to configure both approaches and explain why I ultimately prefer explicit command-line arguments for clarity, discoverability, and operator control.

My plan for this series is to build the code base to show you how to I built up my PoC over the course of a few months with the goal of having you develop your own. I'm planning on proceeding from single topics that progress to testing the PoC against a fictitious server with an SQL flaw that will allow us to extract a token and showing the difference between a linear and binary search.

## Series Roadmap

This article establishes the foundation for the PoC skeleton. Each subsequent part builds on this structure incrementally.

2. [02 - Argument Parsing for OSWE PoCs - argparse vs dotenv](https://fermiparadox.gitbook.io/fermiparadox/oswe-poc-skeleton/02-argument-parsing-for-oswe-pocs-argparse-vs-dotenv)
3. [03 - Context Management with Dataclasses](https://fermiparadox.gitbook.io/fermiparadox/oswe-poc-skeleton/03-context-management-with-dataclasses)
4. Control Flow and Stage Management
5. Structured logging for exploit development
6. A custom web server for hosting or receiving payloads
7. Concurrency concepts using async
8. A fictitious blind SQL injection example (linear vs binary and async variants)

By the end of this series, you should have a reusable PoC skeleton that you can adapt to each lab or exam target with minimal rewrites.


# 02 - Argument Parsing for OSWE PoCs - argparse vs dotenv

This article builds directly on the project structure established in [Part 01](https://fermiparadox.gitbook.io/fermiparadox/oswe-poc-skeleton/01-building-a-reusable-poc-skeleton-for-oswe-project-setup) and focuses on how configuration is supplied to the PoC at runtime.

Python's argparse module is the standard way to build command-line interfaces (CLI). For building a PoC exploit script, one can control how inputs like targets, proxies, etc... are handled. By implementing a comprehensive design, the need to constantly re-write scripts between runs and between labs is eliminated. Generally, knowing all that might be built into the script is difficult.

How many arguments do you need? Should there be defaults for certain arguments? What arguments will be required? Asking yourself questions like this will guide the shape of your script and the various arguments that are considered. What we're about to do isn't written in stone. Don't be afraid to remove items that don't make sense to your or to add ones that do. It's your skeleton to construct as you please. With that said, let's look at a basic command that we might build using argparse and dotenv.

As an alternative, some projects use an environment file to store configuration values. This approach can reduce command length and centralize configuration, which can be appealing when iterating quickly.

Below is an example `.env` file containing the same types of values we would otherwise pass via the command line. The goal here is not to build a full configuration system, but to highlight how this approach differs in practice.

```bash
uv add python-dotenv
```

```
TARGET_IP=192.168.122.45
TARGET_PORT=8080
TARGET_API_PORT=5001

LISTENING_IP=10.8.0.5
LISTENING_PORT=9001
PAYLOAD_PORT=9999

DELAY=5
USER_FILE=user.json
SAVE_IDENTITY=output.json
REGISTER=true
COMPLEXITY=high
INCLUDE_ADDRESS=true
INCLUDE_PHONE=false
CHARSET=ascii
PROXY=http://127.0.0.1:8080
```

```python
from pathlib import Path

from dotenv import dotenv_values

CHARSETS = {
    "alpha": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "alnum": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    "hex": "0123456789abcdef",
    "ascii": "".join(chr(i) for i in range(32, 127)),  # printable ASCII
    "symbols": "!@#$%^&*()-_=+[{]}\\|;:'\",<.>/?`~",
    "base64": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=",
    "numeric": "0123456789",
}

DEFAULTS = {
    "TARGET_PORT": 80,
    "TARGET_API_PORT": 5000,
    "LISTENING_IP": "127.0.0.1",
    "LISTENING_PORT": 9001,
    "PAYLOAD_PORT": 9999,
    "DELAY": 3,
    "USER_FILE": "user.json",
    "REGISTER": False,
    "INCLUDE_ADDRESS": False,
    "INCLUDE_PHONE": False,
    "CHARSET": "alnum",
    "PROXY": None,
}

REQUIRED_KEYS = ["TARGET_IP"]

INT_KEYS = {
    "TARGET_PORT",
    "TARGET_API_PORT",
    "LISTENING_PORT",
    "PAYLOAD_PORT",
    "DELAY",
}

BOOL_KEYS = {
    "REGISTER",
    "INCLUDE_ADDRESS",
    "INCLUDE_PHONE",
}


def parse_config(env_file: str = "authrise.env") -> dict[str, object]:
    env_path = Path(env_file)
    if not env_path.exists():
        raise FileNotFoundError(f"Missing environment file: {env_file}")

    env = dotenv_values(env_path)
    config = {**DEFAULTS, **env}  # env overrides defaults

    # Validate required
    for key in REQUIRED_KEYS:
        if key not in config or not config[key]:
            raise ValueError(f"Missing required config: {key}")

    # Convert types
    for key in INT_KEYS:
        if key in config:
            config[key] = int(config[key])

    for key in BOOL_KEYS:
        if key in config:
            val = str(config[key]).lower()
            config[key] = val in {"true", "1", "yes", "on"}

    return config


def main():
    config = parse_config()

    print(f"Register new user: {config['REGISTER']}")
    print(f"Target IP: {config['TARGET_IP']}")
    print(f"Target Port: {config['TARGET_PORT']}")
    print(f"Listening IP: {config['LISTENING_IP']}")
    print(f"Listening Port: {config['LISTENING_PORT']}")


if __name__ == "__main__":
    main()

```

```bash
❯ uv run poc-env.py
Register new user: True
Target IP: 192.168.122.45
Target Port: 8080
Listening IP: 10.8.0.5
Listening Port: 9001
```

One major difference between the dotenv and argparse methods is that when using argparse, you have an instant help flag that isn't available with the dotenv method. One can write a help method for a dotenv by adding in code like:

One immediate drawback of the environment file approach is discoverability. Unlike `argparse`, there is no built-in `--help` flag. While it’s possible to manually emulate help output, doing so quickly becomes custom, brittle, and repetitive across projects.

For some workflows, environment files are a reasonable choice. However, when developing a reusable PoC skeleton, especially one intended to be run repeatedly, shared, or revisited under time pressure. I found the lack of built-in help and the need for manual type conversion to be limiting. For those reasons, I ultimately preferred an explicit command-line interface built with `argparse`.

Recall, we have a fictitious `uv` project in a directory labeled authrise. If you `cd` into that directory, and use an editor to build a file we'll call poc-args.py. The aim is to start building a workable PoC that we can reuse and doesn't rely on hard-coded values thus providing flexibility to any environment we will end up working in. Here's an example of the beginnings of a simple CLI with arguments.

```bash
uv run poc-args.py --target-ip 192.168.200.10 --target-port 5000 --listening-ip 192.168.1.5 --listening-port 9999
```

How would you configure such a script with a simple CLI like the above.

```python
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="OSWE Application Exploit.")
    parser.add_argument("--target-ip", type=str, required=True, help="Input file path")
    parser.add_argument("--target-port", type=int, default=80, help="Input file path")
    parser.add_argument(
        "--listening-port",
        type=int,
        default=9001,
        help="Port to listen for reverse shell (default: 9001)",
    )
    parser.add_argument(
        "--listening-ip", type=str, help="IP to listen on for reverse shell"
    )

    return parser.parse_args()


def main():
    args = parse_args()
    print(f"Target IP: {args.target_ip}")
    print(f"Target Port: {args.target_port}")
    print(f"Listening IP: {args.listening_ip}")
    print(f"Listening Port: {args.listening_port}")


if __name__ == "__main__":
    main()

```

```bash
❯ uv run poc-args.py --target-ip 192.168.200.10 --target-port 5000 --listening-ip 192.168.1.5 --listening-port 9999
Target IP: 192.168.200.10
Target Port: 5000
Listening IP: 192.168.1.5
Listening Port: 9999
```

```bash
❯ uv run poc-args.py --help
usage: poc-args.py [-h] --target-ip TARGET_IP [--target-port TARGET_PORT] [--listening-port LISTENING_PORT]
                   [--listening-ip LISTENING_IP]

OSWE Application Exploit.

options:
  -h, --help            show this help message and exit
  --target-ip TARGET_IP
                        Input file path
  --target-port TARGET_PORT
                        Input file path
  --listening-port LISTENING_PORT
                        Port to listen for reverse shell (default: 9001)
  --listening-ip LISTENING_IP
                        IP to listen on for reverse shell
```

If you consider the content being presented in the case studies, one can figure out what might be good elements to consider for adding into a script as arguments. Some are fairly obvious like the target ip address and port, but some might not be, at least at first glance. Consider what kinds of elements might pop up repeatedly.

A nice feature of argparse is that allows you to group arguments into sections. The `add_argument_group` method helps facilitate this. The grouping really helps when printing the options if you need a reminder of all the possible elements you can add as input. My grouping broke out into target options, attacker options, identity options, and the aptly named optional options.

For target options, I considered the ip address, port, and a possible api port. I could have expanded this to have a api ip address if I desired. Attacker options centered around my Kali host and how I'd present say a reverse shell port or payload delivery using a web server to the victim. Identity options were configured to make use of my custom identity generator. There are options that allow me to reuse an existing configured user on the web application or set the password complexity, etc...

Once I started seeing the same categories of inputs appear repeatedly across labs, I stopped thinking in terms of individual flags and started thinking in terms of roles. Target details, attacker settings, exploit behavior, and identity data each form a coherent group that benefits from being treated consistently.

The following example represents the point where my argument parsing stabilized. It is intentionally broader than any single lab requires, because its purpose is to be reusable.

```python
import argparse

CHARSETS = {
    "alpha": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "alnum": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    "hex": "0123456789abcdef",
    "ascii": "".join(chr(i) for i in range(32, 127)),  # printable ASCII
    "symbols": "!@#$%^&*()-_=+[{]}\\|;:'\",<.>/?`~",
    "base64": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=",
    "numeric": "0123456789",
}


def parse_args():
    parser = argparse.ArgumentParser(description="OSWE Application Exploit.")

    # --- Target options ---
    target_group = parser.add_argument_group("Target options")
    target_group.add_argument(
        "--target-ip", type=str, required=True, help="Target server IP address"
    )
    target_group.add_argument(
        "--target-port",
        type=int,
        default=80,
        help="Target web frontend port (default: 80)",
    )
    target_group.add_argument(
        "--target-api-port",
        type=int,
        default=5000,
        help="Target API port (default: 5000)",
    )

    # --- Attacker options ---
    attacker_group = parser.add_argument_group("Attacker options")
    attacker_group.add_argument(
        "--listening-ip",
        type=str,
        default="127.0.0.1",
        help="IP to listen on for reverse shell (default: 127.0.0.1)",
    )
    attacker_group.add_argument(
        "--listening-port",
        type=int,
        default=9001,
        help="Port to listen for reverse shell (default: 9001)",
    )
    attacker_group.add_argument(
        "--payload-port",
        type=int,
        default=9999,
        help="Port to listen for xss or other payload (default: 9999)",
    )

    # --- Exploit options ---
    exploit_group = parser.add_argument_group("Exploit options")
    exploit_group.add_argument(
        "--delay",
        type=int,
        default=3,
        help="Response delay in seconds for timing inference (default: 3)",
    )

    # --- Identity options ---
    identity_group = parser.add_argument_group("Identity options")
    identity_group.add_argument(
        "--user-file",
        type=str,
        default="user.json",
        help="Path to existing exploit user JSON (default: user.json)",
    )
    identity_group.add_argument(
        "--save-identity",
        type=str,
        help="Path to save newly generated identity JSON",
    )
    identity_group.add_argument(
        "--register",
        action="store_true",
        default=False,
        help="Whether the user has already been registered",
    )
    identity_group.add_argument(
        "--complexity", choices=["low", "medium", "high"], help="Password complexity"
    )
    identity_group.add_argument(
        "--include-address", action="store_true", help="Include street address"
    )
    identity_group.add_argument(
        "--include-phone", action="store_true", help="Include phone number"
    )

    optional_group = parser.add_argument_group("Optional options")
    optional_group.add_argument(
        "--charset",
        choices=CHARSETS.keys(),
        default="alnum",
        help="Charset to use for blind SQLi password extraction.",
    )
    optional_group.add_argument(
        "--proxy", default=None, help="Turn on Burp Suite proxy for debugging."
    )

    return parser.parse_args()


def main():
    args = parse_args()
    print(f"Target IP: {args.target_ip}")
    print(f"Target Port: {args.target_port}")
    print(f"Listening IP: {args.listening_ip}")
    print(f"Listening Port: {args.listening_port}")


if __name__ == "__main__":
    main()

```

```python
❯ uv run poc.py --help
usage: poc.py [-h] --target-ip TARGET_IP [--target-port TARGET_PORT] [--target-api-port TARGET_API_PORT]
              [--listening-ip LISTENING_IP] [--listening-port LISTENING_PORT] [--payload-port PAYLOAD_PORT] [--delay DELAY]
              [--user-file USER_FILE] [--save-identity SAVE_IDENTITY] [--register] [--complexity {low,medium,high}]
              [--include-address] [--include-phone] [--charset {alpha,alnum,hex,ascii,symbols,base64,numeric}] [--proxy PROXY]

OSWE Application Exploit.

options:
  -h, --help            show this help message and exit

Target options:
  --target-ip TARGET_IP
                        Target server IP address
  --target-port TARGET_PORT
                        Target web frontend port (default: 80)
  --target-api-port TARGET_API_PORT
                        Target API port (default: 5000)

Attacker options:
  --listening-ip LISTENING_IP
                        IP to listen on for reverse shell (default: 127.0.0.1)
  --listening-port LISTENING_PORT
                        Port to listen for reverse shell (default: 9001)
  --payload-port PAYLOAD_PORT
                        Port to listen for xss or other payload (default: 9999)

Exploit options:
  --delay DELAY         Response delay in seconds for timing inference (default: 3)

Identity options:
  --user-file USER_FILE
                        Path to existing exploit user JSON (default: user.json)
  --save-identity SAVE_IDENTITY
                        Path to save newly generated identity JSON
  --register            Whether the user has already been registered
  --complexity {low,medium,high}
                        Password complexity
  --include-address     Include street address
  --include-phone       Include phone number

Optional options:
  --charset {alpha,alnum,hex,ascii,symbols,base64,numeric}
                        Charset to use for blind SQLi password extraction.
  --proxy PROXY         Turn on Burp Suite proxy for debugging.
```

At this point, we have a well-defined interface for interacting with the PoC. The script can be configured explicitly, arguments are discoverable, and related options are grouped in a way that reflects how exploits are actually built and operated.

What we do *not* yet have is a clean way to pass this configuration through the rest of the codebase without threading argument objects everywhere. In the next article, we’ll address that by introducing a structured context object using Python dataclasses, which will allow us to centralize state and simplify the logic of multi-stage exploits.

#### Next:

[03 - Context Management with Dataclasses](https://fermiparadox.gitbook.io/fermiparadox/oswe-poc-skeleton/03-context-management-with-dataclasses)

In the next article, we’ll introduce a structured context object to carry configuration and runtime state through the exploit cleanly, without passing argument objects through every function.


# 03 - Context Management with Dataclasses

In the [last article](https://fermiparadox.gitbook.io/fermiparadox/oswe-poc-skeleton/02-argument-parsing-for-oswe-pocs-argparse-vs-dotenv), I described how using Python's argparse functionality allowed easy configuration of different command line arguments. OSWE Challenge Labs usually have a debug and a victim machine. Each VM has a different IP address on their network. While testing the exploit chain, depending on the student, one might move between the debug and victim vm...or not. *argparse* easily allows the setting of each machines unique configuration without having to edit the PoC code. Parameters can be passed from the command line and stored internally. For example, the target could have input arguments like:

```python
parser.add_argument("--target-ip", type=str, required=True, help="Input file path")
    parser.add_argument("--target-port", type=int, default=80, help="Input file path")
```

After the arguments are read in, the arguments could be initialized in the following manner:

```python
args = parse_args()

target_ip = args.target_ip
target_port = args.target_port
```

As the number of required arguments grows, extracting and passing individual values quickly becomes repetitive and error-prone. Once I considered how many inputs the exploit required, I needed a way to pass this data cleanly between functions.

Before I explain what I eventually ended up doing to consolidate the collection of arguments, I'd like to briefly describe a method for organizing them. Given the course and lab objectives, some argument options seemed fairly transparent and connected (eg target vs attacker). As I was refining the structure throughout the labs, I learned that one can group arguments with argparse. Grouping the arguments is really only for cosmetic purposes. Running the code with the `--help` option, when the arguments are grouped, will display the groupings together (see below).

I decided to group arguments using target, attacker, exploit, identity, and optional options. To group options together, decide on a variable name for the grouping and then use `.add_argument_group("descripton")`. A basic groupings might look like:

```python
def parse_args():
    parser = argparse.ArgumentParser(description="OSWE Application Exploit.")

    # --- Target options ---
    target_group = parser.add_argument_group("Target options")
    target_group.add_argument(
        "--target-ip", type=str, required=True, help="Target server IP address"
    )
    target_group.add_argument(
        "--target-port",
        type=int,
        default=80,
        help="Target web frontend port (default: 80)",
    )
```

When using `--help` to find the options, grouped options are shown together.

```bash
❯ uv run poc.py --help
usage: poc.py [-h] --target-ip TARGET_IP [--target-port TARGET_PORT] [--target-api-port TARGET_API_PORT] [--listening-ip LISTENING_IP]
               [--listening-port LISTENING_PORT] [--payload-port PAYLOAD_PORT] [--delay DELAY] [--user-file USER_FILE]
               [--save-identity SAVE_IDENTITY] [--register] [--complexity {low,medium,high}] [--include-address] [--include-phone]
               [--charset {alpha,alnum,hex,ascii,symbols,base64,numeric}] [--proxy PROXY]

OSWE Application Exploit.

options:
  -h, --help            show this help message and exit

Target options:
  --target-ip TARGET_IP
                        Target server IP address
  --target-port TARGET_PORT
                        Target web frontend port (default: 80)
  --target-api-port TARGET_API_PORT
                        Target API port (default: 5000)

Attacker options:
  --listening-ip LISTENING_IP
                        IP to listen on for reverse shell (default: 127.0.0.1)
  --listening-port LISTENING_PORT
                        Port to listen for reverse shell (default: 9001)
  --payload-port PAYLOAD_PORT
                        Port to listen for xss or other payload (default: 9999)

Exploit options:
  --delay DELAY         Response delay in seconds for timing inference (default: 3)

Identity options:
  --user-file USER_FILE
                        Path to existing exploit user JSON (default: user.json)
  --save-identity SAVE_IDENTITY
                        Path to save newly generated identity JSON
  --register            Whether the user has already been registered
  --complexity {low,medium,high}
                        Password complexity
  --include-address     Include street address
  --include-phone       Include phone number

Optional options:
  --charset {alpha,alnum,hex,ascii,symbols,base64,numeric}
                        Charset to use for blind SQLi password extraction.
  --proxy PROXY         Turn on Burp Suite proxy for debugging.
 
```

The grouping itself does not change behavior, but it significantly improves readability once the number of options grows.

Before introducing a context object, most exploit scripts grow organically: variables are defined near main(), then slowly threaded through multiple function calls. As the exploit evolves, function signatures grow longer, ordering becomes brittle, and small changes require touching many call sites.

```
Before:
    create_account(target_ip, target_port, user, proxy, timeout)
    sign_in(target_ip, target_port, user, proxy)
    extract_flag(target_ip, target_port, session)

After:
    create_account(ctx, user)
    sign_in(ctx, user)
    extract_flag(ctx)
```

Dataclasses come with `__init__` baked-in and the data structure can be printed as a dictionary without having to add a `__repr__` method. We can use the `@dataclass` decorator to initialize the class. Notice the use of `slots=True` on the dataclass. This enforces a fixed schema, preventing accidental attribute creation due to typos and making the structure of the context explicit. While slots can provide performance benefits in some scenarios, its primary purpose here is correctness and discipline rather than speed.

I named the class `ExploitContext`, but this was just a personal choice. What we are building with `ExploitContext` is a structured object which will contain the state required to execute most of the exploit. I say most here, because I ended up having a different structure for simulating and registering user accounts. By having a singular structure, important data can be passed through layers of functions without having to have a multitude of function arguments and when layering function calls, the passing of said information is simplified.

ExploitContext is intentionally **not** a replacement for HTTP sessions, request state, or per-request variables. Transport concerns (cookies, headers, retries) live in requests or httpx sessions. The context exists to describe the environment the exploit operates in, not every transient detail of execution.

At a high level, `ExploitContext` is intended to hold:

* Target-specific configuration (IP addresses, ports, protocol)
* Attacker-side configuration (listener and payload delivery ports)
* Stable runtime identifiers and configuration needed across exploit steps
* Metadata useful for auditing or reporting (PoC ID, vulnerability name)

Below is an example of how to start constructing the class and initializing it.

```python
# additional imports go here
from dataclasses import dataclass

# any global variables, etc... go here

@dataclass(slots=True)
class ExploitContext:
    target_ip: str
    target_port: int
    target_api_port: int
    attacker_ip: str
    attacker_port: int
    payload_port: int
    protocol: str = "http"
    
# more code
# def main()
# more code

    ctx = ExploitContext(
        target_ip=args.target_ip,
        target_port=args.target_port,
        attacker_ip=args.listening_ip,
        attacker_port=args.listening_port,
        protocol="http"
    )    
    
# more code
```

* `target_port`: victim's web front end
* `target_api_port`: victim's API service (when present)
* `attacker_port`: interactive callbacks (e.g., reverse shell)
* `payload_port`: hosted payload delivery

Once the context exists, exploit functions can accept a single argument (`ctx`), instead of a long list of parameters. This makes function signatures stable even as the exploit grows and allows new fields to be added to the context without additional rewriting.

At this point, we have a single object that represents everything the exploit needs to know about its environment and current state. Configuration, runtime values, and metadata are no longer scattered across the codebase.

Rather than passing configuration values through every function, the context moves unchanged through the exploit, accumulating state as needed.

```
┌───────────────┐
│ CLI / argparse│
└───────┬───────┘
        │
        │ parse_args()
        ▼
┌────────────────────┐
│  ExploitContext    │
│  (ctx)             │
│────────────────────│
│ target_ip          │
│ target_port        │
│ attacker_ip        │
│ payload_port       │
│ protocol           │
│ metadata / state   │
└─────────┬──────────┘
          │
          │ passed as a single argument
          ▼
┌────────────────────┐
│ create_account(ctx)│
└────────────────────┘
          │
          ▼
┌────────────────────┐
│ sign_in(ctx)       │
└────────────────────┘
          │
          ▼
┌────────────────────┐
│ exploit_step(ctx)  │
└────────────────────┘
```

What we *do not* yet have is a clear model for how exploit stages relate to one another. In practice, most PoCs grow into long `main()` functions with deeply intertwined control flow, retries, and conditional logic. In the next article, we’ll address that problem directly by introducing explicit stage and control-flow management, using the context as the shared state between stages.

This article focuses on *what the context is*, not *everything it can do*. Helpers for URL construction, logging, and orchestration are intentionally deferred to later articles.

**An example of how `ExploitContext` evolves**

```python
# imports and code
from dataclasses import dataclass, field

# more imports anc code possible here

@dataclass(slots=True)
class ExploitContext:
    target_ip: str
    target_port: int
    target_api_port: int
    attacker_ip: str
    attacker_port: int
    payload_port: int
    protocol: str = "http"

    # Runtime-only fields
    output_path: Path = field(
        default_factory=lambda: Path("exploit_context.json"), repr=False
    )

    # --- Factory constructor from argparse -

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "ExploitContext":
        """Build an ExploitContext from CLI arguments."""
        return cls(
            target_ip=args.target_ip,
            target_port=args.target_port,  # maps to --target-port
            target_api_port=args.target_api_port,  # maps to --target-api-port
            attacker_ip=args.listening_ip,  # maps to --listening-ip
            attacker_port=args.listening_port,  # maps to --listening-port
            payload_port=args.payload_port # maps to --payload-port
        )

# Code for the PoC

def main():
    args = parse_args()
    
    # more initialization code might be here
    
    ctx = ExploitContext.from_args(args)

```

What I’ve done here is make the construction of `ExploitContext` simpler by reducing the amount of boilerplate code required during initialization. Instead of deconstructing parsed arguments inside `main()`, the from\_args(args) classmethod accepts the full `argparse.Namespace` and is responsible for mapping CLI options directly into the context. Placing this mapping logic inside `ExploitContext` keeps construction concerns close to the data they produce, reduces duplication, and makes future refactors safer when CLI options change.

Because from\_args is defined as a `@classmethod`, it receives the class itself (`cls`) rather than an instance, allowing it to act as an alternate constructor. The `argparse.Namespace` passed into `from_args` contains all parsed command-line options, which are selectively extracted and used to build the context in a single, centralized place. Finally, `output_path` is initialized at runtime to define where the context may be serialized. This file can be used for auditing, debugging, or state restoration if desired, but its use is optional and left entirely to the programmer.

This structure is not a template you must copy verbatim. The goal is to demonstrate a pattern that scales as exploits grow, not to prescribe a fixed schema.

In the next article, we’ll focus on structuring exploit execution itself by introducing explicit stages and control flow that operate over the shared context so the PoC is well-organized and maintainable.


---

Based on the provided file, here is a detailed explanation of how to build a reusable OSWE (Offensive Security Web Expert) Proof of Concept (PoC) skeleton. This guide breaks down the process into three distinct phases: **Project Setup**, **Argument Parsing**, and **Context Management**.

---

### Phase 1: Project Setup & Structure
**Goal:** Create a reproducible, organized environment that separates code, logs, and evidence (screenshots/archives).

The author emphasizes using **`uv`** (a modern Python package manager) instead of standard pip/venv for speed and reproducibility.

#### 1. Directory Initialization
Instead of a messy folder with random scripts, the project follows a strict hierarchy.

**Command to create project:**
```bash
# Initialize a bare project named 'authrise' without a readme, using git
uv init --bare --no-readme --vcs git authrise
```

**The Resulting Directory Structure:**
The skeleton includes specific folders for the exam requirements (proofs, logs, screenshots).

```text
authrise/
├── .git/               # Version control
├── .gitignore          # Ignores __pycache__, .env, .venv, etc.
├── pyproject.toml      # Dependency management (handled by uv)
├── poc.py              # The main entry point (your exploit code)
├── Notes.md            # For documenting findings/SQL queries/credentials
├── Archives/           # Saved HTTP responses, tokens, or data dumps
├── Logs/               # Runtime logs for debugging
└── Screenshots/        # Exam-safe references (since copying files is restricted)
```

#### 2. The `.gitignore`
To keep the project clean, the author suggests a specific `.gitignore` configuration to exclude virtual environments and compiled python files:

```text
__pycache__/
*.py[oc]
.venv
.env
.vscode/
```

---

### Phase 2: Argument Parsing (The CLI)
**Goal:** Eliminate hardcoded values (IPs, ports) and create a user-friendly Command Line Interface (CLI) with help menus.

While `.env` files are an option, the author prefers **`argparse`** because it provides a built-in `--help` flag, which is crucial when returning to a script after a break or during the pressure of an exam.

#### The "Grouping" Strategy
Instead of a long list of random flags, the author groups arguments logically using `parser.add_argument_group`.

**Example Code (`poc.py`):**

```python
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="OSWE Application Exploit.")

    # Group 1: Target Options (Where are we attacking?)
    target_group = parser.add_argument_group("Target options")
    target_group.add_argument("--target-ip", required=True, help="Target server IP")
    target_group.add_argument("--target-port", type=int, default=80, help="Web port")
    target_group.add_argument("--target-api-port", type=int, default=5000, help="API port")

    # Group 2: Attacker Options (Where do we catch shells?)
    attacker_group = parser.add_argument_group("Attacker options")
    attacker_group.add_argument("--listening-ip", default="127.0.0.1", help="LHOST")
    attacker_group.add_argument("--listening-port", type=int, default=9001, help="LPORT")

    # Group 3: Identity/Exploit Options (User creation, passwords, etc.)
    identity_group = parser.add_argument_group("Identity options")
    identity_group.add_argument("--register", action="store_true", help="Register new user?")
    identity_group.add_argument("--complexity", choices=["low", "high"], help="Password complexity")

    return parser.parse_args()
```

**The Benefit:**
When you run `uv run poc.py --help`, the output is categorized, making it easy to read:

```text
Target options:
  --target-ip TARGET_IP    Target server IP address
  --target-port TARGET_PORT ...

Attacker options:
  --listening-ip LISTENING_IP ...
```

---

### Phase 3: Context Management (Dataclasses)
**Goal:** Stop passing 10 different arguments to every function.

As the exploit grows, functions like `login()` or `upload_shell()` would need access to IPs, ports, and configurations. Passing these individually is messy. The solution is a **Context Object**.

#### 1. The `ExploitContext` Class
The author uses Python's `@dataclass` with `slots=True`. This creates a rigid, memory-efficient object to hold the "State" of the exploit.

```python
from dataclasses import dataclass, field
import argparse
from pathlib import Path

@dataclass(slots=True)
class ExploitContext:
    # Core connection info
    target_ip: str
    target_port: int
    target_api_port: int
    
    # Attacker info
    attacker_ip: str
    attacker_port: int
    payload_port: int
    
    # Default protocol
    protocol: str = "http"

    # Runtime field (not passed via CLI, but calculated)
    output_path: Path = field(
        default_factory=lambda: Path("exploit_context.json"), repr=False
    )

    # FACTORY METHOD: Bridges argparse and this class
    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "ExploitContext":
        return cls(
            target_ip=args.target_ip,
            target_port=args.target_port,
            target_api_port=args.target_api_port,
            attacker_ip=args.listening_ip,
            attacker_port=args.listening_port,
            payload_port=args.payload_port
        )
```

#### 2. Why use `from_args`?
This class method encapsulates the logic of converting CLI arguments into the Context object. It keeps your `main()` function clean.

---

### Putting It All Together: The Complete Skeleton

Here is how the `main()` function looks when combining Phase 2 (Argparse) and Phase 3 (Context).

**The "Before" (Messy):**
```python
# Without Context, function signatures are huge and brittle
def login(target_ip, target_port, protocol, username, password):
    ...

def main():
    args = parse_args()
    login(args.target_ip, args.target_port, "http", "admin", "pass")
```

**The "After" (Clean & Reusable):**
```python
# With Context, you pass ONE object
def login(ctx: ExploitContext, username, password):
    url = f"{ctx.protocol}://{ctx.target_ip}:{ctx.target_port}/login"
    print(f"Logging into {url}...")

def main():
    # 1. Parse CLI arguments
    args = parse_args()
    
    # 2. Hydrate the Context object
    ctx = ExploitContext.from_args(args)
    
    # 3. Pass context to exploit stages
    print(f"Starting attack against {ctx.target_ip}...")
    login(ctx, "admin", "secret")

if __name__ == "__main__":
    main()
```

### Summary of Benefits
1.  **Auditability:** You have dedicated folders (`Logs`, `Archives`) for exam evidence.
2.  **Flexibility:** You can switch between Debug and Victim machines instantly using CLI flags (`--target-ip`).
3.  **Maintainability:** Adding a new global setting (like a proxy) only requires updating the `ExploitContext` definition, not every single function signature in your script.