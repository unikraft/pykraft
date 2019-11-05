// Copyright 2019 The UNICORE Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file
//
// Author: Gaulthier Gain <gaulthier.gain@uliege.be>

package buildtool

import (
	"bufio"
	"io"
	"os"
	"strings"

	u "tools/common"
)

const (
	CONFIG          = iota // Config <CONFIG_.*> = <value>
	COMMENTEDCONFIG        // Commented config: # <CONFIG_.*> is not set
	HEADER                 // Header: # <.*>
	SEPARATOR              // Separator: #
	LINEFEED               // Line FEED: \n
)

type KConfig struct {
	Config string
	Value  *string
	Type   int
}

// writeConfig writes a '.config' file for the Unikraft build system.
//
// It returns an error if any, otherwise it returns nil.
func writeConfig(filename string, items []*KConfig) error {

	f, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer f.Close()

	for _, kConfig := range items {

		var config string
		switch kConfig.Type {
		case CONFIG:
			config = kConfig.Config + "=" + *kConfig.Value
		case COMMENTEDCONFIG:
			config = "# " + kConfig.Config + " is not set"
		case HEADER:
			config = kConfig.Config
		case SEPARATOR:
			config = "#"
		case LINEFEED:
			config = "\n"
		}
		if _, err := f.Write([]byte(config + "\n")); err != nil {
			u.PrintErr(err)
		}
	}

	return nil
}

// parseConfig parses a '.config' file used by the Unikraft build system.
//
// It returns a list of KConfig and an error if any, otherwise it returns nil.
func parseConfig(filename string, kConfigMap map[string]*KConfig,
	items []*KConfig, matchedLibs []string) ([]*KConfig, error) {

	f, err := os.Open(filename)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	r := bufio.NewReader(f)
	for {
		line, err := r.ReadString(0x0A)

		items = addKConfig(line, kConfigMap, items, matchedLibs)

		if err == io.EOF {
			break
		} else if err != nil {
			return nil, err
		}
	}

	return items, nil
}

// addKConfig adds a KConfig entry to adequate data structures.
//
// It returns a list of KConfig. This list will be saved into a '.config' file.
func addKConfig(line string, kConfigMap map[string]*KConfig,
	items []*KConfig, matchedLibs []string) []*KConfig {

	var config string
	var value *string
	var typeConfig int

	switch {
	case strings.HasPrefix(line, "#") && strings.Contains(line,
		"CONFIG"): // Commented config: # <CONFIG_.*> is not set

		split := strings.Fields(line)
		config = split[1]
		value = nil
		typeConfig = COMMENTEDCONFIG
	case strings.HasPrefix(line, "#") && len(line) > 2: // Separator: #
		config = strings.TrimSuffix(line, "\n")
		value = nil
		typeConfig = HEADER
	case strings.HasPrefix(line, "#") && len(line) == 2: // Header: # <.*>
		config, value = "#", nil
		typeConfig = SEPARATOR
	case strings.Contains(line, "="): // Config: <CONFIG_.*> = y
		split := strings.Split(line, "=")
		config = split[0]
		word := strings.TrimSuffix(split[1], "\n")
		value = &word
		typeConfig = CONFIG
	default: // Line FEED
		config, value = "#", nil
		typeConfig = LINEFEED
	}

	// Create KConfig
	kConfig := &KConfig{
		config,
		value,
		typeConfig,
	}

	// If config is not a comment, perform additional procedures
	if config != "#" {
		kConfigMap[config] = kConfig
		items = append(items, kConfigMap[config])
		items = addInternalConfig(config, kConfigMap, items)
		items = matchLibsKconfig(config, kConfigMap, items, matchedLibs)
	} else {
		items = append(items, kConfig)
	}

	return items
}

