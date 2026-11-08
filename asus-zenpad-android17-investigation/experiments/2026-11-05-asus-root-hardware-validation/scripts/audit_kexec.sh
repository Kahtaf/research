#!/system/bin/sh
set -eu
grep -E ' (compat_sys_kexec_load|sys_kexec_file_load|sys_kexec_load|sys_ni_syscall|machine_kexec|kernel_kexec)$' /proc/kallsyms
