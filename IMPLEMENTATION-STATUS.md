# OSWE-Prep Repository Expansion - Implementation Status

**Date**: 2026-07-11 (study system pack: exam ops, enriched classic cases, methodology guides, drills)
**Status**: Study-aid expansion complete (docs/practice systems). Earlier Phase 1 PoC foundation still applies below.

## 2026-07-11 study pack (summary)

| Area | Deliverables |
|------|----------------|
| Exam ops | `Exam-Day-Runbook.md`, `Progress-Tracker.md`, `Report-Snippet-Templates.md`, `Speed-Drills.md` |
| Classic cases enriched | ATutor type juggling + auth/RCE, Atmail, ManageEngine, DNN cookie |
| PoC Notes expanded | Node deserial, .NET ViewState, XXE lab manuals |
| Guides | Type juggling, XSS→RCE, Postgres SQLi→RCE, Blind SQLi, LFI, sinks cheatsheet, chain trees; .NET guide expanded + renamed `guides/DotNet-Deserialization-Guide.md` |
| Practice systems | `drills/Cold-Start-Drills.md`, `study-log/`, `Lab-Setup-Matrix.md` |
| Indexes | README Start Here + methodology table; Roadmap weeks linked; AGENTS.md |

---

**Prior status note**: Phase 1 Complete (Foundation + 2 Priority PoCs) - Remaining work documented below

---

## ✅ COMPLETED WORK (100% Functional & Tested)

### 1. Foundation Modules ✅

**File**: `poc-examples/advanced-skeleton/modules/payloads.py` (NEW - 200+ lines)
- Reverse shells: Bash, PowerShell, Python, Perl, PHP, Ruby
- Webshells: PHP (simple, GET, POST, obfuscated), JSP, ASPX, ASP
- Encoding utilities: Base64, URL, Hex, Double-URL encoding
- SQLi payloads: MySQL/PostgreSQL/MSSQL sleep patterns
- Deserialization helpers: Java magic bytes, PHP serialize
- XXE templates: File read, OOB DTD generation
- SSTI payloads: Jinja2 probes and RCE
- Command injection separators and helpers

**File**: `poc-examples/advanced-skeleton/modules/sqli.py` (ENHANCED - +150 lines)
- Extended MSSQLDialect class with comprehensive RCE methods
- Methods: `enable_xp_cmdshell()`, `disable_xp_cmdshell()`, `execute_command()`
- Alternative RCE: `enable_ole_automation()`, `execute_command_ole()`
- File operations: `write_file()`, `read_file()`
- Database enumeration: `list_databases()`, `list_tables()`, `list_columns()`
- Privilege checking: `is_sysadmin()`, `get_current_user()`
- Utility methods: `get_version()`, `stacked_query_separator()`

---

### 2. Java Deserialization - Commons Collections ✅ (COMPLETE EXAMPLE)

**Directory**: `poc-examples/java-deserialization-commons/`

**Files Created**:
- ✅ `poc.py` (454 lines) - Production-quality PoC
  - ysoserial integration via subprocess
  - Multiple delivery methods (cookie, POST, header, TCP)
  - Multiple command types (ping, sleep, reverse_shell)
  - Gadget chain selection (CommonsCollections1-10, Spring, ROME, etc.)
  - Full ExploitContext pattern with dataclass
  - Stage-based architecture (recon, generate, exploit, verify)
  - Comprehensive error handling and logging

- ✅ `Notes.md` (400+ lines) - Complete lab manual
  - Vulnerability summary and attack chain
  - Lab setup: Jenkins 2.46.1 Docker, JBoss, custom Java app
  - ysoserial download and installation
  - Manual exploitation walkthrough (all stages)
  - Payload generation for different OS (Linux/Windows)
  - Multiple verification methods (ping, DNS, HTTP, sleep)
  - Bypass techniques (encoding, alternate gadgets)
  - Debugging section with common issues
  - Mitigation strategies (code fixes, server config)
  - OSWE exam notes (time management, pre-exam checklist)

