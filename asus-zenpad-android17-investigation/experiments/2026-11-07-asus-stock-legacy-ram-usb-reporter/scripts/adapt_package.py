from pathlib import Path
r=Path(__file__).resolve().parents[1]
p=r/'scripts/build.py';s=p.read_text()
s=s.replace("REPORTER = WORK / '2026-11-07-asus-linux49-usb-ram-report'", "REPORTER = WORK / '2026-11-07-asus-stock-usb-reporter-failure-log'")
s=s.replace("CURRENT = '039c5a52d9ac04fd515c2081c455066057d1503d6979fc81a5b2c70712bc7dba'", "CURRENT = 'a647247d220a0a33fc23ee125744847b836f20908539d9f150054aa20f1ce20d'")
a=s.index('    assert setup_operations(source)');z=s.index('    copies = {}',a)
s=s[:a]+'''    for name in ('make_fat','clean_uname','log_event','log_call','log_guard','log_open','log_uname','log_watchdog','log_watchdog_return','put','equals','unique_udc','arm_watchdog','lifecycle'):
        assert cbody(source,name)==cbody(original_c,name), name
    assert cbody(source,'ram_report').replace('ram_created=st;rc=0;', 'rc=0;') == cbody(original_c,'ram_report')
    for macro in ('RUN_ID','USB_SERIAL','RAMFILE','FAT_BYTES','TMPFS_MAGIC','LOG_REV','LOG_NODE','LOG_RECORDS'):
        assert re.search(r'^#define '+macro+r' .+$',source,re.M)[0]==re.search(r'^#define '+macro+r' .+$',original_c,re.M)[0]
    for policy in ('alarm(60)', 'end.tv_sec+=60', 'CLOCK_MONOTONIC,TIMER_ABSTIME,&end,NULL', 'while(r==EINTR)', 'for(;;)pause()'):
        assert policy in source and policy in original_c
    assert source.index('log_open();log_uname();') < source.index('int setup_rc=setup();')
    assert not any(s in source for s in ('mmcblk', 'system(', 'execve(', 'socket(', 'nodename', 'domainname', 'configfs', 'usb_gadget/g1', 'unregister', '/unbind')) or ('configfs' in source and source.count('configfs')==1 and '/* Explicit STOCK' in source and not any(s in source for s in ('mmcblk','system(','execve(','socket(','nodename','domainname','usb_gadget/g1','unregister','/unbind')))
    setup=cbody(source,'setup')
    ordered=['legacy_paths()', 'equals(LUN "file","")', 'put(A "enable","0")', 'put(A "functions","mass_storage")', 'put(LUN "ro","1")', 'log_event("stage","lun.attach"', 'put(LUN "file",RAMFILE)', 'legacy_owned=1', 'put(A "enable","1")']
    positions=[setup.index(v) for v in ordered]; assert positions==sorted(positions)
    assert 'equals(LUN "ro","1")' in setup[setup.index('put(LUN "ro","1")'):setup.index('put(LUN "file",RAMFILE)')]
    assert 'if(!legacy_owned)return' in cbody(source,'disable')
    assert 'watchdog_disable();log_watchdog();' in cbody(source,'watchdog_signal')

''' +s[z:]
s=s.replace('compile-2-attempt.json','compile-1-attempt.json')
s=s.replace("'udc.bind'", "'legacy.enable'")
s=s.replace("original = (CONTROL / 'source/install.py').read_text()", "original = (REPORTER / 'source/install.py').read_text()")
s=s.replace("IMAGE_SHA='e7d5f3c93a1c94d0f27c3f19e7b29aab32d70d5139e296bad8ab749c3852c57e'", "IMAGE_SHA='cd3cf35840129247e93b7df899d8948d811745c48e156935f9bcdd937dee0dd2'")
s=s.replace('len(image)==7737344','len(image)==7741440')
s=s.replace("profile='exact-stock-3.18.35-unchanged-ram-usb-pid1-reporter-control'", "profile='exact-stock-3.18.35-ram-usb-pid1-reporter-failure-log-r1'")
s=s.replace('exact-stock-3.18.35-ram-usb-pid1-reporter-failure-log-r1\'",\n    }', 'exact-stock-3.18.35-legacy-ram-usb-pid1-reporter-r1\'",\n    }')
s=s.replace("fromfile='stockcontrol/source/install.py'", "fromfile='failure-log/source/install.py'")
s=s.replace('setup_operation_arguments_and_order_exact=True, setup_operation_count=len(setup_operations(source)),', 'backend="stock-only legacy android_usb", configfs_setup_replaced=True,')
s=s.replace('original_udc_absence_policy_retained=True', 'original_udc_absence_policy_retained=True, fixed_stock_udc_identity_guard=True, fresh_disabled_empty_functions_required=True, kernel_sysfs_paths_guarded=True, sole_empty_lun_required=True, read_only_before_attachment_and_enable=True, reverified_private_regular_singlelink_tmpfs_0444=True, own_configuration_only_disable=True')
s=s.replace('build=dict(attempts=2, successful_compiles=1, second_compile_explicitly_authorized=True, first_failure=\'three ignored logging write return values under -Werror\',', 'build=dict(attempts=1, successful_compiles=1,')
s=s.replace("signal_records_max=2", "signal_records_max=3")
s=s.replace("dt_token_control='initrd=0x44000200,0x03e4a3'", "dt_token_control='initrd=0x44000200,0x03e4a3'")
s=s.replace('No runtime/helper execution, USB validation, or proof of printk/last_kmsg retention.', 'No runtime/helper execution or USB validation. Prior physical trial proved failure-log retention; this revision has no runtime proof. Public GPL source differs from shipped binary; shipped attribute disassembly retained separately. No Linux 4.9 equivalence claim.')
p.write_text(s)
p=r/'scripts/plan_only.py';s=p.read_text().replace('stock_failure_log_installer','stock_legacy_installer').replace("assert '039c5a52d9ac04fd515c2081c455066057d1503d6979fc81a5b2c70712bc7dba'", "assert 'a647247d220a0a33fc23ee125744847b836f20908539d9f150054aa20f1ce20d'");p.write_text(s)
