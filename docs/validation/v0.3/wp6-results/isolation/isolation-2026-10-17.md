# Isolation test, 2026-10-17T20:50:21Z

| Side | Check | Result | Detail |
|---|---|---|---|
| host | `one_adapter` | PASS | 1 adapters |
| host | `adapter_on_configured_switch` | PASS | switch 'refute-internal' |
| host | `switch_internal` | PASS | [{'Id': '9a27f54d-3435-4ff4-b442-06862e708657', 'Name': 'refute-internal', 'SwitchType': 'Internal'}] |
| host | `port_acls_equal_build` | PASS | 4 entries |
| host | `guest_service_interface_off` | PASS | [{'Enabled': False, 'Id': 'Microsoft:F77C8269-F6D7-4955-A37B-42A503FFE2F1\\6C09BB55-D683-4DA0-8931-C9BF705F6480', 'Name': 'Interface de Serviço de Convidado'}] |
| host | `enhanced_session_off` | PASS | False |
| host | `no_dvd_drive` | PASS | [] |
| guest | `proxy_port_open` | PASS | 10.231.71.3:3128 open |
| guest | `proxy_ssh_blocked` | PASS | 10.231.71.3:22 closed |
| guest | `host_22_blocked` | PASS | 10.231.71.1:22 closed |
| guest | `host_135_blocked` | PASS | 10.231.71.1:135 closed |
| guest | `host_139_blocked` | PASS | 10.231.71.1:139 closed |
| guest | `host_445_blocked` | PASS | 10.231.71.1:445 closed |
| guest | `host_3389_blocked` | PASS | 10.231.71.1:3389 closed |
| guest | `host_5985_blocked` | PASS | 10.231.71.1:5985 closed |
| guest | `host_5986_blocked` | PASS | 10.231.71.1:5986 closed |
| guest | `host_80_blocked` | PASS | 10.231.71.1:80 closed |
| guest | `host_443_blocked` | PASS | 10.231.71.1:443 closed |
| guest | `private_192.168.0.1_blocked` | PASS | 192.168.0.1:80 closed |
| guest | `private_192.168.1.1_blocked` | PASS | 192.168.1.1:80 closed |
| guest | `private_10.0.0.1_blocked` | PASS | 10.0.0.1:80 closed |
| guest | `private_172.16.0.1_blocked` | PASS | 172.16.0.1:80 closed |
| guest | `private_169.254.169.254_blocked` | PASS | 169.254.169.254:80 closed |
| guest | `direct_tcp_1.1.1.1_443_blocked` | PASS | 1.1.1.1:443 closed |
| guest | `direct_tcp_9.9.9.9_53_blocked` | PASS | 9.9.9.9:53 closed |
| guest | `no_dns` | PASS | no name resolution in the guest |
| guest | `proxy_allows_pypi` | PASS | 200 |
| guest | `proxy_refuses_example_com` | PASS | 000 |
| guest | `proxy_refuses_ip_literal` | PASS | 403 |
| guest | `proxy_refuses_other_port` | PASS | 000 |
| guest | `no_ipv6_address` | PASS | none configured |
| guest | `ipv6_blocked` | PASS | only the guest itself answers |
| guest | `container_network_none` | PASS | closed 10.231.71.3/3128 closed 1.1.1.1/443 interfaces lo,  |

Result: **every check passed**.