- ✅ `payloads/` directory created for ysoserial.jar storage

**Case Study**: `notes/JAVA-DESERIALIZATION-COMMONS-COLLECTIONS.md` (100+ lines)
- Environment: Jenkins 2.46.1 Docker setup
- Recon: Entry points (CLI port 50000, HTTP 8080)
- Vulnerable code patterns with explanations
- Complete exploitation chain (6 steps)
- Evidence locations (screenshots, logs, artifacts)
- Root cause analysis with gadget chain breakdown
- Recommended fixes (immediate patches + secure code)

**Methodology Guide**: `guides/Java-Deserialization-Methodology.md` (280+ lines)
- Part 1: Identifying Deserialization (white-box and black-box)
- Part 2: Understanding Gadget Chains (anatomy, selection)
- Part 3: ysoserial Usage (installation, payload generation)
- Part 4: Exploitation Techniques (delivery methods)
- Part 5: OSWE Exam Strategy (workflow, time management)
- Part 6: Common Vulnerable Libraries (version matrix)
- Part 7: Bypasses and Advanced Techniques
- Part 8: Quick Reference (checklists, common mistakes)

---

### 3. MSSQL SQLi to xp_cmdshell ✅ (COMPLETE EXAMPLE)

**Directory**: `poc-examples/mssql-sqli-xp-cmdshell/`

**Files Created**:
- ✅ `poc.py` (500+ lines) - Production-quality PoC
  - Integration with enhanced sqli.py module
  - Time-based SQLi detection (WAITFOR DELAY)
  - Sysadmin privilege checking
  - Stacked queries for xp_cmdshell enablement
  - Multiple command types (ping, whoami, reverse_shell, webshell)
  - PowerShell reverse shell with base64 encoding
  - ASPX webshell writing capability
  - Full ExploitContext pattern
  - 5-stage architecture (recon, privilege check, enable, exploit, verify)

- ✅ `Notes.md` (350+ lines) - Complete lab manual
  - Vulnerability summary (SQLi → xp_cmdshell → RCE)
  - Vulnerable ASP.NET code examples
  - Lab setup: Windows Server + MSSQL, Docker MSSQL
  - Manual exploitation walkthrough
  - xp_cmdshell overview and enable sequence
  - Command execution examples (ping, PowerShell, webshell)
  - Bypass techniques (WAF evasion, OLE Automation)
  - Debugging common issues
  - Secure code examples (parameterized queries)
  - OSWE exam notes

**Case Study**: `notes/MSSQL-SQLI-XP-CMDSHELL.md` (90 lines)
- Environment: Windows Server 2019 + MSSQL 2019 Express
- Vulnerable ASP.NET MVC code (ProductsController.cs)
- Full exploitation chain
- Root cause analysis
- Secure code fix with parameterized queries

---

### 4. README.md Updates ✅

**File**: `README.md` (UPDATED)

**New Sections Added**:
1. **Advanced Exploitation Techniques**
   - Deserialization Vulnerabilities table (Java, .NET, PHP, Node.js)
   - XXE (XML External Entity) table
   - Template Injection table (SSTI)
   - Advanced SQL Injection table (MSSQL xp_cmdshell, Second-Order)

2. **Methodology Guides**
   - 7 comprehensive guides linked
   - Java Deserialization, .NET, PHP, XXE, SSTI, Advanced SQLi, Code Review

All links properly formatted with relative paths to poc-examples/ and guides/ directories.

---

## 📋 REMAINING WORK (Templates & Guidance Provided)

### Phase 2: XXE File Read/SSRF

**Status**: Directory created, templates ready
**Directory**: `poc-examples/xxe-file-read-ssrf/`
**What's needed**:

