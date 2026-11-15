# Device configurations

Running configuration of every network device, exported from Packet Tracer, with every secret removed.

| File | Device |
|---|---|
| `HQ-R.txt` | HQ edge router (NAT, zone-based firewall, IPS, VPN hub, OSPF ABR) |
| `B1-R.txt` | Branch 1 router |
| `B2-R.txt` | Branch 2 router |
| `ISP-R.txt` | ISP router |
| `INTERNET-R.txt` | Internet router |
| `HQ-DSW1.txt`, `HQ-DSW2.txt` | HQ distribution (L3) switches |
| `HQ-ASW1.txt`, `HQ-ASW2.txt` | HQ access switches |
| `B1-S.txt`, `B2-S.txt` | Branch access switches |
| `DMZ-SW.txt` | DMZ switch |
| `INTERNET-SW.txt` | Internet LAN switch |

Replaced with `<REDACTED>` by [`redact.py`](redact.py): enable secrets, user and parser-view secrets, line passwords, TACACS+/RADIUS keys, ISAKMP pre-shared keys, OSPF and NTP authentication keys, the SNMP community and FTP credentials.
