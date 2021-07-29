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
	"text/tabwriter"
)

type DynamicTable struct {
	nbEntries int
	name      string
	elf64dyn  []Elf64Dynamic
}

type Elf64Dynamic struct {
	Tag   uint64
	Value uint64
}

func (elfFile *ELF64File) addDynamicEntry(index int, dynEntries []Elf64Dynamic) error {

	elfFile.DynamicTable = DynamicTable{}
	elfFile.DynamicTable.nbEntries = len(dynEntries)
	elfFile.DynamicTable.name = elfFile.SectionsTable.DataSect[index].Name
	elfFile.DynamicTable.elf64dyn = make([]Elf64Dynamic, 0)

	for _, s := range dynEntries {
		elfFile.DynamicTable.elf64dyn = append(elfFile.DynamicTable.elf64dyn, s)
		if s.Tag == uint64(elf.DT_NULL) {
			return nil
		}
	}
	return nil
}

func (elfFile *ELF64File) parseDynamic(index int) error {

	content, err := elfFile.GetSectionContent(uint16(index))

	if err != nil {
		return fmt.Errorf("failed reading relocation table: %s", err)
	}

	dynEntries := make([]Elf64Dynamic, len(content)/binary.Size(Elf64Dynamic{}))
	if err := binary.Read(bytes.NewReader(content),
		elfFile.Endianness, dynEntries); err != nil {
		return err
	}

	if err := elfFile.addDynamicEntry(index, dynEntries); err != nil {
		return err
	}

	return nil
}

func (table *DynamicTable) DisplayDynamicEntries() {

	if len(table.elf64dyn) == 0 {
		u.PrintWarning("Dynamic table is empty")
		return
	}

	w := new(tabwriter.Writer)
	w.Init(os.Stdout, 0, 8, 0, '\t', 0)
	fmt.Println("-----------------------------------------------------------------------")

	fmt.Printf("%s table contains %d entries:\n\n", table.name, table.nbEntries)
	_, _ = fmt.Fprintln(w, "Nr\tTag\tType\tValue")
	for i, s := range table.elf64dyn {
		_, _ = fmt.Fprintf(w, "%d:\t%.8x\t%s\t%x\n", i, s.Tag,
			dtStrings[s.Tag], s.Value)
	}
	_ = w.Flush()
}
