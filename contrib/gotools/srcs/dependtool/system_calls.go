// SPDX-License-Identifier: BSD-3-Clause
//
// Authors: Gaulthier Gain <gaulthier.gain@uliege.be>
//
// Copyright (c) 2020, Université de Liège., ULiege. All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions
// are met:
//
// 1. Redistributions of source code must retain the above copyright
//    notice, this list of conditions and the following disclaimer.
// 2. Redistributions in binary form must reproduce the above copyright
//    notice, this list of conditions and the following disclaimer in the
//    documentation and/or other materials provided with the distribution.
// 3. Neither the name of the copyright holder nor the names of its
//    contributors may be used to endorse or promote products derived from
//    this software without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
// AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
// IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
// ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
// LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
// CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
// SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
// INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
// CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
// ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
// POSSIBILITY OF SUCH DAMAGE.

package dependtool

// InitSystemCalls initialises all Linux system calls.
//
// It returns a map of all system calls.
func initSystemCalls() map[string]*string {
	return map[string]*string{"_llseek": nil, "_newselect": nil, "_sysctl": nil,
		"accept": nil, "accept4": nil, "access": nil, "acct": nil,
		"add_key": nil, "adjtimex": nil, "alarm": nil, "alloc_hugepages": nil,
		"arc_gettls": nil, "arc_settls": nil, "arc_usr_cmpxchg": nil,
		"arch_prctl": nil, "atomic_barrier": nil, "atomic_cmpxchg_32": nil,
		"bdflush": nil, "bfin_spinlock": nil, "bind": nil, "bpf": nil,
		"brk": nil, "breakpoint": nil, "cacheflush": nil, "capget": nil,
		"capset": nil, "chdir": nil, "chmod": nil, "chown": nil, "chown32": nil,
		"chroot": nil, "clock_adjtime": nil, "clock_getres": nil,
		"clock_gettime": nil, "clock_nanosleep": nil, "connect": nil,
		"copy_file_range": nil, "creat": nil, "create_module": nil,
		"delete_module": nil, "dma_memcpy": nil, "dup": nil, "dup2": nil,
		"dup3": nil, "epoll_create": nil, "epoll_create1": nil,
		"epoll_ctl": nil, "epoll_pwait": nil, "epoll_wait": nil, "eventfd": nil,
		"eventfd2": nil, "execv": nil, "execve": nil, "execveat": nil,
		"exit": nil, "exit_group": nil, "faccessat": nil, "fadvise64": nil,
		"fadvise64_64": nil, "fallocate": nil, "fanotify_init": nil,
		"fanotify_mark": nil, "fchdir": nil, "fchmod": nil,
		"fchmodat": nil, "fchown": nil, "fchown32": nil, "fchownat": nil,
		"fcntl": nil, "fcntl64": nil, "fdatasync": nil, "fgetxattr": nil,
		"finit_module": nil, "flistxattr": nil, "flock": nil, "fork": nil,
		"free_hugepages": nil, "fremovexattr": nil, "fsetxattr": nil,
		"fstat": nil, "fstat64": nil, "fstatat64": nil, "fstatfs": nil,
		"fstatfs64": nil, "fsync": nil, "ftruncate": nil, "ftruncate64": nil,
		"futex": nil, "futimesat": nil, "get_kernel_syms": nil,
		"get_mempolicy": nil, "get_robust_list": nil, "get_thread_area": nil,
		"get_tls": nil, "getcpu": nil, "getcwd": nil, "getdents": nil,
		"getdents64": nil, "getdomainname": nil, "getdtablesize": nil,
		"getegid": nil, "getegid32": nil, "geteuid": nil, "geteuid32": nil,
		"getgid": nil, "getgid32": nil, "getgroups": nil, "getgroups32": nil,
		"gethostname": nil, "getitimer": nil, "getpeername": nil,
		"getpagesize": nil, "getpgid": nil, "getpgrp": nil, "getpid": nil,
		"getppid": nil, "getpriority": nil, "getrandom": nil, "getresgid": nil,
		"getresgid32": nil, "getresuid": nil, "getresuid32": nil,
		"getrlimit": nil, "getrusage": nil, "getsid": nil, "getsockname": nil,
		"getsockopt": nil, "gettid": nil, "gettimeofday": nil, "getuid": nil,
		"getuid32": nil, "getunwind": nil, "getxattr": nil, "getxgid": nil,
		"getxpid": nil, "getxuid": nil, "init_module": nil,
		"inotify_add_watch": nil, "inotify_init": nil, "inotify_init1": nil,
		"inotify_rm_watch": nil, "io_cancel": nil, "io_destroy": nil,
		"io_getevents": nil, "io_pgetevents": nil, "io_setup": nil,
		"io_submit": nil, "ioctl": nil, "ioperm": nil, "iopl": nil,
		"ioprio_get": nil, "ioprio_set": nil, "ipc": nil, "kcmp": nil,
		"kern_features": nil, "kexec_file_load": nil, "kexec_load": nil,
		"keyctl": nil, "kill": nil, "lchown": nil, "lchown32": nil,
		"lgetxattr": nil, "link": nil, "linkat": nil, "listen": nil,
		"listxattr": nil, "llistxattr": nil, "lookup_dcookie": nil,
		"lremovexattr": nil, "lseek": nil, "lsetxattr": nil, "lstat": nil,
		"lstat64": nil, "madvise": nil, "mbind": nil, "memory_ordering": nil,
		"metag_get_tls": nil, "metag_set_fpu_flags": nil, "metag_set_tls": nil,
		"metag_setglobalbit": nil, "membarrier": nil, "memfd_create": nil,
		"migrate_pages": nil, "mincore": nil, "mkdir": nil,
		"mkdirat": nil, "mknod": nil, "mknodat": nil, "mlock": nil,
		"mlock2": nil, "mlockall": nil, "mmap": nil, "mmap2": nil,
		"modify_ldt": nil, "mount": nil, "move_pages": nil, "mprotect": nil,
		"mq_getsetattr": nil, "mq_notify": nil, "mq_open": nil,
		"mq_timedreceive": nil, "mq_timedsend": nil, "mq_unlink": nil,
		"mremap": nil, "msgctl": nil, "msgget": nil, "msgrcv": nil,
		"msgsnd": nil, "msync": nil, "munlock": nil, "munlockall": nil,
		"munmap": nil, "name_to_handle_at": nil, "nanosleep": nil,
		"newfstatat": nil, "nfsservctl": nil, "nice": nil, "old_adjtimex": nil,
		"old_getrlimit": nil, "oldfstat": nil, "oldlstat": nil,
		"oldolduname": nil, "oldstat": nil, "oldumount": nil, "olduname": nil,
		"open": nil, "open_by_handle_at": nil, "openat": nil,
		"or1k_atomic": nil, "pause": nil, "pciconfig_iobase": nil,
		"pciconfig_read": nil, "pciconfig_write": nil, "perf_event_open": nil,
		"personality": nil, "perfctr": nil, "perfmonctl": nil, "pipe": nil,
		"pipe2": nil, "pivot_root": nil, "pkey_alloc": nil, "pkey_free": nil,
		"pkey_mprotect": nil, "poll": nil, "ppoll": nil, "prctl": nil,
		"pread": nil, "pread64": nil, "preadv": nil, "preadv2": nil,
		"prlimit64": nil, "process_vm_readv": nil, "process_vm_writev": nil,
		"pselect6": nil, "ptrace": nil, "pwrite": nil, "pwrite64": nil,
		"pwritev": nil, "pwritev2": nil, "query_module": nil, "quotactl": nil,
		"read": nil, "readahead": nil, "readdir": nil, "readlink": nil,
		"readlinkat": nil, "readv": nil, "reboot": nil, "recv": nil,
		"recvfrom": nil, "recvmsg": nil, "recvmmsg": nil,
		"remap_file_pages": nil, "removexattr": nil, "rename": nil,
		"renameat": nil, "renameat2": nil, "request_key": nil,
		"restart_syscall": nil, "riscv_flush_icache": nil, "rmdir": nil,
		"rseq": nil, "rt_sigaction": nil, "rt_sigpending": nil,
		"rt_sigprocmask": nil, "rt_sigqueueinfo": nil, "rt_sigreturn": nil,
		"rt_sigsuspend": nil, "rt_sigtimedwait": nil, "rt_tgsigqueueinfo": nil,
		"rtas": nil, "s390_runtime_instr": nil, "s390_pci_mmio_read": nil,
		"s390_pci_mmio_write": nil, "s390_sthyi": nil,
		"s390_guarded_storage": nil, "sched_get_affinity": nil,
		"sched_get_priority_max": nil, "sched_get_priority_min": nil,
		"sched_getaffinity": nil, "sched_getattr": nil, "sched_getparam": nil,
		"sched_getscheduler": nil, "sched_rr_get_interval": nil,
		"sched_set_affinity": nil, "sched_setaffinity": nil,
		"sched_setattr": nil, "sched_setparam": nil, "sched_setscheduler": nil,
		"sched_yield": nil, "seccomp": nil, "select": nil, "semctl": nil,
		"semget": nil, "semop": nil, "semtimedop": nil, "send": nil,
		"sendfile": nil, "sendfile64": nil, "sendmmsg": nil, "sendmsg": nil,
		"sendto": nil, "set_mempolicy": nil, "set_robust_list": nil,
		"set_thread_area": nil, "set_tid_address": nil, "set_tls": nil,
		"setdomainname": nil, "setfsgid": nil, "setfsgid32": nil,
		"setfsuid": nil, "setfsuid32": nil, "setgid": nil, "setgid32": nil,
		"setgroups": nil, "setgroups32": nil, "sethae": nil, "sethostname": nil,
		"setitimer": nil, "setns": nil, "setpgid": nil, "setpgrp": nil,
		"setpriority": nil, "setregid": nil, "setregid32": nil,
		"setresgid": nil, "setresgid32": nil, "setresuid": nil,
		"setresuid32": nil, "setreuid": nil, "setreuid32": nil,
		"setrlimit": nil, "setsid": nil, "setsockopt": nil, "settimeofday": nil,
		"setuid": nil, "setuid32": nil, "setup": nil, "setxattr": nil,
		"sgetmask": nil, "shmat": nil, "shmctl": nil, "shmdt": nil,
		"shmget": nil, "shutdown": nil, "sigaction": nil, "sigaltstack": nil,
		"signal": nil, "signalfd": nil, "signalfd4": nil, "sigpending": nil,
		"sigprocmask": nil, "sigreturn": nil, "sigsuspend": nil, "socket": nil,
		"socketcall": nil, "socketpair": nil, "spill": nil, "splice": nil,
		"spu_create": nil, "spu_run": nil, "sram_alloc": nil, "sram_free": nil,
		"ssetmask": nil, "stat": nil, "stat64": nil, "statfs": nil,
		"statfs64": nil, "statx": nil, "stime": nil, "subpage_prot": nil,
		"switch_endian": nil, "swapcontext": nil, "swapoff": nil, "swapon": nil,
		"symlink": nil, "symlinkat": nil, "sync": nil, "sync_file_range": nil,
		"sync_file_range2": nil, "syncfs": nil, "sys_debug_setcontext": nil,
		"syscall": nil, "sysfs": nil, "sysinfo": nil, "syslog": nil,
		"sysmips": nil, "tee": nil, "tgkill": nil, "time": nil,
		"timer_create": nil, "timer_delete": nil, "timer_getoverrun": nil,
		"timer_gettime": nil, "timer_settime": nil,
		"timerfd_create": nil, "timerfd_gettime": nil, "timerfd_settime": nil,
		"times": nil, "tkill": nil, "truncate": nil, "truncate64": nil,
		"ugetrlimit": nil, "umask": nil, "umount": nil, "umount2": nil,
		"uname": nil, "unlink": nil, "unlinkat": nil, "unshare": nil,
		"uselib": nil, "ustat": nil, "userfaultfd": nil, "usr26": nil,
		"usr32": nil, "utime": nil, "utimensat": nil, "utimes": nil,
		"utrap_install": nil, "vfork": nil, "vhangup": nil, "vm86old": nil,
		"vm86": nil, "vmsplice": nil, "wait4": nil, "waitid": nil,
		"waitpid": nil, "write": nil, "writev": nil, "xtensa": nil}
}
