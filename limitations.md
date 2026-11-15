# Packet Tracer limitations

Packet Tracer simulates a subset of Cisco IOS. These features were designed for the lab but couldn't run (fully) in Packet Tracer. For each one: what happened, and the configuration that would be used on real hardware.

---

### VLAN ACL (VACL) — not supported
`vlan access-map` and `vlan filter` are rejected. Goal: block ICMP between hosts inside VLAN 20.
```
ip access-list extended V20-ICMP
 permit icmp 10.10.20.0 0.0.0.255 10.10.20.0 0.0.0.255
vlan access-map V20-MAP 10
 match ip address V20-ICMP
 action drop
vlan access-map V20-MAP 20
 action forward
vlan filter V20-MAP vlan-list 20
```

### IP Source Guard — not supported
`ip verify source` is rejected. On real hardware, on every untrusted access port (requires DHCP snooping):
```
interface range f0/2, f0/4 - 24
 ip verify source port-security
! static hosts need a manual binding
ip source binding <MAC> vlan <vlan> <IP> interface f0/x
```

### Control Plane Policing — no `police` action
`policy-map` classes only offer `bandwidth`, `priority`, `shape` and similar; policing isn't available, so CoPP can't be applied.
```
ip access-list extended COPP-ICMP
 permit icmp any any
class-map match-all CM-ICMP
 match access-group name COPP-ICMP
policy-map COPP
 class CM-OSPF
  police 1000000 conform-action transmit exceed-action transmit
 class CM-SSH
  police 1000000 conform-action transmit exceed-action transmit
 class CM-ICMP
  police 8000 conform-action transmit exceed-action drop
 class class-default
  police 64000 conform-action transmit exceed-action drop
control-plane
 service-policy input COPP
```

### DHCP snooping on port-channels
`ip dhcp snooping trust` is rejected on the port-channel interface, so trust is set on the member ports instead. On real IOS it's configured on the port-channel itself.

### `ip ospf cost` on tunnel interfaces
Rejected on tunnels. The backup tunnel was made less preferred by *lowering* the primary serial link's cost instead. On real IOS: `ip ospf cost 65535` on the tunnel interfaces.

### AAA source address
The AAA server lists each router's physical source addresses as clients (IOS sources TACACS+ from the outgoing interface). On real IOS, `ip tacacs source-interface Loopback0` gives one stable client address per device, whichever path is used.

### WLC VLAN tagging
The WLC sends all traffic untagged regardless of the configured VLAN ID, so:
- the management interface only works with the switch port's **native VLAN = 99**;
- wireless clients mapped to the VLAN 40 dynamic interface still land in **VLAN 99**.

Real design: one trunk to the WLC, management interface tagged VLAN 99, dynamic interface tagged VLAN 40, native VLAN 999 on the switch port.

The WLC GUI was also only reachable over plain HTTP.

### 802.1X with EAP-MD5
The full exchange works (port unauthorised → EAPOL → RADIUS), but the RADIUS server returns Access-Reject for correct credentials. Configuration as it would be on real hardware:
```
aaa authentication dot1x default group radius
dot1x system-auth-control
interface f0/2
 authentication port-control auto
 dot1x pae authenticator
```
On real networks EAP-MD5 isn't used anyway — PEAP or EAP-TLS would be.

### Network controller collection
The controller logs in to devices with **Telnet**, not SSH, and the 2911 routers and 3560 switches are reported as *Unsupported* models. Device discovery and the REST API (ticket + inventory) work. A real controller (Cisco Catalyst Center) uses SSH and NETCONF/RESTCONF.

### NTP startup
After the devices boot, NTP associations often stay at `.INIT.` and never poll again until the `ntp server` line is re-entered. `ntp master` on the edge router gives the network a time source that's available immediately.