// updateConfig updates KConfig entries to particular values.
//
// It returns a list of KConfig.
func updateConfig(kConfigMap map[string]*KConfig, items []*KConfig) []*KConfig {
	v := "y"
	var configs = []*KConfig{
		// CONFIG libs
		{"CONFIG_HAVE_BOOTENTRY", &v, CONFIG},
		{"CONFIG_HAVE_SCHED", &v, CONFIG},
		{"CONFIG_LIBUKARGPARSE", &v, CONFIG},
		{"CONFIG_LIBUKBUS", &v, CONFIG},
		{"CONFIG_LIBUKSGLIST", &v, CONFIG},
		{"CONFIG_LIBUKTIMECONV", &v, CONFIG},

		// CONFIG build
		{"CONFIG_OPTIMIZE_NONE", &v, CONFIG},
		{"CONFIG_OPTIMIZE_PERF", nil, COMMENTEDCONFIG},
	}

	return SetConfig(configs, kConfigMap, items)
}

// SetConfig updates a specific KConfig entry.
//
// It returns a list of KConfig.
func SetConfig(newConfigs []*KConfig, kConfigMap map[string]*KConfig,
	items []*KConfig) []*KConfig {

	for _, conf := range newConfigs {
		// If kConfigMap does not contains the value, add it
		if _, ok := kConfigMap[conf.Config]; !ok {
			if len(conf.Config) > 1 {
				kConfigMap[conf.Config] = conf
				items = append(items, kConfigMap[conf.Config])
			} else {
				items = append(items, conf)
			}
		} else {
			// Update only
			newConfiguration := kConfigMap[conf.Config]
			newConfiguration.Value = conf.Value
			newConfiguration.Type = conf.Type
		}
	}

	return items
}

