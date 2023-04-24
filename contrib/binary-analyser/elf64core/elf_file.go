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

package elf64core

import (
	"bufio"
	"encoding/binary"
	"os"
)

type ELF64File struct {
	Header           *ELF64Header
	SectionsTable    SectionsTable
	SegmentsTable    ProgramTable
	DynamicTable     DynamicTable
	SymbolsTables    []SymbolsTables
	RelaTables       []RelaTables
	NotesTables      []NotesTables
	FunctionsTables  []FunctionTables
	Raw              []byte
	IndexSections    map[string]int
	Name             string
	Endianness       binary.ByteOrder
	TextSectionIndex []int // slice since we can have several
}

func (elfFile *ELF64File) ReadElfBinaryFile(filename string) error {
	file, err := os.Open(filename)

	if err != nil {
		return err
	}
	defer file.Close()

	stats, statsErr := file.Stat()
	if statsErr != nil {
		return statsErr
	}

	var size = stats.Size()
	elfFile.Raw = make([]byte, size)

	buf := bufio.NewReader(file)
	_, err = buf.Read(elfFile.Raw)

	return err
}

func (elfFile *ELF64File) ParseAll(path, name string) error {

	elfFile.Name = name

	if err := elfFile.ReadElfBinaryFile(path + name); err != nil {
		return err
	}

	if err := elfFile.ParseElfHeader(); err != nil {
		return err
	}

	if err := elfFile.ParseSectionHeaders(); err != nil {
		return err
	}

	if err := elfFile.ParseSections(); err != nil {
		return err
	}

	if err := elfFile.ParseProgramHeaders(); err != nil {
		return err
	}

	if err := elfFile.parseFunctions(); err != nil {
		return err
	}

	return nil
}
