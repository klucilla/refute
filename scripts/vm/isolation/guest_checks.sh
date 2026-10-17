#!/bin/bash
# The guest half of the WP6 isolation test (wp6-acceptance.md, section "Isolation test
# (V3)"; the maintainer's decision of 2026-10-17). Run once inside the Refute VM, through
# SSH from the host, at the end of phase 2, with the adapter connected in the "build"
# profile. It changes nothing persistent: the only change, a temporary IPv6 link-local
# address for the IPv6 check, is removed before it ends. It prints one line per check:
#   CHECK <name> <PASS|FAIL> <detail>
# A check PASSES when what it observes is what isolation requires.
set -u
PROXY=10.231.71.3
HOST=10.231.71.1
IFACE=$(ip -o link show | awk -F': ' '$2 != "lo" {print $2; exit}')
pass() { echo "CHECK $1 PASS $2"; }
fail() { echo "CHECK $1 FAIL $2"; }
# tcp <name> <host> <port> <expect: open|closed>
tcp() {
  if timeout 5 bash -c "exec 3<>/dev/tcp/$2/$3" 2>/dev/null; then got=open; else got=closed; fi
  if [ "$got" = "$4" ]; then pass "$1" "$2:$3 $got"; else fail "$1" "$2:$3 $got, expected $4"; fi
}

echo "INFO interface $IFACE"
echo "INFO addresses $(ip -o addr show dev "$IFACE" | awk '{print $3, $4}' | tr '\n' ' ')"
echo "INFO routes $(ip route | tr '\n' ';')"

# 1. the proxy port answers; on the SAME target a listening port outside the list (the
#    proxy's SSH) is blocked: the block comes from the port ACLs, with no state of fewer ACLs
tcp proxy_port_open "$PROXY" 3128 open
tcp proxy_ssh_blocked "$PROXY" 22 closed

# 2. the Windows host: nothing the guest starts reaches it (SSH runs only from the host)
for port in 22 135 139 445 3389 5985 5986 80 443; do
  tcp "host_${port}_blocked" "$HOST" "$port" closed
done

# 3. the LAN and private ranges (no route either; the port ACLs deny them as well)
for target in 192.168.0.1 192.168.1.1 10.0.0.1 172.16.0.1 169.254.169.254; do
  tcp "private_${target}_blocked" "$target" 80 closed
done

# 4. the internet without the proxy: TCP and DNS both fail
tcp direct_tcp_1.1.1.1_443_blocked 1.1.1.1 443 closed
tcp direct_tcp_9.9.9.9_53_blocked 9.9.9.9 53 closed
if timeout 5 getent hosts pypi.org >/dev/null 2>&1; then fail no_dns "pypi.org resolved"; else pass no_dns "no name resolution in the guest"; fi

# 5. the proxy lets the allowlist through and nothing else
code() { curl -s -o /dev/null -w '%{http_code}' --max-time 20 -x "http://$PROXY:3128" "$1" 2>/dev/null; }
c=$(code https://pypi.org/simple/pip/); [ "$c" = 200 ] && pass proxy_allows_pypi "$c" || fail proxy_allows_pypi "$c"
c=$(code https://example.com/); [ "$c" != 200 ] && pass proxy_refuses_example_com "$c" || fail proxy_refuses_example_com "$c"
c=$(code http://1.1.1.1/); [ "$c" != 200 ] && pass proxy_refuses_ip_literal "$c" || fail proxy_refuses_ip_literal "$c"
c=$(code https://pypi.org:8443/); [ "$c" != 200 ] && pass proxy_refuses_other_port "$c" || fail proxy_refuses_other_port "$c"

# 6. IPv6: the guest has no IPv6 address; with a temporary link-local address, a ping of
#    all nodes on the link gets no answer, since the port denies every IPv6 packet
if [ -z "$(ip -6 -o addr show dev "$IFACE")" ]; then pass no_ipv6_address "none configured"; else fail no_ipv6_address "$(ip -6 -o addr show dev "$IFACE" | awk '{print $4}')"; fi
sudo ip -6 addr add fe80::2:1/64 dev "$IFACE" 2>/dev/null
sleep 3
if ping -6 -c 3 -W 2 "ff02::1%$IFACE" 2>/dev/null | grep -q 'bytes from'; then
  replies=$(ping -6 -c 3 -W 2 "ff02::1%$IFACE" 2>/dev/null | grep 'bytes from' | grep -vc 'fe80::2:1')
  [ "$replies" = 0 ] && pass ipv6_blocked "only the guest itself answers" || fail ipv6_blocked "$replies answers from other nodes"
else
  pass ipv6_blocked "no answer"
fi
sudo ip -6 addr del fe80::2:1/64 dev "$IFACE" 2>/dev/null

# 7. a container with --network none has no network (Docker Engine installed). The image
#    only needs bash (the Ubuntu image, pinned by digest, is enough); the container lists its
#    interfaces and tries the proxy port and an internet address.
if command -v docker >/dev/null 2>&1; then
  out=$(sudo docker run --rm --network none "${ISOLATION_IMAGE:?set ISOLATION_IMAGE to an image pinned by digest}" \
    bash -c 'for t in 10.231.71.3/3128 1.1.1.1/443; do
  if timeout 3 bash -c "exec 3<>/dev/tcp/$t" 2>/dev/null; then echo "open $t"; else echo "closed $t"; fi
done
echo "interfaces $(tail -n +3 /proc/net/dev | cut -d: -f1 | tr -d " " | tr "\n" ",")"' 2>&1)
  if echo "$out" | grep -q '^open' || ! echo "$out" | grep -q '^interfaces lo,$'; then
    fail container_network_none "$(echo "$out" | tr '\n' ' ')"
  else
    pass container_network_none "$(echo "$out" | tr '\n' ' ')"
  fi
else
  fail container_network_none "docker is not installed"
fi
echo "END"