// matchLibsKconfig performs the matching between Kconfig entries and micro-libs
// and updates the right Kconfig
//
// It returns a list of KConfig.
func matchLibsKconfig(conf string, kConfigMap map[string]*KConfig,
	items []*KConfig, matchedLibs []string) []*KConfig {

	v := "y"
	switch conf {
	case "CONFIG_LIBPOSIX_PROCESS":
		if u.Contains(matchedLibs, POSIXPROCESS) {
			configs := []*KConfig{
				{"CONFIG_LIBPOSIX_PROCESS", &v, CONFIG},
			}
			items = SetConfig(configs, kConfigMap, items)
		}
	case "CONFIG_LIBPOSIX_USER":
		if u.Contains(matchedLibs, POSIXUSER) {
			configs := []*KConfig{
				{"CONFIG_LIBPOSIX_USER", &v, CONFIG},
			}
			items = SetConfig(configs, kConfigMap, items)
		}
	case "CONFIG_LIBUKTIME":
		if u.Contains(matchedLibs, UKTIME) {
			configs := []*KConfig{
				{"CONFIG_LIBUKTIME", &v, CONFIG},
			}
			items = SetConfig(configs, kConfigMap, items)
		}
	case "CONFIG_UKSYSINFO":
		if u.Contains(matchedLibs, UKSYSINFO) {
			configs := []*KConfig{
				{"CONFIG_UKSYSINFO", &v, CONFIG},
			}
			items = SetConfig(configs, kConfigMap, items)
		}
	case "CONFIG_POSIX_LIBDL":
		if u.Contains(matchedLibs, POSIXLIBDL) {
			configs := []*KConfig{
				{"CONFIG_POSIX_LIBDL", &v, CONFIG},
			}
			items = SetConfig(configs, kConfigMap, items)
		}
	case "CONFIG_LIBVFSCORE":
		if u.Contains(matchedLibs, VFSCORE) {
			n := "16"
			configs := []*KConfig{
				{"CONFIG_LIBVFSCORE", &v, CONFIG},
				{"CONFIG_LIBRAMFS", nil, COMMENTEDCONFIG},
				{"CONFIG_LIBDEVFS", &v, CONFIG},
				{"CONFIG_LIBDEVFS_USE_RAMFS", nil, COMMENTEDCONFIG},
				{"#", nil, SEPARATOR},
				{"# vfscore configuration", nil, HEADER},
				{"#", nil, SEPARATOR},
				{"CONFIG_LIBVFSCORE_PIPE_SIZE_ORDER", &n, CONFIG},
				{"CONFIG_LIBVFSCORE_AUTOMOUNT_ROOTFS", nil, COMMENTEDCONFIG},
			}
			items = SetConfig(configs, kConfigMap, items)
		}
	case "CONFIG_LIBNEWLIBC":
		if u.Contains(matchedLibs, NEWLIB) {
			configs := []*KConfig{
				{"CONFIG_HAVE_LIBC", &v, CONFIG},
				{"CONFIG_LIBNEWLIBC", &v, CONFIG},
				{"CONFIG_LIBNEWLIBM", &v, CONFIG},
				{"CONFIG_LIBNEWLIBC_WANT_IO_C99_FORMATS", nil, COMMENTEDCONFIG},
				{"CONFIG_LIBNEWLIBC_LINUX_ERRNO_EXTENSIONS", nil, COMMENTEDCONFIG},
			}
			items = SetConfig(configs, kConfigMap, items)
		}
	case "CONFIG_LIBPTHREAD_EMBEDDED":
		if u.Contains(matchedLibs, PTHREADEMBEDDED) {
			number := "32"
			configs := []*KConfig{
				{"CONFIG_LIBPTHREAD_EMBEDDED", &v, CONFIG},
				{"CONFIG_LIBPTHREAD_EMBEDDED_MAX_SIMUL_THREADS", &number, CONFIG},
				{"CONFIG_LIBPTHREAD_EMBEDDED_MAX_TLS", &number, CONFIG},
				{"CONFIG_LIBPTHREAD_EMBEDDED_UTEST", nil, COMMENTEDCONFIG},
			}
			items = SetConfig(configs, kConfigMap, items)
		}
	case "CONFIG_LIBLWIP":
		if u.Contains(matchedLibs, LWIP) {
			seed, queues := "23", "1"
			mss, dnsMaxServer, dnsTableSize := "1460", "2", "32"
			configs := []*KConfig{
				{"CONFIG_VIRTIO_NET", &v, CONFIG},
				//
				{"CONFIG_LIBUKMPI", &v, CONFIG},
				{"CONFIG_LIBUKMPI_MBOX", &v, CONFIG},
				//
				{"CONFIG_LIBUKSWRAND", &v, CONFIG},
				{"CONFIG_LIBUKSWRAND_MWC", &v, CONFIG},
				{"CONFIG_LIBUKSWRAND_INITIALSEED", &seed, CONFIG},
				//
				{"CONFIG_LIBUKNETDEV", &v, CONFIG},
				{"CONFIG_LIBUKNETDEV_MAXNBQUEUES", &queues, CONFIG},
				{"CONFIG_LIBUKNETDEV_DISPATCHERTHREADS", &v, CONFIG},
				//
				{"CONFIG_LIBLWIP", &v, CONFIG},
				{"#", nil, SEPARATOR},
				{"# Netif drivers", nil, HEADER},
				{"#", nil, SEPARATOR},
				{"CONFIG_LWIP_UKNETDEV", &v, CONFIG},
				{"CONFIG_LWIP_AUTOIFACE", &v, CONFIG},
				{"CONFIG_LWIP_NOTHREADS", nil, COMMENTEDCONFIG},
				{"CONFIG_LWIP_THREADS", &v, CONFIG},
				{"CONFIG_LWIP_HEAP", &v, CONFIG},
				{"CONFIG_LWIP_NETIF_EXT_STATUS_CALLBACK", &v, CONFIG},
				{"CONFIG_LWIP_NETIF_STATUS_PRINT", &v, CONFIG},
				{"CONFIG_LWIP_IPV4", &v, CONFIG},
				{"CONFIG_LWIP_IPV6", nil, COMMENTEDCONFIG},
				{"CONFIG_LWIP_UDP", &v, CONFIG},
				{"CONFIG_LWIP_TCP", &v, CONFIG},
				{"CONFIG_LWIP_TCP_MSS", &mss, CONFIG},
				{"CONFIG_LWIP_WND_SCALE", &v, CONFIG},
				{"CONFIG_LWIP_TCP_KEEPALIVE", nil, COMMENTEDCONFIG},
				{"CONFIG_LWIP_TCP_TIMESTAMPS", nil, COMMENTEDCONFIG},
				{"CONFIG_LWIP_ICMP", &v, CONFIG},
				{"CONFIG_LWIP_IGMP", nil, COMMENTEDCONFIG},
				{"CONFIG_LWIP_SNMP", nil, COMMENTEDCONFIG},
				{"CONFIG_LWIP_DHCP", nil, COMMENTEDCONFIG},
				{"CONFIG_LWIP_DNS", &v, CONFIG},
				{"CONFIG_LWIP_DNS_MAX_SERVERS", &dnsMaxServer, CONFIG},
				{"CONFIG_LWIP_DNS_TABLE_SIZE", &dnsTableSize, CONFIG},
				{"CONFIG_LWIP_SOCKET", &v, CONFIG},
				{"CONFIG_LWIP_DEBUG", nil, COMMENTEDCONFIG},
			}
			items = SetConfig(configs, kConfigMap, items)
		}
	}

	return items
}