1. **poc.py** (~450 lines)
   - Pattern: Follow Java Deserialization example structure
   - Key features:
     - Generate XXE payloads for file read (file:// protocol)
     - Generate external DTD for out-of-band exfiltration
     - Integrate with `payload_server.py` module for callback handling
     - Test for blind XXE via error messages
     - Support multiple formats (XML, SVG, DOCX)
   - Stages:
     1. Recon: Identify XML parsing endpoints
     2. Generate: Create XXE and DTD payloads
     3. Exploit: Deliver payload (POST, file upload)
     4. Verify: Check callback server or error messages

2. **Notes.md** (~400 lines)
   - Lab setup: Docker container with vulnerable Java/PHP XML parser
   - XXE types: In-band file read, OOB exfiltration, blind XXE
   - DTD construction examples for different scenarios
   - Protocol handlers: file://, http://, ftp://, php://
   - XXE in different formats (DOCX, XLSX, SVG)
   - OSWE exam tips

3. **Case study**: `notes/XXE-FILE-READ-SSRF.md`
   - Environment details
   - Vulnerable code (XMLReader, DocumentBuilder patterns)
   - Exploitation chain

4. **Methodology guide**: `guides/XXE-Attack-Vectors.md`
   - Reference payloads.py XXE templates (already created!)
   - Detection methods (white-box and black-box)
   - DTD construction guide
   - Out-of-band techniques
   - Code review patterns

**Quick Start Template** (for poc.py):
```python
# Use existing pattern from java-deserialization-commons/poc.py
# Import from modules/payloads.py:
#   - xxe_file_read()
#   - xxe_oob_dtd()
#   - xxe_oob_dtd_content()
# Import from modules/payload_server.py for callback handling
```

---

### Phase 3: .NET ViewState Deserialization

**Status**: Directory created
**Directory**: `poc-examples/dotnet-viewstate-deserialization/`

**What's needed**:
1. **poc.py** (~450 lines)
   - ViewState decoding (base64 → binary)
   - Machine key discovery/brute-forcing
   - ysoserial.net integration (similar to ysoserial for Java)
   - ObjectDataProvider gadget chain
   - Delivery via __VIEWSTATE parameter

2. **Notes.md** (~400 lines)
   - Lab setup: IIS + DotNetNuke 9.1.1
   - ViewState structure explanation
   - ysoserial.net usage
   - Machine key exploitation

3. **Case study**: `notes/DOTNET-VIEWSTATE-DESERIALIZATION.md`
4. **Methodology guide**: `guides/DotNet-Deserialization-Guide.md`
   - ViewState decoding process
   - ysoserial.net gadget chains
   - Code review patterns (BinaryFormatter, ObjectStateFormatter)

---

### Phase 4: PHP Object Injection

**Status**: Directory created
**Directory**: `poc-examples/php-object-injection/`

**What's needed**:
1. **poc.py** (~400 lines)
   - PHP magic method exploitation (__wakeup, __destruct, __toString)
   - POP chain construction
   - Serialized object generation
   - PHAR deserialization vectors
   - Reference `payloads.py php_serialize_simple()`

2. **Notes.md** (~350 lines)
   - Lab setup: LAMP stack + WordPress vulnerable plugin
   - Magic methods overview
   - POP chain identification in source code
   - PHAR wrapper exploitation

3. **Case study**: `notes/PHP-OBJECT-INJECTION.md`
4. **Methodology guide**: `guides/PHP-Deserialization-Patterns.md`
   - Magic methods deep dive
   - POP chain construction methodology
   - Common vulnerable libraries (Symfony, Monolog)

---

### Phase 5: Node.js Deserialization

**Status**: Directory created
**Directory**: `poc-examples/nodejs-deserialization/`

**What's needed**:
1. **poc.py** (~420 lines)
   - node-serialize exploitation
   - IIFE (Immediately Invoked Function Expression) payloads
   - Cookie-based deserialization
   - Session token manipulation

2. **Notes.md** (~350 lines)
   - Lab setup: Docker + Express.js with node-serialize
   - Payload construction: `_$$ND_FUNC$$_` wrapper
   - Verification via reverse shell or callback

3. **Case study**: `notes/NODEJS-DESERIALIZATION.md`

---

### Phase 6: SSTI Jinja2

**Status**: Directory created
**Directory**: `poc-examples/ssti-jinja2-flask/`

**What's needed**:
1. **poc.py** (~420 lines)
   - Template engine fingerprinting
   - Jinja2 sandbox escape techniques
   - MRO (Method Resolution Order) exploitation
   - Polyglot payloads for multiple engines
   - Reference `payloads.py ssti_*()` functions (already created!)

2. **Notes.md** (~380 lines)
   - Lab setup: Docker + Flask with Jinja2
   - Manual SSTI testing ({{7*7}}, {{config}})
   - Sandbox escape progression
   - Different template engines (Jinja2, Twig, Freemarker)

3. **Case study**: `notes/SSTI-JINJA2-FLASK.md`
4. **Methodology guide**: `guides/SSTI-Exploitation-Guide.md`
   - Template engine fingerprinting matrix
   - Engine-specific payloads
   - Code review patterns (render_template_string)

---

### Phase 7: Second-Order SQLi

**Status**: Directory created
**Directory**: `poc-examples/second-order-sqli/`

**What's needed**:
1. **poc.py** (~480 lines)
   - Two-stage injection (registration → admin panel)
   - Payload storage and trigger identification
   - Integration with `modules/sqli.py` BlindSQLi class
   - Time optimization (binary search)

2. **Notes.md** (~400 lines)
   - Lab setup: Custom PHP app (user registration + admin panel)
   - Second-order SQLi identification in code
   - Payload storage locations (database fields)
   - Trigger points (admin search, export, reports)

3. **Case study**: `notes/SECOND-ORDER-SQLI.md`

---

### Remaining Methodology Guides

**Status**: Guides partially created (Java complete, 6 remaining)
**Directory**: `guides/`

1. **.NET-Deserialization-Guide.md** (~260 lines)
   - ViewState structure and analysis
   - ysoserial.net comprehensive usage
   - Machine key exploitation techniques
   - Code review: BinaryFormatter, ObjectStateFormatter, JavaScriptSerializer

2. **PHP-Deserialization-Patterns.md** (~240 lines)
   - Magic methods: __wakeup, __destruct, __toString, __call
   - POP chain construction step-by-step
   - PHAR deserialization (phar:// wrapper)
   - Common vulnerable libraries

3. **XXE-Attack-Vectors.md** (~280 lines)
   - XXE types: In-band, out-of-band, blind, error-based
   - DTD construction for different scenarios
   - Protocol handlers: file, http, ftp, expect, php
   - XXE in different file formats (DOCX, XLSX, SVG, PDF)

4. **SSTI-Exploitation-Guide.md** (~260 lines)
   - Template engine fingerprinting techniques
   - Jinja2 sandbox escape (MRO, config object)
   - Twig/Freemarker/Velocity exploitation
   - Polyglot payloads
   - Code review patterns

5. **Advanced-SQLi-Techniques.md** (~300 lines)
   - Second-order SQLi methodology
   - Database-specific RCE:
     - MSSQL: xp_cmdshell, OLE Automation, sp_OACreate
     - PostgreSQL: COPY, lo_export, CVE-2019-9193
     - MySQL: LOAD_FILE, INTO OUTFILE/DUMPFILE
   - Out-of-band exfiltration (DNS, HTTP)
   - Time optimization: Binary search vs linear
   - WAF bypass techniques

6. **Code-Review-Checklists.md** (~220 lines)
   - Dangerous functions by language:
     - Java: ObjectInputStream, XMLDecoder, XStream
     - .NET: BinaryFormatter, ObjectStateFormatter
     - PHP: unserialize, phar://, eval
     - Node.js: node-serialize, serialize-to-js
     - Python: pickle, PyYAML
   - Source/sink identification methodology
   - Data flow analysis patterns
   - Quick wins for OSWE exam (30-minute check)

---

## 🎯 IMPLEMENTATION ROADMAP

### For Completing Remaining PoCs

**Each PoC should follow this pattern** (established by Java Deserialization example):

**poc.py Structure** (400-500 lines):
```python
#!/usr/bin/env python3
"""
[Vulnerability Name] PoC
CVE: [CVE-ID or N/A]
Target: [Application Type]
Vulnerability: [Brief description]

Reference:
- [Link 1]
- [Link 2]

Exploit Flow:
1. [Step 1]
2. [Step 2]
...
"""

import argparse
import requests
import sys
from dataclasses import dataclass, field
from typing import Optional
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Import from modules as needed
# from modules.payloads import *
# from modules.payload_server import PayloadServer

@dataclass(slots=True)
class ExploitContext:
    """[App] exploit configuration and state."""
    target_ip: str
    target_port: int
    protocol: str = "http"
    # ... more fields

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "ExploitContext":
        """Build ExploitContext from CLI arguments."""
        return cls(...)

    def get_base_url(self) -> str:
        return f"{self.protocol}://{self.target_ip}:{self.target_port}"

    def get_proxies(self) -> Optional[dict]:
        if self.proxy:
            return {"http": self.proxy, "https": self.proxy}
        return None

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    # Follow grouping pattern: Target, Attacker, Exploit, Optional
    pass

def stage_recon(ctx: ExploitContext) -> bool:
    """Stage 1: Reconnaissance."""
    pass

def stage_exploit(ctx: ExploitContext) -> bool:
    """Stage 2: Exploitation."""
    pass

def stage_verify(ctx: ExploitContext) -> bool:
    """Stage 3: Verification."""
    pass

def main():
    """Main execution."""
    # Stage orchestration with error handling
    pass

if __name__ == "__main__":
    main()
```

**Notes.md Structure** (350-450 lines):
```markdown
# [Vulnerability Name] PoC Notes

## Vulnerability Summary
- Target, CVE, Type, Impact

## Vulnerability Details
- Attack Chain
- Root Cause
- Vulnerable Code Pattern

## Lab Setup
- Prerequisites
- Option 1: [Primary setup]
- Option 2: [Alternative setup]
- Verification Setup

## Exploit Chain
- Stage 1: Manual exploitation
- Stage 2: Manual exploitation
- ...

## Testing Commands
- Basic PoC usage examples
- Manual verification commands

## Bypass Techniques
- WAF bypasses
- Alternative techniques

## Debugging
- Common failure points
- Diagnostic commands

## Mitigation
- Developer fixes (secure code)
- Server configuration

## OSWE Exam Notes
- Key takeaways
- Time management
- Pre-exam checklist
- Quick reference commands
```

---

## 📊 SUMMARY STATISTICS

**Content Created**:
- ✅ 2 Complete PoC Examples (Java Deserialization, MSSQL SQLi)
- ✅ 2 Complete poc.py files (954 lines total)
- ✅ 2 Complete Notes.md lab manuals (750+ lines total)
- ✅ 2 Case studies (190 lines total)
- ✅ 1 Complete methodology guide (Java - 280 lines)
- ✅ 2 Enhanced modules (payloads.py, sqli.py - 350+ lines)
- ✅ README.md fully updated with all sections

**Total Lines of Code & Documentation**: ~2,500+ lines

**Remaining Work**:
- 6 PoC examples (following established patterns)
- 6 methodology guides (templates provided above)
- All directory structures created
- All module dependencies ready

---

## 💡 KEY DESIGN PATTERNS ESTABLISHED

### 1. ExploitContext Pattern
```python
@dataclass(slots=True)
class ExploitContext:
    # Target configuration
    target_ip: str
    target_port: int
    protocol: str = "http"

    # Attacker configuration
    attacker_ip: str
    attacker_port: int

    # Exploit configuration
    proxy: Optional[str] = None

    # Runtime state
    session: requests.Session = field(default_factory=requests.Session, repr=False)

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "ExploitContext":
        return cls(...)
```

### 2. Argument Parsing Groups
- Target Configuration
- Attacker Configuration
- Exploit Configuration
- Optional

### 3. Stage-Based Architecture
- `stage_recon()` - Connectivity and vulnerability detection
- `stage_exploit()` - Main exploitation logic
- `stage_verify()` - RCE confirmation

### 4. Module Integration
- Import from `modules/payloads.py` for common payloads
- Import from `modules/sqli.py` for SQL injection
- Import from `modules/payload_server.py` for callback handling
- Import from `modules/logger.py` for structured logging (optional)

---

## 🚀 QUICK START FOR CONTINUING

### To complete an example (e.g., XXE):

1. **Copy template from Java Deserialization**:
   ```bash
   cp poc-examples/java-deserialization-commons/poc.py poc-examples/xxe-file-read-ssrf/poc.py
   ```

2. **Modify for XXE specifics**:
   - Change vulnerability description in header
   - Update ExploitContext fields (add `dtd_server`, `target_file`, etc.)
   - Implement `generate_xxe_payload()` function
   - Implement `generate_dtd()` function
   - Update stages for XXE flow
   - Import from `modules/payloads.py` (xxe_* functions already exist!)

3. **Create Notes.md**:
   - Follow MSSQL example structure
   - Add XXE-specific lab setup
   - Document DTD construction
   - Add verification methods (callback server logs)

4. **Test locally**:
   ```bash
   python3 poc.py localhost 8080 10.10.14.5 4444
   ```

---

## 📚 REFERENCES FOR REMAINING WORK

### Essential Reading
- Java Deserialization example: `poc-examples/java-deserialization-commons/`
- MSSQL SQLi example: `poc-examples/mssql-sqli-xp-cmdshell/`
- Payload library: `poc-examples/advanced-skeleton/modules/payloads.py`
- Enhanced SQLi module: `poc-examples/advanced-skeleton/modules/sqli.py`

### Existing Resources in Repository
- `Building a Reusable OSWE PoC Skeleton.md` - Foundational design philosophy
- `Exploit Writing for OSWE.md` - requests library patterns
- `OSWE-PoC-Skeleton-Guide.md` - Template-focused guide
- `COMPLETE-POC-GUIDE.md` - Master navigation document

---

## ✨ QUALITY STANDARDS MAINTAINED

All completed work follows these standards:
- ✅ Type hints on all functions
- ✅ Comprehensive docstrings
- ✅ ExploitContext pattern from atmail-xss-rce
- ✅ Stage-based architecture
- ✅ Color-coded output ([+] success, [-] error, [*] info, [!] warning)
- ✅ Proxy support for debugging
- ✅ Proper error handling
- ✅ 400-500 lines per PoC (within established range)
- ✅ Complete lab setup instructions in Notes.md
- ✅ OSWE exam tips in all documentation

---

## 🎓 EXAM-READY FEATURES

**Time Optimizations**:
- Binary search in sqli.py (7 requests/char vs 32 linear)
- Async SQLi extraction capability
- Pre-generated payload templates in payloads.py
- Modular approach allows quick adaptation during exam

**Verification Methods**:
- Ping callbacks (fastest to verify)
- DNS callbacks (out-of-band)
- HTTP callbacks (payload_server.py)
- Time-based (sleep detection)
- Reverse shells (interactive access)

**Debugging Support**:
- Proxy support (Burp Suite integration)
- Verbose logging with progress indicators
- Clear error messages
- Manual verification prompts

---

## 📝 CONCLUSION

**Phase 1 Complete**: Foundation laid with 2 complete, production-quality examples that establish all patterns, conventions, and quality standards.

**Remaining Work**: 6 more PoC examples + 6 methodology guides, all following established patterns. Directory structures created, module dependencies ready, templates provided.

**Estimated Effort to Complete**:
- Per PoC: 6-8 hours (including testing)
- Per Guide: 2-3 hours
- **Total**: 50-70 hours of focused work

**Next Steps**: Follow this document's templates and patterns to complete remaining examples. Each new PoC becomes faster as familiarity with patterns increases.

---

## ✨ 2026 Enrichment Pass (Study-Focused Improvements)

**Date**: Current session

**Scope**: Focused on making the repo more effective as a *study system* for OSWE rather than just a collection of PoCs.

### Additions & Major Improvements
- **New OSWE-Study-Roadmap.md** (comprehensive 8-week plan, prerequisites, topic priority matrix, daily habits, milestones, exam simulation guidance, curated recent reviews). Directly referenced from README and PoC guides.
- **Expanded case studies** (notes/*.md now substantially richer, 150-300+ lines each for the previously minimal ones):
  - notes/NODEJS-DESERIALIZATION.md
  - notes/PHP-OBJECT-INJECTION.md
  - notes/SSTI-JINJA2-FLASK.md
  - notes/SECOND-ORDER-SQLI.md
  - notes/DOTNET-VIEWSTATE-DESERIALIZATION.md
  - notes/BASSMASTER-1.5.1-JS-INJECTION.md
  - notes/XXE-FILE-READ-SSRF.md (further detailed)
  - All now include deeper recon, code patterns, bypasses, OSWE-specific timing tips, manual examples, and cross-links to PoCs + guides.
- **Enriched guide**: guides/PHP-Deserialization-Patterns.md (nearly doubled in practical content — more gadget examples, PHAR deep dive, code review 30-min workflow, PoC integration, common pitfalls, exam time boxes).
- **README.md overhaul**:
  - Prominent "Start Here" table pointing to Roadmap + core methodology docs.
  - "Core Exam Topics (High Priority)" callout.
  - Added recent high-quality 2025/2026 OSWE reviews to Exam Resources.
  - Added explicit File Upload subsection (syllabus-critical).
  - Better cross-linking and navigation notes.
- **PoC polish**: Added `stage_verify()` + verification guidance to the lighter Node.js deserialization PoC (poc-examples/nodejs-deserialization/poc.py) for consistency with fuller examples (Java, MSSQL, etc.). Small robustness/doc improvements.
- **New/updated links**: Recent reviews, additional high-value learning material (PortSwigger SSTI, JSON Attacks paper), explicit File Upload emphasis.

### Verification Performed
- No new TODO/FIXME introduced in published content (skeleton templates intentionally retain them as guidance).
- Tables remain consistent `| Order | Name | Link |` format.
- All new links are to public resources; no credentials or non-public material added.
- Cross references between Roadmap ↔ README ↔ guides ↔ notes ↔ poc-examples improved.

### Impact for Learners
- Clear entry point and study sequence (biggest user request addressed).
- Case studies are now actually useful as quick-reference + deep-dive companions instead of one-pagers.
- Roadmap tells you *exactly* which PoC/Notes/Guide to use in which week.
- File Upload gap is now explicitly called out with study pointers (future dedicated PoC still valuable).

**Remaining high-value opportunities** (not completed in this pass):
- ~~Full dedicated `guides/File-Upload-to-RCE.md` + `poc-examples/file-upload-rce/` (skeleton placeholders exist; high exam relevance).~~ **COMPLETED in this pass** — full ~500+ line PoC, 350+ line Notes.md, 400+ line methodology guide with bypass matrix table, ASCII + Mermaid diagram examples, decision tree cheat sheet, verification one-liners, code review greps, OSWE tips. Added to all indexes + case study table.
- Bringing the other lighter PoCs (PHP, SSTI, second-order, dotnet, xxe) to full 400-500+ line feature parity with Java/MSSQL (they are usable but less "batteries-included").
- Further .NET guide expansion (currently one of the shorter ones).
- More HTB / recent student lab recommendations.

These changes make the repo a more complete self-study package while preserving the existing high-quality PoC and guide work.
