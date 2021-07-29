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
	"os"
	"text/tabwriter"
	u "github.com/unikraft/kraft/contrib/common"
)

type RelaTables struct {
	nbEntries int
	name      string
	dataRela  []*dataRela
}

type dataRela struct {
	name      *string
	elf64Rela Elf64Rela
}

type Elf64Rela struct {
	Offset      uint64
	Type        uint32
	SymbolIndex uint32
	Addend      int64
}

func (elfFile *ELF64File) addRela(index int, relas []Elf64Rela) error {

	var relocationTables RelaTables
	relocationTables.nbEntries = len(relas)
	relocationTables.name = elfFile.SectionsTable.DataSect[index].Name
	relocationTables.dataRela = make([]*dataRela, relocationTables.nbEntries)

	for i := range relas {

		relocationTables.dataRela[i] = &dataRela{
			elf64Rela: relas[i],
			name:      nil,
		}
	}

	elfFile.RelaTables = append(elfFile.RelaTables, relocationTables)

	return nil
}

func (elfFile *ELF64File) parseRelocations(index int) error {

	content, err := elfFile.GetSectionContent(uint16(index))

	if err != nil {
		return fmt.Errorf("failed reading relocation table: %s", err)
	}

	rela := make([]Elf64Rela, len(content)/binary.Size(Elf64Rela{}))
	if err := binary.Read(bytes.NewReader(content),
		elfFile.Endianness, rela); err != nil {
		return err
	}

	if err := elfFile.addRela(index, rela); err != nil {
		return err
	}

	return nil
}

func (elfFile *ELF64File) resolveRelocSymbolsName() error {
	for _, table := range elfFile.RelaTables {
		for _, s := range table.dataRela {
			t := 0
			if s.elf64Rela.Type == uint32(elf.R_X86_64_JMP_SLOT) ||
				s.elf64Rela.Type == uint32(elf.R_X86_64_GLOB_DAT) ||
				s.elf64Rela.Type == uint32(elf.R_X86_64_COPY) &&
					len(elfFile.SymbolsTables) > 1 {
				t++
			}

			symName, err := elfFile.SymbolsTables[t].getSymbolName(s.elf64Rela.SymbolIndex)
			if err != nil {
				return err
			}
			s.name = &symName
		}
	}
	return nil
}

func (table *RelaTables) displayRelocations(w *tabwriter.Writer) {
	_, _ = fmt.Fprintf(w, "\nRelocation section '%s' contains %d entries:\n",
		table.name, table.nbEntries)
	_, _ = fmt.Fprintln(w, "Offset\tInfo\tType\tValue")
	for _, r := range table.dataRela {
		_, _ = fmt.Fprintf(w, "%.6x\t%.6d\t%s\t%s %x\n",
			r.elf64Rela.Offset, r.elf64Rela.SymbolIndex,
			rx86_64Strings[r.elf64Rela.Type], *r.name,
			r.elf64Rela.Addend)
	}
}

func (elfFile *ELF64File) DisplayRelocationTables() {

	if len(elfFile.RelaTables) == 0 {
		u.PrintWarning("Relocation table(s) are empty")
		return
	}

	w := new(tabwriter.Writer)
	w.Init(os.Stdout, 0, 8, 0, '\t', 0)
	fmt.Println("-----------------------------------------------------------------------")

	for _, table := range elfFile.RelaTables {
		table.displayRelocations(w)
	}
	_ = w.Flush()
}