// matchLibsKconfig performs the matching between Kconfig entries and micro-libs
// and updates the right Kconfigs
//
// It returns a list of KConfig.
func addInternalConfig(conf string, kConfigMap map[string]*KConfig, items []*KConfig) []*KConfig {
	v := "y"
	switch conf {
	case "CONFIG_PLAT_XEN":
		configs := []*KConfig{
			{"CONFIG_PLAT_XEN", &v, CONFIG},
			{"CONFIG_XEN_HVMLITE", nil, COMMENTEDCONFIG},
			{"", nil, LINEFEED},
			{"#", nil, SEPARATOR},
			{"# Console Options", nil, HEADER},
			{"#", nil, SEPARATOR},
			{"CONFIG_XEN_KERNEL_HV_CONSOLE", &v, CONFIG},
			{"CONFIG_XEN_KERNEL_EMG_CONSOLE", nil, COMMENTEDCONFIG},
			{"CONFIG_XEN_DEBUG_HV_CONSOLE", &v, CONFIG},
			{"CONFIG_XEN_DEBUG_EMG_CONSOLE", nil, COMMENTEDCONFIG},
			{"CONFIG_XEN_PV_BUILD_P2M", &v, CONFIG},
			{"CONFIG_XEN_GNTTAB", &v, CONFIG},
			{"CONFIG_XEN_XENBUS", nil, COMMENTEDCONFIG},
		}
		items = SetConfig(configs, kConfigMap, items)
	case "CONFIG_PLAT_KVM":
		configs := []*KConfig{
			{"CONFIG_PLAT_KVM", &v, CONFIG},
			{"", nil, LINEFEED},
			{"#", nil, SEPARATOR},
			{"# Console Options", nil, HEADER},
			{"#", nil, SEPARATOR},
			{"CONFIG_KVM_KERNEL_SERIAL_CONSOLE", &v, CONFIG},
			{"CONFIG_KVM_KERNEL_VGA_CONSOLE", &v, CONFIG},
			{"CONFIG_KVM_DEBUG_SERIAL_CONSOLE", &v, CONFIG},
			{"CONFIG_KVM_DEBUG_VGA_CONSOLE", &v, CONFIG},
			{"CONFIG_KVM_PCI", &v, CONFIG},
			{"CONFIG_VIRTIO_BUS", &v, CONFIG},
			{"", nil, LINEFEED},
			{"#", nil, SEPARATOR},
			{"# Virtio", nil, HEADER},
			{"#", nil, SEPARATOR},
			{"CONFIG_VIRTIO_PCI", nil, COMMENTEDCONFIG},
			{"CONFIG_VIRTIO_NET", nil, COMMENTEDCONFIG},
		}
		items = SetConfig(configs, kConfigMap, items)
	case "CONFIG_PLAT_LINUXU":
		heapSize := "4"
		configs := []*KConfig{
			{"CONFIG_PLAT_LINUXU", &v, CONFIG},
			{"CONFIG_LINUXU_DEFAULT_HEAPMB", &heapSize, CONFIG},
		}
		items = SetConfig(configs, kConfigMap, items)
	case "CONFIG_LIBUKBOOT":
		var number = "60"
		configs := []*KConfig{
			{"CONFIG_LIBUKBOOT", &v, CONFIG},
			{"CONFIG_LIBUKBOOT_BANNER", &v, CONFIG},
			{"CONFIG_LIBUKBOOT_MAXNBARGS", &number, CONFIG},
			{"CONFIG_LIBUKBOOT_INITALLOC", &v, CONFIG},
			{"CONFIG_LIBUKDEBUG", &v, CONFIG},
			{"CONFIG_LIBUKDEBUG_PRINTK", &v, CONFIG},
			{"CONFIG_LIBUKDEBUG_PRINTK_INFO", &v, CONFIG},

			{"CONFIG_LIBUKDEBUG_PRINTK_WARN", nil, COMMENTEDCONFIG},
			{"CONFIG_LIBUKDEBUG_PRINTK_ERR", nil, COMMENTEDCONFIG},
			{"CONFIG_LIBUKDEBUG_PRINTK_CRIT", nil, COMMENTEDCONFIG},
			{"CONFIG_LIBUKDEBUG_PRINTD", nil, COMMENTEDCONFIG},
			{"CONFIG_LIBUKDEBUG_NOREDIR", nil, COMMENTEDCONFIG},
			{"CONFIG_LIBUKDEBUG_REDIR_PRINTD", nil, COMMENTEDCONFIG},
			{"CONFIG_LIBUKDEBUG_REDIR_PRINTK", nil, COMMENTEDCONFIG},
			{"CONFIG_LIBUKDEBUG_PRINT_TIME", nil, COMMENTEDCONFIG},
			{"CONFIG_LIBUKDEBUG_PRINT_STACK", nil, COMMENTEDCONFIG},
			{"CONFIG_LIBUKDEBUG_ENABLE_ASSERT", nil, COMMENTEDCONFIG},
			{"CONFIG_LIBUKDEBUG_TRACEPOINTS", nil, COMMENTEDCONFIG},
		}
		items = SetConfig(configs, kConfigMap, items)
	case "CONFIG_LIBNOLIBC":
		configs := []*KConfig{
			{"CONFIG_LIBNOLIBC", nil, COMMENTEDCONFIG},
			{"CONFIG_LIBNOLIBC_UKDEBUG_ASSERT", nil, COMMENTEDCONFIG},
		}
		items = SetConfig(configs, kConfigMap, items)
	case "CONFIG_LIBUKALLOC":
		configs := []*KConfig{
			{"CONFIG_LIBUKALLOC", &v, CONFIG},
			{"CONFIG_LIBUKALLOC_IFPAGES", &v, CONFIG},
			{"CONFIG_LIBUKALLOC_IFSTATS", nil, COMMENTEDCONFIG},
			{"CONFIG_LIBUKALLOCBBUDDY", &v, CONFIG},
		}
		items = SetConfig(configs, kConfigMap, items)
	case "CONFIG_LIBUKSCHED":
		configs := []*KConfig{
			{"CONFIG_LIBUKSCHED", &v, CONFIG},
			{"CONFIG_LIBUKSCHEDCOOP", &v, CONFIG},
		}
		items = SetConfig(configs, kConfigMap, items)
	case "CONFIG_LIBUKMPI":
		configs := []*KConfig{
			{"CONFIG_LIBUKMPI", nil, COMMENTEDCONFIG},
			{"CONFIG_LIBUKMPI_MBOX", nil, COMMENTEDCONFIG},
		}
		items = SetConfig(configs, kConfigMap, items)
	case "CONFIG_LIBUKSWRAND":
		configs := []*KConfig{
			{"CONFIG_LIBUKSWRAND_MWC", nil, COMMENTEDCONFIG},
			{"CONFIG_LIBUKSWRAND_INITIALSEED", nil, COMMENTEDCONFIG},
			{"CONFIG_DEV_RANDOM", nil, COMMENTEDCONFIG},
		}
		items = SetConfig(configs, kConfigMap, items)
	case "CONFIG_LIBUKNETDEV":
		configs := []*KConfig{
			{"CONFIG_LIBUKNETDEV_MAXNBQUEUES", nil, COMMENTEDCONFIG},
			{"CONFIG_LIBUKNETDEV_DISPATCHERTHREADS", nil, COMMENTEDCONFIG},
		}
		items = SetConfig(configs, kConfigMap, items)
	case "CONFIG_LIBUKLOCK":
		configs := []*KConfig{
			{"CONFIG_LIBUKLOCK", &v, CONFIG},
			{"CONFIG_LIBUKLOCK_SEMAPHORE", &v, CONFIG},
			{"CONFIG_LIBUKLOCK_MUTEX", &v, CONFIG},
		}
		items = SetConfig(configs, kConfigMap, items)
	}

	return items
}
