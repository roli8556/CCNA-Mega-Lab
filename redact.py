"""Remove secrets from Cisco IOS running-configs before publishing.

Usage:  python redact.py HQ-R.txt B1-R.txt ...
Each file is rewritten in place. Review the result before you commit it.
"""
import re
import sys

RULES = [
    # enable / user secrets and passwords (any hash type)
    (r"^(enable (?:secret|password)(?: level \d+)?)( \d)? .+$", r"\1 <REDACTED>"),
    (r"^(username \S+(?: privilege \d+)?(?: view \S+)? (?:secret|password))( \d)? .+$", r"\1 <REDACTED>"),
    (r"^(\s*password)( \d)? .+$", r"\1 <REDACTED>"),
    (r"^(\s+secret)( \d)? .+$", r"\1 <REDACTED>"),  # parser view secrets
    (r"^(ip ftp (?:password|username))( \d)? .+$", r"\1 <REDACTED>"),
    # AAA keys
    (r"^(tacacs-server host \S+.*? key)( \d)? .+$", r"\1 <REDACTED>"),
    (r"^(radius-server host \S+.*? key)( \d)? .+$", r"\1 <REDACTED>"),
    (r"^((?:tacacs|radius)-server key)( \d)? .+$", r"\1 <REDACTED>"),
    (r"^(\s*key)( \d)? .+$", r"\1 <REDACTED>"),
    # IPsec pre-shared keys
    (r"^(crypto isakmp key) \S+ (address .+)$", r"\1 <REDACTED> \2"),
    # OSPF authentication
    (r"^(\s*ip ospf message-digest-key \d+ md5)( \d)? .+$", r"\1 <REDACTED>"),
    (r"^(\s*ip ospf authentication-key)( \d)? .+$", r"\1 <REDACTED>"),
    # NTP authentication
    (r"^(ntp authentication-key \d+ md5) .+$", r"\1 <REDACTED>"),
    # SNMP communities
    (r"^(snmp-server community) \S+(.*)$", r"\1 <REDACTED>\2"),
    # HSRP authentication
    (r"^(\s*standby \d+ authentication(?: md5 key-string)?)( \d)? .+$", r"\1 <REDACTED>"),
]

for path in sys.argv[1:]:
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    out = []
    for line in lines:
        for pattern, repl in RULES:
            line = re.sub(pattern, repl, line)
        out.append(line)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(f"redacted {path}")
