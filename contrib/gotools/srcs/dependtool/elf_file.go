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

import (
	"debug/elf"
	"os"
)

// getElf reads and decodes an ELF file.
//
// It returns a pointer to an ELF file and an error if any, otherwise it
// returns nil.
func getElf(filename string) (*elf.File, error) {
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
