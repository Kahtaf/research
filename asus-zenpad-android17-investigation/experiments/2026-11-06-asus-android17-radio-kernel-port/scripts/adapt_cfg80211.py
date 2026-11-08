from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]/'stagedpatches/kernel-input/drivers/misc/mediatek/connectivity'
W=R/'wlan/gen2'
def edit(p,old,new):
 s=p.read_text(); assert old in s,(p,old);p.write_text(s.replace(old,new))
# 4.9 nl80211 band and station filled-bit API, with original semantics preserved.
for p in W.rglob('*'):
 if p.suffix not in ['.c','.h']:continue
 s=p.read_text()
 for band in ['2GHZ','5GHZ','60GHZ']:
  s=s.replace('IEEE80211_BAND_'+band,'NL80211_BAND_'+band)
 s=s.replace('IEEE80211_NUM_BANDS','NUM_NL80211_BANDS').replace('enum ieee80211_band','enum nl80211_band')
 for attr in ['TX_BITRATE','SIGNAL','TX_PACKETS','TX_FAILED','INACTIVE_TIME']:
  s=s.replace('STATION_INFO_'+attr,'BIT_ULL(NL80211_STA_INFO_'+attr+')')
 s=s.replace('rStationInfo.filled = STATION_INFO_ASSOC_REQ_IES;','memset(&rStationInfo, 0, sizeof(rStationInfo));')
 s=s.replace('/* rStationInfo.filled |= STATION_INFO_ASSOC_REQ_IES; */','')
 # A real adapter creates the new scan-info structure; abort is not discarded.
 s=s.replace('cfg80211_scan_done(', 'p00a_cfg80211_scan_done(')
 s=s.replace('cfg80211_vendor_event_alloc(wiphy,', 'cfg80211_vendor_event_alloc(wiphy, NULL,')
 p.write_text(s)
p=W/'os/linux/include/gl_os.h'
# gl_os pulls cfg80211 before helper, so append at its include rather than bottom after guard.
s=p.read_text();match=re.search(r'#include\s*[<"]net/cfg80211.h[>"]',s);assert match
s=s[:match.end()]+'''

static inline void p00a_cfg80211_scan_done(struct cfg80211_scan_request *request,
					 bool aborted)
{
	struct cfg80211_scan_info info = { .aborted = aborted };
	cfg80211_scan_done(request, &info);
}
'''+s[match.end():];p.write_text(s)
# Del-station operation was a success-only placeholder in ASUS STA path; don't advertise it.
p=W/'os/linux/gl_init.c'
edit(p,'\t.del_station = mtk_cfg80211_del_station,','')
p=W/'os/linux/gl_cfg80211.c'
edit(p,'int mtk_cfg80211_del_station(struct wiphy *wiphy, struct net_device *ndev, const u8 *mac)\n{\n\treturn 0;\n}', 'int mtk_cfg80211_del_station(struct wiphy *wiphy, struct net_device *ndev,\n\t\t\t     struct station_del_parameters *params)\n{\n\treturn -EOPNOTSUPP;\n}')
edit(W/'os/linux/include/gl_cfg80211.h','int mtk_cfg80211_del_station(struct wiphy *wiphy, struct net_device *ndev, const u8 *mac);','int mtk_cfg80211_del_station(struct wiphy *wiphy, struct net_device *ndev,\n\t\t\t     struct station_del_parameters *params);')
# P2P has an actual disconnection message. Carry the requested MAC/reason; unsupported
# disassociation subtype is rejected instead of silently emitting a deauthentication.
p=W/'os/linux/gl_p2p_cfg80211.c'
edit(p,'int mtk_p2p_cfg80211_del_station(struct wiphy *wiphy, struct net_device *dev, const u8 *mac)\n{','''int mtk_p2p_cfg80211_del_station(struct wiphy *wiphy, struct net_device *dev,
				struct station_del_parameters *params)
{
	const u8 *mac = params->mac;''')
