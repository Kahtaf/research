from pathlib import Path
p=Path(__file__).resolve().parents[1]/'stagedpatches/kernel-input/drivers/misc/mediatek/connectivity/wlan/gen2/os/linux/gl_init.c';s=p.read_text();a=s.index('void wlanHandleSystemSuspend(')
s=s[:a]+'''/* ip6_ptr is an inet6_dev, never an in_device. Hold its address-list lock. */
static bool p00a_first_ipv4(struct net_device *dev, u8 *addr)
{
	struct in_device *idev;
	bool found = false;

	rcu_read_lock();
	idev = __in_dev_get_rcu(dev);
	if (idev) {
		struct in_ifaddr *ifa = rcu_dereference(idev->ifa_list);
		if (ifa) {
			memcpy(addr, &ifa->ifa_local, 4);
			found = true;
		}
	}
	rcu_read_unlock();
	return found;
}
#ifdef CONFIG_IPV6
static bool p00a_first_ipv6(struct net_device *dev, u8 *addr)
{
	struct inet6_dev *idev = in6_dev_get(dev);
	struct inet6_ifaddr *ifa;
	bool found = false;

	if (!idev)
		return false;
	read_lock_bh(&idev->lock);
	list_for_each_entry(ifa, &idev->addr_list, if_list) {
		if (ifa->flags & (IFA_F_TENTATIVE | IFA_F_DADFAILED))
			continue;
		memcpy(addr, &ifa->addr, 16);
		found = true;
		break;
	}
	read_unlock_bh(&idev->lock);
	in6_dev_put(idev);
	return found;
}
#endif

'''+s[a:]
a=s.index('\tif (!prDev || !(prDev->ip_ptr)',s.index('void wlanHandleSystemSuspend('));b=s.index('\n\t/* <7> set up the ARP filter */',a)
s=s[:a]+'''\tu4NumIPv4 = p00a_first_ipv4(prDev, ip) ? 1 : 0;
#ifdef CONFIG_IPV6
	u4NumIPv6 = p00a_first_ipv6(prDev, ip6) ? 1 : 0;
#endif
'''+s[b:]
a=s.index('\t/* <2> get the IPv4 address */',s.index('void wlanHandleSystemResume('));b=s.index('\t/* <7> clear the ARP filter */',a)
s=s[:a]+'''\tp00a_first_ipv4(prDev, ip);
#ifdef CONFIG_IPV6
	p00a_first_ipv6(prDev, ip6);
#endif
'''+s[b:]
s=s.replace('prDev = arWlanDevInfo[u4WlanDevNum - 1].prDev;','prDev = arWlanDevInfo[u4WlanDevNum - 1].prDev;\n\tif (!prDev)\n\t\treturn;')
s=s.replace('#include "precomp.h"','#include "precomp.h"\n#include <net/addrconf.h>')
s=s.replace('notify_suspend:\n','').replace('notify_resume:\n','')
p.write_text(s)
