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

type SymbolsTables struct {
	nbEntries   int
	name        string
	dataSymbols []*dataSymbols
}

type dataSymbols struct {
	elf64sym   ELF64Symbols
	name       string
	TypeSymbol byte
}

type ELF64Symbols struct {
	Name  uint32
	Info  byte
	Other byte
	Shndx uint16
	Value uint64
	Size  uint64
}

func (elfFile *ELF64File) addSymbols(index int, symbols []ELF64Symbols) error {

	var symbolsTables SymbolsTables
	symbolsTables.nbEntries = len(symbols)
	symbolsTables.name = elfFile.SectionsTable.DataSect[index].Name
	symbolsTables.dataSymbols = make([]*dataSymbols, symbolsTables.nbEntries)

	var nameString string
	var err error
	for j, s := range symbols {

		if s.Info == byte(elf.STT_SECTION) {
			// This is a section, save its name
			nameString = elfFile.SectionsTable.DataSect[s.Shndx].Name
		} else {
			nameString, err = elfFile.GetSectionName(s.Name, uint16(index+1))
			if err != nil {
				return err
			}
		}

		symbolsTables.dataSymbols[j] = &dataSymbols{
			elf64sym:   s,
			name:       nameString,
			TypeSymbol: (s.Info) & 0xf,
		}
	}

	elfFile.SymbolsTables = append(elfFile.SymbolsTables, symbolsTables)

	return nil
}

func (elfFile *ELF64File) parseSymbolsTable(index int) error {

	content, err := elfFile.GetSectionContent(uint16(index))

	if err != nil {
		return fmt.Errorf("failed reading string table: %s", err)
	}

	if content[len(content)-1] != 0 {
		return fmt.Errorf("the string table isn't null-terminated")
	}

	symbols := make([]ELF64Symbols, len(content)/binary.Size(ELF64Symbols{}))
	if err := binary.Read(bytes.NewReader(content),
		elfFile.Endianness, symbols); err != nil {
		return err
	}

	if err := elfFile.addSymbols(index, symbols); err != nil {
		return err
	}

	return nil
}

func (table *SymbolsTables) displaySymbols(w *tabwriter.Writer) {
	_, _ = fmt.Fprintf(w, "\nSymbol table %s contains %d entries:\n\n",
		table.name, table.nbEntries)

	_, _ = fmt.Fprintf(w, "\nNum:\tValue\tSize\tName\tType\n")

	for i, s := range table.dataSymbols {
		_, _ = fmt.Fprintf(w, "%d:\t%.6x\t%d\t%s\t%s (%d)\n", i,
			s.elf64sym.Value, s.elf64sym.Size, s.name,
			sttStrings[s.TypeSymbol], s.TypeSymbol)
	}
}

func (elfFile *ELF64File) DisplaySymbolsTables() {

	if len(elfFile.SymbolsTables) == 0 {
		u.PrintWarning("Symbols table(s) are empty")
		return
	}

	w := new(tabwriter.Writer)
	w.Init(os.Stdout, 0, 8, 0, '\t', 0)
	fmt.Println("-----------------------------------------------------------------------")

	for _, table := range elfFile.SymbolsTables {
		table.displaySymbols(w)
	}
	_ = w.Flush()
}

func (table *SymbolsTables) getSymbolName(index uint32) (string, error) {
	if table.dataSymbols == nil {
		return "", fmt.Errorf("symbol table is empty")
	}

	if uint32(table.nbEntries) <= index {
		return "", fmt.Errorf("invalid index %d", index)
	}

	return table.dataSymbols[index].name, nil
}
