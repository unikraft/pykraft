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

package main

import (
	"bufio"
	"io"
	"os"
	"strings"
	u "github.com/unikraft/kraft/contrib/common"
)

const (
	configLine          = iota // Config <CONFIG_.*> = <value>
	commentedConfigLine        // Commented config: # <CONFIG_.*> is not set
	headerLine                 // Header: # <.*>
	separatorLine              // Separator: #
	lineFeed                   // Line FEED: \n
)

// Exported struct that represents a Kconfig entry.
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
		case configLine:
			config = kConfig.Config + "=" + *kConfig.Value
		case commentedConfigLine:
			config = "# " + kConfig.Config + " is not set"
		case headerLine:
			config = kConfig.Config
		case separatorLine:
			config = "#"
		case lineFeed:
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
// It returns a list of KConfig. This list will be saved into a '.config'
// file.
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
		typeConfig = commentedConfigLine
	case strings.HasPrefix(line, "#") && len(line) > 2: // Separator: #
		config = strings.TrimSuffix(line, "\n")
		value = nil
		typeConfig = headerLine
	case strings.HasPrefix(line, "#") && len(line) == 2: // Header: # <.*>
		config, value = "#", nil
		typeConfig = separatorLine
	case strings.Contains(line, "="): // Config: <CONFIG_.*> = y
		split := strings.Split(line, "=")
		config = split[0]
		word := strings.TrimSuffix(split[1], "\n")
		value = &word
		typeConfig = configLine
	default: // Line FEED
		config, value = "#", nil
		typeConfig = lineFeed
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
func updateConfig(kConfigMap map[string]*KConfig,
	items []*KConfig) []*KConfig {
	v := "y"
	var configs = []*KConfig{
		// CONFIG libs
		{"CONFIG_HAVE_BOOTENTRY", &v, configLine},
		{"CONFIG_HAVE_SCHED", &v, configLine},
		{"CONFIG_LIBUKARGPARSE", &v, configLine},
		{"CONFIG_LIBUKBUS", &v, configLine},
		{"CONFIG_LIBUKSGLIST", &v, configLine},
		{"CONFIG_LIBUKTIMECONV", &v, configLine},

		// CONFIG build
		{"CONFIG_OPTIMIZE_NONE", &v, configLine},
		{"CONFIG_OPTIMIZE_PERF", nil, commentedConfigLine},
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
				{"CONFIG_LIBPOSIX_PROCESS", &v, configLine},
			}
			items = SetConfig(configs, kConfigMap, items)
		}
	case "CONFIG_LIBPOSIX_USER":
		if u.Contains(matchedLibs, POSIXUSER) {
			configs := []*KConfig{
				{"CONFIG_LIBPOSIX_USER", &v, configLine},
			}
			items = SetConfig(configs, kConfigMap, items)
		}
	case "CONFIG_LIBSYSCALL_SHIM":
		if u.Contains(matchedLibs, SYSCALLSHIM) {
			configs := []*KConfig{
				{"CONFIG_LIBSYSCALL_SHIM", &v, configLine},
			}
			items = SetConfig(configs, kConfigMap, items)
		}
	case "CONFIG_LIBUKTIME":
		if u.Contains(matchedLibs, UKTIME) {
			configs := []*KConfig{
				{"CONFIG_LIBUKTIME", &v, configLine},
			}
			items = SetConfig(configs, kConfigMap, items)
		}
	case "CONFIG_UKSYSINFO":
		if u.Contains(matchedLibs, UKSYSINFO) {
			configs := []*KConfig{
				{"CONFIG_UKSYSINFO", &v, configLine},
			}
			items = SetConfig(configs, kConfigMap, items)
		}
	case "CONFIG_POSIX_LIBDL":
		if u.Contains(matchedLibs, POSIXLIBDL) {
			configs := []*KConfig{
				{"CONFIG_POSIX_LIBDL", &v, configLine},
			}
			items = SetConfig(configs, kConfigMap, items)
		}
	case "CONFIG_LIBVFSCORE":
		if u.Contains(matchedLibs, VFSCORE) {
			n := "16"
			configs := []*KConfig{
				{"CONFIG_LIBVFSCORE", &v, configLine},
				{"CONFIG_LIBRAMFS", nil, commentedConfigLine},
				{"CONFIG_LIBDEVFS", &v, configLine},
				{"CONFIG_LIBDEVFS_USE_RAMFS", nil, commentedConfigLine},
				{"#", nil, separatorLine},
				{"# vfscore configuration", nil, headerLine},
				{"#", nil, separatorLine},
				{"CONFIG_LIBVFSCORE_PIPE_SIZE_ORDER", &n, configLine},
				{"CONFIG_LIBVFSCORE_AUTOMOUNT_ROOTFS", nil, commentedConfigLine},
			}
			items = SetConfig(configs, kConfigMap, items)
		}
	case "CONFIG_LIBNEWLIBC":
		if u.Contains(matchedLibs, NEWLIB) {
			configs := []*KConfig{
				{"CONFIG_HAVE_LIBC", &v, configLine},
				{"CONFIG_LIBNEWLIBC", &v, configLine},
				{"CONFIG_LIBNEWLIBM", &v, configLine},
				{"CONFIG_LIBNEWLIBC_WANT_IO_C99_FORMATS", nil, commentedConfigLine},
				{"CONFIG_LIBNEWLIBC_LINUX_ERRNO_EXTENSIONS", nil, commentedConfigLine},
			}
			items = SetConfig(configs, kConfigMap, items)
		}
	case "CONFIG_LIBPTHREAD_EMBEDDED":
		if u.Contains(matchedLibs, PTHREADEMBEDDED) {
			number := "32"
			configs := []*KConfig{
				{"CONFIG_LIBPTHREAD_EMBEDDED", &v, configLine},
				{"CONFIG_LIBPTHREAD_EMBEDDED_MAX_SIMUL_THREADS", &number, configLine},
				{"CONFIG_LIBPTHREAD_EMBEDDED_MAX_TLS", &number, configLine},
				{"CONFIG_LIBPTHREAD_EMBEDDED_UTEST", nil, commentedConfigLine},
			}
			items = SetConfig(configs, kConfigMap, items)
		}
	case "CONFIG_LIBLWIP":
		if u.Contains(matchedLibs, LWIP) {
			seed, queues := "23", "1"
			mss, dnsMaxServer, dnsTableSize := "1460", "2", "32"
			configs := []*KConfig{
				{"CONFIG_VIRTIO_NET", &v, configLine},
				//
				{"CONFIG_LIBUKMPI", &v, configLine},
				{"CONFIG_LIBUKMPI_MBOX", &v, configLine},
				//
				{"CONFIG_LIBUKSWRAND", &v, configLine},
				{"CONFIG_LIBUKSWRAND_MWC", &v, configLine},
				{"CONFIG_LIBUKSWRAND_INITIALSEED", &seed, configLine},
				//
				{"CONFIG_LIBUKNETDEV", &v, configLine},
				{"CONFIG_LIBUKNETDEV_MAXNBQUEUES", &queues, configLine},
				{"CONFIG_LIBUKNETDEV_DISPATCHERTHREADS", &v, configLine},
				//
				{"CONFIG_LIBLWIP", &v, configLine},
				{"#", nil, separatorLine},
				{"# Netif drivers", nil, headerLine},
				{"#", nil, separatorLine},
				{"CONFIG_LWIP_UKNETDEV", &v, configLine},
				{"CONFIG_LWIP_AUTOIFACE", &v, configLine},
				{"CONFIG_LWIP_NOTHREADS", nil, commentedConfigLine},
				{"CONFIG_LWIP_THREADS", &v, configLine},
				{"CONFIG_LWIP_HEAP", &v, configLine},
				{"CONFIG_LWIP_NETIF_EXT_STATUS_CALLBACK", &v, configLine},
				{"CONFIG_LWIP_NETIF_STATUS_PRINT", &v, configLine},
				{"CONFIG_LWIP_IPV4", &v, configLine},
				{"CONFIG_LWIP_IPV6", nil, commentedConfigLine},
				{"CONFIG_LWIP_UDP", &v, configLine},
				{"CONFIG_LWIP_TCP", &v, configLine},
				{"CONFIG_LWIP_TCP_MSS", &mss, configLine},
				{"CONFIG_LWIP_WND_SCALE", &v, configLine},
				{"CONFIG_LWIP_TCP_KEEPALIVE", nil, commentedConfigLine},
				{"CONFIG_LWIP_TCP_TIMESTAMPS", nil, commentedConfigLine},
				{"CONFIG_LWIP_ICMP", &v, configLine},
				{"CONFIG_LWIP_IGMP", nil, commentedConfigLine},
				{"CONFIG_LWIP_SNMP", nil, commentedConfigLine},
				{"CONFIG_LWIP_DHCP", nil, commentedConfigLine},
				{"CONFIG_LWIP_DNS", &v, configLine},
				{"CONFIG_LWIP_DNS_MAX_SERVERS", &dnsMaxServer, configLine},
				{"CONFIG_LWIP_DNS_TABLE_SIZE", &dnsTableSize, configLine},
				{"CONFIG_LWIP_SOCKET", &v, configLine},
				{"CONFIG_LWIP_DEBUG", nil, commentedConfigLine},
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
func addInternalConfig(conf string, kConfigMap map[string]*KConfig,
	items []*KConfig) []*KConfig {
	v := "y"
	switch conf {
	case "CONFIG_PLAT_XEN":
		configs := []*KConfig{
			{"CONFIG_PLAT_XEN", &v, configLine},
			{"CONFIG_XEN_HVMLITE", nil, commentedConfigLine},
			{"", nil, lineFeed},
			{"#", nil, separatorLine},
			{"# Console Options", nil, headerLine},
			{"#", nil, separatorLine},
			{"CONFIG_XEN_KERNEL_HV_CONSOLE", &v, configLine},
			{"CONFIG_XEN_KERNEL_EMG_CONSOLE", nil, commentedConfigLine},
			{"CONFIG_XEN_DEBUG_HV_CONSOLE", &v, configLine},
			{"CONFIG_XEN_DEBUG_EMG_CONSOLE", nil, commentedConfigLine},
			{"CONFIG_XEN_PV_BUILD_P2M", &v, configLine},
			{"CONFIG_XEN_GNTTAB", &v, configLine},
			{"CONFIG_XEN_XENBUS", nil, commentedConfigLine},
		}
		items = SetConfig(configs, kConfigMap, items)
	case "CONFIG_PLAT_KVM":
		configs := []*KConfig{
			{"CONFIG_PLAT_KVM", &v, configLine},
			{"", nil, lineFeed},
			{"#", nil, separatorLine},
			{"# Console Options", nil, headerLine},
			{"#", nil, separatorLine},
			{"CONFIG_KVM_KERNEL_SERIAL_CONSOLE", &v, configLine},
			{"CONFIG_KVM_KERNEL_VGA_CONSOLE", &v, configLine},
			{"CONFIG_KVM_DEBUG_SERIAL_CONSOLE", &v, configLine},
			{"CONFIG_KVM_DEBUG_VGA_CONSOLE", &v, configLine},
			{"CONFIG_KVM_PCI", &v, configLine},
			{"CONFIG_VIRTIO_BUS", &v, configLine},
			{"", nil, lineFeed},
			{"#", nil, separatorLine},
			{"# Virtio", nil, headerLine},
			{"#", nil, separatorLine},
			{"CONFIG_VIRTIO_PCI", nil, commentedConfigLine},
			{"CONFIG_VIRTIO_NET", nil, commentedConfigLine},
		}
		items = SetConfig(configs, kConfigMap, items)
	case "CONFIG_PLAT_LINUXU":
		heapSize := "4"
		configs := []*KConfig{
			{"CONFIG_PLAT_LINUXU", &v, configLine},
			{"CONFIG_LINUXU_DEFAULT_HEAPMB", &heapSize, configLine},
		}
		items = SetConfig(configs, kConfigMap, items)
	case "CONFIG_LIBUKBOOT":
		var number = "60"
		configs := []*KConfig{
			{"CONFIG_LIBUKBOOT", &v, configLine},
			{"CONFIG_LIBUKBOOT_BANNER", &v, configLine},
			{"CONFIG_LIBUKBOOT_MAXNBARGS", &number, configLine},
			{"CONFIG_LIBUKBOOT_INITALLOC", &v, configLine},
			{"CONFIG_LIBUKDEBUG", &v, configLine},
			{"CONFIG_LIBUKDEBUG_PRINTK", &v, configLine},
			{"CONFIG_LIBUKDEBUG_PRINTK_INFO", &v, configLine},

			{"CONFIG_LIBUKDEBUG_PRINTK_WARN", nil, commentedConfigLine},
			{"CONFIG_LIBUKDEBUG_PRINTK_ERR", nil, commentedConfigLine},
			{"CONFIG_LIBUKDEBUG_PRINTK_CRIT", nil, commentedConfigLine},
			{"CONFIG_LIBUKDEBUG_PRINTD", nil, commentedConfigLine},
			{"CONFIG_LIBUKDEBUG_NOREDIR", nil, commentedConfigLine},
			{"CONFIG_LIBUKDEBUG_REDIR_PRINTD", nil, commentedConfigLine},
			{"CONFIG_LIBUKDEBUG_REDIR_PRINTK", nil, commentedConfigLine},
			{"CONFIG_LIBUKDEBUG_PRINT_TIME", nil, commentedConfigLine},
			{"CONFIG_LIBUKDEBUG_PRINT_STACK", nil, commentedConfigLine},
			{"CONFIG_LIBUKDEBUG_ENABLE_ASSERT", nil, commentedConfigLine},
			{"CONFIG_LIBUKDEBUG_TRACEPOINTS", nil, commentedConfigLine},
		}
		items = SetConfig(configs, kConfigMap, items)
	case "CONFIG_LIBNOLIBC":
		configs := []*KConfig{
			{"CONFIG_LIBNOLIBC", nil, commentedConfigLine},
			{"CONFIG_LIBNOLIBC_UKDEBUG_ASSERT", nil, commentedConfigLine},
		}
		items = SetConfig(configs, kConfigMap, items)
	case "CONFIG_LIBUKALLOC":
		configs := []*KConfig{
			{"CONFIG_LIBUKALLOC", &v, configLine},
			{"CONFIG_LIBUKALLOC_IFPAGES", &v, configLine},
			{"CONFIG_LIBUKALLOC_IFSTATS", nil, commentedConfigLine},
			{"CONFIG_LIBUKALLOCBBUDDY", &v, configLine},
		}
		items = SetConfig(configs, kConfigMap, items)
	case "CONFIG_LIBUKSCHED":
		configs := []*KConfig{
			{"CONFIG_LIBUKSCHED", &v, configLine},
			{"CONFIG_LIBUKSCHEDCOOP", &v, configLine},
		}
		items = SetConfig(configs, kConfigMap, items)
	case "CONFIG_LIBUKMPI":
		configs := []*KConfig{
			{"CONFIG_LIBUKMPI", nil, commentedConfigLine},
			{"CONFIG_LIBUKMPI_MBOX", nil, commentedConfigLine},
		}
		items = SetConfig(configs, kConfigMap, items)
	case "CONFIG_LIBUKSWRAND":
		configs := []*KConfig{
			{"CONFIG_LIBUKSWRAND_MWC", nil, commentedConfigLine},
			{"CONFIG_LIBUKSWRAND_INITIALSEED", nil, commentedConfigLine},
			{"CONFIG_DEV_RANDOM", nil, commentedConfigLine},
		}
		items = SetConfig(configs, kConfigMap, items)
	case "CONFIG_LIBUKNETDEV":
		configs := []*KConfig{
			{"CONFIG_LIBUKNETDEV_MAXNBQUEUES", nil, commentedConfigLine},
			{"CONFIG_LIBUKNETDEV_DISPATCHERTHREADS", nil, commentedConfigLine},
		}
		items = SetConfig(configs, kConfigMap, items)
	case "CONFIG_LIBUKLOCK":
		configs := []*KConfig{
			{"CONFIG_LIBUKLOCK", &v, configLine},
			{"CONFIG_LIBUKLOCK_SEMAPHORE", &v, configLine},
			{"CONFIG_LIBUKLOCK_MUTEX", &v, configLine},
		}
		items = SetConfig(configs, kConfigMap, items)
	}

	return items
}
