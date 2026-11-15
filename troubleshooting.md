# Troubleshooting log

Two parts: real problems hit while building the lab, and 24 break-fix scenarios worked through as trouble tickets.

The method that worked best, every time: **start at Layer 1 and move up** — `show interfaces status` → `show interfaces trunk` / `show mac address-table` → `show ip arp` → `show ip route` → the protocol's own `show` commands — and when a config looks right on both sides, prove where the packet dies in Simulation mode instead of guessing.

---

## Part 1 · Real issues from the build

### Switching

**EtherChannel Po1 wouldn't bundle ("vlan mask is different").**
One member port on DSW1 was missing VLAN 999 from its allowed list, and the members also had a duplex mismatch. Members of a bundle must have *identical* settings (allowed VLANs, native VLAN, speed/duplex, mode). After aligning them the bundle still showed members as `(I)` — stand-alone — which a Packet Tracer restart cleared.
*Command:* `show etherchannel summary`, then `show run` on each member.

**Po2 suspended.**
The member ports still had native VLAN 1 while the port-channel had 999.
*Fix:* `switchport trunk native vlan 999` on the members, and remove the leftover `switchport access vlan`.

**Root guard blocked a downlink.**
An access switch had become STP root for VLAN 999 (lowest MAC wins when priorities are default), so the DSW's root guard saw superior BPDUs and put the port into root-inconsistent state.
*Fix:* make the distribution switches root for every VLAN, including the native one: `spanning-tree vlan 999 root primary` / `secondary`.

**Native VLAN mismatch on a trunk.**
One side still on native 1, the other on 999 — CDP mismatch messages and per-VLAN blocking.
*Command:* `show interfaces trunk` on both ends.

### Routing

**HSRP: both switches Active for the same VLAN.**
One switch ran HSRP version 1, the other version 2 — they never saw each other.
*Fix:* `standby version 2` on both, configured *before* the group.

**OSPF neighbours FULL but no routes.**
The DSWs used `ip ospf network point-to-point`, HQ-R used the default broadcast type on the same links. Adjacency formed, but the LSAs didn't describe the link consistently, so no routes were installed.
*Fix:* the same network type on both ends.

**Access switches unreachable from other subnets.**
The switches answered on their own subnet but not from HQ-R. A Layer 2 switch is a host as far as IP goes — it needs `ip default-gateway` to reply to anything off-subnet.

**Backup VPN preferred over the private serial link.**
After `auto-cost reference-bandwidth 100000`, the serial link cost ~64 767 while the tunnel cost ~17 000, so OSPF sent Branch 1 traffic through the backup tunnel.
*Fix:* Packet Tracer refuses `ip ospf cost` on tunnel interfaces, so the serial link got `ip ospf cost 1000` on both ends instead. Verified with a failover test (shut the serial → traffic moves to Tunnel12 → no shut → back).
*Lesson:* changing the reference bandwidth changes every cost — re-check path selection afterwards.

### IP services

**Sales PCs got no DHCP address.**
Simulation mode showed the Discover reaching the server, relayed from 10.10.10.2, and the server answering *"no pool configured for the received port"*. The pool's start address was 10.10.50.0 — the server's own subnet — instead of 10.10.10.20. A DHCP server picks the pool whose network contains the relay address (giaddr).

**A switch wouldn't sync NTP.**
It had no management SVI, so it had no IP to send NTP from.

**NTP associations stuck at `.INIT.`, `when -`.**
`ntp server` was configured before the device could reach the server, and Packet Tracer never retried. Removing and re-adding the line restarted polling. Long-term fix: `ntp master` on the edge router so the network always has a time source.

### AAA

**TACACS+ logins silently fell back to local.**
The AAA server knew HQ-R by its loopback (1.1.1.1), but IOS sources TACACS+ from the *outgoing interface* (10.0.0.1 / 10.0.0.5). The server ignored requests from unknown IPs, the router treated that as "server down" and used the local database.
*Fix:* register the real source addresses (or use `ip tacacs source-interface`).
*Rule learned:* local fallback only happens when the server **doesn't answer** — never when it **rejects**.

**SSH from the IT PC failed before the password prompt.**
The PC had no IP address (DHCP had failed), so the VTY access-class dropped it. The ACL's counters not moving was the clue.

**802.1X port stayed unauthorised.**
Simulation showed the full exchange — EAPOL to the switch, RADIUS to the server — ending in Access-Reject, while RADIUS logins on the same switches also failed. A Packet Tracer restart fixed RADIUS; EAP-MD5 still returned Access-Reject with correct credentials (see limitations).

### VPN

**IKE phase 1 stuck at MM_NO_STATE.**
The peer simply wasn't configured yet — HQ-R tried to negotiate with a router that didn't speak IPsec. Also a reminder that once a crypto map matches GRE to a peer, the tunnel is *down* until both sides are done.

### Wireless

**WLC unreachable after connecting it.**
The switch port was a trunk with native VLAN 999, and the WLC sent its management traffic untagged — so it landed in VLAN 999. Native VLAN 99 on that one port fixed it.

**Wireless clients got management-VLAN addresses.**
`show mac address-table` placed the laptop's MAC in VLAN 99 on the WLC port: the Packet Tracer WLC sends every interface untagged, so dynamic-interface tagging (VLAN 40) never happens. Documented as a limitation.
*Mistake made along the way:* a second WLC-to-switch cable in a different VLAN made the WLC bridge VLAN 40 and 99 together — clients flapped between subnets. Removing it fixed the loop.

