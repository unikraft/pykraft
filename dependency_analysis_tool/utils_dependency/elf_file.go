// Copyright 2019 The UNICORE Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file
//
// Author: Gaulthier Gain <gaulthier.gain@uliege.be>

package utils_dependency

import (
	"debug/elf"
	"os"
)

// GetElf reads and decodes an ELF file.
//
// It returns a pointer to an ELF file and an error if any, otherwise it
// returns nil.
func GetElf(filename string) (*elf.File, error) {
	f, err := os.Open(filename)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	_elf, err := elf.NewFile(f)
	if err != nil {
		return nil, err
	}

	// Read and decode ELF identifier
	var ident [16]uint8
	_, err = f.ReadAt(ident[0:], 0)
	if err != nil {
		return nil, err
	}

	// Check the type
	if ident[0] != '\x7f' || ident[1] != 'E' || ident[2] != 'L' || ident[3] != 'F' {
		return nil, nil
	}

	return _elf, nil
}

// GetElfArchitecture gets the ELF architecture.
//
// It returns a string that defines the ELF class and a string that defines the
// Machine type.
func GetElfArchitecture(elf *elf.File) (string, string) {
	var arch, mach string

	switch elf.Class.String() {
	case "ELFCLASS64":
		arch = "64 bits"
	case "ELFCLASS32":
		arch = "32 bits"
	}

	switch elf.Machine.String() {
	case "EM_AARCH64":
		mach = "ARM64"
	case "EM_386":
		mach = "x86"
	case "EM_X86_64":
		mach = "x86_64"
	}

	return arch, mach
}
