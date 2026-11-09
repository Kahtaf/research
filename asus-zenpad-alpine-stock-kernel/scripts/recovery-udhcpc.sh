#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
case "$1" in
deconfig)
  ip -4 addr flush dev "$interface"
  ip route del default dev "$interface" 2>/dev/null || true
;;
bound|renew)
  ifconfig "$interface" "$ip" netmask "$subnet" up
  for gateway in $router; do ip route replace default via "$gateway" dev "$interface"; break; done
  : > /etc/resolv.conf
  for server in $dns; do echo "nameserver $server" >> /etc/resolv.conf; done
  echo 'ALPINE_NATIVE_DHCP_BOUND'
;;
esac
