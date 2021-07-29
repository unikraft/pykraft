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
	"bytes"
	"debug/elf"
	"encoding/binary"
	"fmt"
	u "github.com/unikraft/kraft/contrib/common"
	"os"
	"strings"
	"text/tabwriter"
)

type SectionsTable struct {
	NbEntries int
	Name      string
	DataSect  []*DataSections
}

type DataSections struct {
	Name         string
	Elf64section ELF64SectionHeader
}

type ELF64SectionHeader struct {
	Name           uint32
	Type           uint32
	Flags          uint64
	VirtualAddress uint64
	FileOffset     uint64
	Size           uint64
	LinkedIndex    uint32
	Info           uint32
	Align          uint64
	EntrySize      uint64
}

func (elfFile *ELF64File) addSection(sections []ELF64SectionHeader) error {

	elfFile.SectionsTable = SectionsTable{}
	elfFile.SectionsTable.NbEntries = len(sections)
	elfFile.SectionsTable.DataSect = make([]*DataSections,
		elfFile.SectionsTable.NbEntries)

	for i := len(sections) - 1; i >= 0; i-- {
		elfFile.SectionsTable.DataSect[i] = &DataSections{
			Elf64section: sections[i],
		}
		nameString, err := elfFile.GetSectionName(elfFile.SectionsTable.DataSect[i].Elf64section.Name, elfFile.Header.SectionNamesTable)
		if err != nil {
			return err
		}
		elfFile.SectionsTable.DataSect[i].Name = nameString
	}

	return nil
}

func (elfFile *ELF64File) ParseSectionHeaders() error {

	offset := elfFile.Header.SectionHeaderOffset
	if offset >= uint64(len(elfFile.Raw)) {
		return fmt.Errorf("invalid elf64section header offset: 0x%x", offset)
	}

	data := bytes.NewReader(elfFile.Raw[offset:])

	sections := make([]ELF64SectionHeader, elfFile.Header.SectionHeaderEntries)
	err := binary.Read(data, elfFile.Endianness, sections)
	if err != nil {
		return fmt.Errorf("failed reading elf64section header table: %s", err)
	}

	if err := elfFile.addSection(sections); err != nil {
		return err
	}
	return nil
}

func (elfFile *ELF64File) GetSectionContent(sectionIndex uint16) ([]byte, error) {

	sectionTable := elfFile.SectionsTable.DataSect
	if int(sectionIndex) > len(sectionTable) {
		return nil, fmt.Errorf("invalid elf64section index: %d", sectionIndex)
	}

	start := sectionTable[sectionIndex].Elf64section.FileOffset
	if start > uint64(len(elfFile.Raw)) {
		return nil, fmt.Errorf("bad file offset for elf64section %d", sectionIndex)
	}

	end := start + sectionTable[sectionIndex].Elf64section.Size
	if (end > uint64(len(elfFile.Raw))) || (end < start) {
		return nil, fmt.Errorf("bad size for elf64section %d", sectionIndex)
	}

	return elfFile.Raw[start:end], nil
}

func (elfFile *ELF64File) GetSectionName(indexString uint32, indexStringTable uint16) (string, error) {

	rawDataStringTable, err := elfFile.GetSectionContent(indexStringTable)
	if err != nil {
		return "", err
	}

	rawDataStart := rawDataStringTable[indexString:]

	return string(rawDataStart[:bytes.IndexByte(rawDataStart, 0)]), nil
}

func (elfFile *ELF64File) ParseSections() error {

	elfFile.IndexSections = make(map[string]int, 0)
	elfFile.FunctionsTables = make([]FunctionTables, 0)
	elfFile.TextSectionIndex = make([]int, 0)

	for i := 0; i < len(elfFile.SectionsTable.DataSect)-1; i++ {
		sectionName := elfFile.SectionsTable.DataSect[i].Name
		elfFile.IndexSections[sectionName] = i
		typeSection := elfFile.SectionsTable.DataSect[i].Elf64section.Type
		switch typeSection {
		case uint32(elf.SHT_SYMTAB):
			if err := elfFile.parseSymbolsTable(i); err != nil {
				return err
			}
		case uint32(elf.SHT_RELA):
			if err := elfFile.parseRelocations(i); err != nil {
				return err
			}
		case uint32(elf.SHT_DYNAMIC):
			if err := elfFile.parseDynamic(i); err != nil {
				return err
			}
		case uint32(elf.SHT_DYNSYM):
			if err := elfFile.parseSymbolsTable(i); err != nil {
				return err
			}
		case uint32(elf.SHT_NOTE):
			if err := elfFile.parseNote(i); err != nil {
				return err
			}
		default:

		}

		if strings.Contains(sectionName, TextSection) {
			elfFile.FunctionsTables = append(elfFile.FunctionsTables, FunctionTables{
				Name:      sectionName,
				NbEntries: 0,
				Functions: nil,
			})

			if typeSection != uint32(elf.SHT_RELA) {
				elfFile.TextSectionIndex = append(elfFile.TextSectionIndex, i)
			}
		}
	}

	return elfFile.resolveRelocSymbolsName()
}

func (table *SectionsTable) DisplaySections() {

	if table.DataSect == nil || len(table.DataSect) == 0 {
		u.PrintWarning("Section table(s) are empty")
		return
	}

	w := new(tabwriter.Writer)
	w.Init(os.Stdout, 0, 8, 0, '\t', 0)
	fmt.Println("-----------------------------------------------------------------------")
	_, _ = fmt.Fprintln(w, "Nr\tName\tType\tAddress\tOffset\tSize")
	for i, s := range table.DataSect {
		_, _ = fmt.Fprintf(w, "[%d]\t%s\t%s\t%.6x\t%.6x\t%.6x\n", i,
			s.Name, shtStrings[s.Elf64section.Type],
			s.Elf64section.VirtualAddress, s.Elf64section.FileOffset,
			s.Elf64section.Size)
	}
	_ = w.Flush()
}