**Replacement WLC unreachable for 20 minutes.**
Config, ARP and trunk all checked out. `show interfaces status` finally showed the port as **notconnect** — the cable was wrong.
*Lesson:* check Layer 1 first, always.

### Automation

**Controller reported "Wrong credential" for working credentials.**
Printing the raw JSON from the API showed `"reachabilityFailureReason": "Telnet Authentication Failed"` — the Packet Tracer controller logs in with Telnet, and the VTY lines only allowed SSH. Reading the raw API output found what the GUI didn't say.

---

## Part 2 · Break-fix tickets

24 faults, worked through as trouble tickets in random order: from the user's symptom to the one command that pinpoints the cause.

| # | Symptom | Pinpointing command | Cause → fix |
|---|---|---|---|
| 1 | One VLAN's PCs get 169.254 addresses; static hosts work | `show ip interface vlan 10` | `ip helper-address` missing on the SVIs → re-add (on both DSWs, since either can relay) |
| 2 | No internet in or out, but the edge router can ping the ISP | `show ip nat statistics` | NAT inside/outside swapped → correct the roles |
| 3 | AAA account rejected on one router, local account works remotely | `show run \| include tacacs` vs server entry | TACACS+ key mismatch (case-sensitive) → match keys |
| 4 | Traffic uses the backup tunnel while the primary link is up/up | `show ip ospf interface` | OSPF hello/dead timer mismatch → no adjacency on primary → match timers |
| 5 | Every site loses the internet server; the ISP can reach both ends | `show ip route` on the internet router | /30 mistyped as /24 → connected route beats the default → correct mask |
| 6 | CDP errors, some VLANs blocked on an uplink | `show interfaces trunk` | Native VLAN mismatch → same native VLAN both ends |
| 7 | Branch VPN goes up and down in a steady rhythm | `show ip route <tunnel destination>` | Recursive routing: tunnel destination learned through the tunnel → keep public subnets out of OSPF, /32 static |
| 8 | Gateway works intermittently for one VLAN, duplicate-address logs | `show standby brief` | HSRP group numbers differ → both Active → same group |
| 9 | New PC in VLAN 10 on ASW2 is dead, other VLANs fine | `show interfaces trunk` | VLAN missing from the allowed list → `allowed vlan add` |
| 10 | One host reaches its subnet but nothing else | `ipconfig` | Wrong default gateway → correct it / DHCP |
| 11 | Port-channel SD, members (I), STP blocks a link | `show etherchannel summary` | LACP on one side, PAgP on the other → same protocol |
| 12 | Guests get DHCP but nothing past the gateway | `show ip interface` | ACL applied `out` instead of `in` → fix direction |
| 13 | Link light off after a desk move | `show interfaces status` | Port security err-disabled (sticky MAC) → clear sticky, bounce port |
| 14 | VPN interface up, no OSPF over it, IKE in MM_KEY_EXCH | `show crypto isakmp sa` | Pre-shared key mismatch → match keys |
| 15 | DHCP fails on one switch only, static hosts work | `show ip dhcp snooping` | Uplinks untrusted → `ip dhcp snooping trust` |
| 16 | SSIDs disappear; AP has power and an IP | WLC AP list, port VLAN | AP moved to another VLAN without option 43 / DNS → right VLAN or discovery option |
| 17 | One L3 switch loses all OSPF routes; link pings fine | `show ip ospf neighbor` | OSPF MD5 key mismatch → match keys |
| 18 | WPA2-Enterprise fails, WPA2-Personal works | WLC RADIUS entry vs server | RADIUS shared secret mismatch → match keys |
| 19 | Static-IP servers unreachable after enabling ARP protection | `show ip arp inspection statistics` | DAI drops ARP from hosts without DHCP bindings → ARP ACL (or trust) |
| 20 | IKE up (QM_IDLE) but zero packets encrypted | `show crypto ipsec sa` | Transform set mismatch (phase 2) → match transform sets |
| 21 | One prefix unreachable while OSPF is healthy | `show ip route <prefix>` | Forgotten static route (AD 1) beats OSPF (110) → remove / make floating |
| 22 | Routes flap across area 0 | `show ip ospf` on each router | Duplicate router ID → unique IDs + `clear ip ospf process` |
| 23 | New LAN reaches its gateway only | `show zone security` | Interface left out of every firewall zone → assign a zone (and advertise the subnet) |
| 24 | Every OSPF neighbour flaps at once, everything matches | `show policy-map control-plane` | CoPP polices OSPF too hard → don't rate-limit routing protocols tightly |

### Patterns worth remembering
- **"Works locally, fails beyond X"** → whatever sits at X: gateway, relay, NAT, firewall zone.
- **IKE states tell you the phase:** stuck before QM_IDLE = phase 1 (policy / key); QM_IDLE with zero packets = phase 2 (transform set / crypto ACL).
- **Local login working remotely** on an AAA-configured device = the AAA server isn't being reached or can't be understood (wrong IP, wrong key).
- **Equal prefixes compare AD; different prefixes compare length** — that explains both ticket 5 and ticket 21.