# nl80211 fills subtype with 0 or IEEE80211_STYPE_DEAUTH >> 4; kernel source verify value later.
edit(p,'prDisconnectMsg->u2ReasonCode = REASON_CODE_UNSPECIFIED;','prDisconnectMsg->u2ReasonCode = params->reason_code;')
edit(W/'os/linux/include/gl_p2p_ioctl.h','int mtk_p2p_cfg80211_del_station(struct wiphy *wiphy, struct net_device *dev, const u8 *mac);','int mtk_p2p_cfg80211_del_station(struct wiphy *wiphy, struct net_device *dev,\n\t\t\t\tstruct station_del_parameters *params);')
# Driver firmware supports one repeated scan interval. Reject plans it cannot represent.
p=W/'os/linux/gl_cfg80211.c'
edit(p,'prSchedScanRequest->u2ScanInterval = (UINT_16) (request->interval);','prSchedScanRequest->u2ScanInterval = (UINT_16) request->scan_plans[0].interval;')
needle='int mtk_cfg80211_sched_scan_stop'
s=p.read_text();a=s.index('mtk_cfg80211_sched_scan_start(');b=s.index(needle,a);block=s[a:b]
# Place validation immediately before allocation, after declarations.
match=re.search(r'\n\s*prSchedScanRequest =',block);assert match
pos=a+match.start();s=s[:pos]+'''
	if (request->n_scan_plans != 1 || request->scan_plans[0].iterations ||
	    !request->scan_plans[0].interval || request->scan_plans[0].interval > 65535)
		return -EOPNOTSUPP;
'''+s[pos:];p.write_text(s)
p=W/'os/linux/gl_kal.c'
edit(p,'ssid.aucSsid, ssid.u4SsidLen, WLAN_CAPABILITY_ESS, WLAN_CAPABILITY_ESS);','ssid.aucSsid, ssid.u4SsidLen, IEEE80211_BSS_TYPE_ESS, IEEE80211_PRIVACY_ANY);')
# Track local cfg80211 disconnection request rather than guessing every event was remote.
p=W/'os/linux/include/gl_os.h'
s=p.read_text();match=re.search(r'struct cfg80211_scan_request\s*\*prScanRequest;',s);assert match
s=s[:match.end()]+'\n\tbool p00a_local_disconnect;'+s[match.end():];p.write_text(s)
p=W/'os/linux/gl_cfg80211.c';s=p.read_text();a=s.index('int mtk_cfg80211_disconnect(');b=s.index('\n}',a);block=s[a:b]
match=re.search(r'\n\s*rStatus = kalIoctl',block);assert match
pos=a+match.start();s=s[:pos]+'\n\tprGlueInfo->p00a_local_disconnect = true;\n'+s[pos:];p.write_text(s)
p=W/'os/linux/gl_kal.c'
edit(p,'cfg80211_disconnected(prGlueInfo->prDevHandler, u2DeauthReason, NULL, 0, GFP_KERNEL);','''cfg80211_disconnected(prGlueInfo->prDevHandler, u2DeauthReason, NULL, 0,
					      prGlueInfo->p00a_local_disconnect, GFP_KERNEL);
			prGlueInfo->p00a_local_disconnect = false;''')
# These callbacks lack a local flag; no local P2P route is enabled in the first STA trial.
edit(W/'os/linux/gl_p2p_kal.c','u2StatusReason, pucRxIEBuf, u2RxIELen, GFP_KERNEL);','u2StatusReason, pucRxIEBuf, u2RxIELen, false, GFP_KERNEL);')
# 4.9 rx_mgmt last argument is NL80211_RXMGMT_FLAG_* not gfp allocation flags.
for name in ['gl_kal.c','gl_p2p_kal.c']:
 p=W/'os/linux'/name
 s=p.read_text();s=re.sub(r'(prSwRfb->pvHeader, prSwRfb->u2PacketLen), GFP_(?:KERNEL|ATOMIC)\);',r'\1, 0);',s);p.write_text(s)
# last_rx disappeared; rx stats are already recorded by the driver on this path.
for p in W.rglob('*.c'):
 s=p.read_text();s=re.sub(r'^\s*prNetDev->last_rx = jiffies;\n','\n',s,flags=re.M);p.write_text(s)
