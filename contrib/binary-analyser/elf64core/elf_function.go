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
	"debug/elf"
	"errors"
	"fmt"
	u "github.com/unikraft/kraft/contrib/common"
	"os"
	"sort"
	"strings"
	"text/tabwriter"
)

type FunctionTables struct {
	Name      string
	NbEntries int
	Functions []ELF64Function
}

type ELF64Function struct {
	Name         string
	Addr         uint64
	Size         uint64
}

func (elfFile *ELF64File) getIndexFctTable(ndx uint16) int {

	if int(ndx) > len(elfFile.SectionsTable.DataSect) {
		return -1
	}

	sectionName := elfFile.SectionsTable.DataSect[ndx].Name
	for i, t := range elfFile.FunctionsTables {
		if strings.Compare(t.Name, sectionName) == 0 {
			return i
		}
	}

	return -1
}

func (elfFile *ELF64File) detectSizeSymbol(symbolsTable []ELF64Function, index int) uint64 {

	if index+1 == len(symbolsTable) {
		textIndex := elfFile.IndexSections[TextSection]
		textSection := elfFile.SectionsTable.DataSect[textIndex]
		size := textSection.Elf64section.FileOffset + textSection.Elf64section.Size
		return size - symbolsTable[index].Addr
	}
	return symbolsTable[index+1].Addr - symbolsTable[index].Addr
}

func (elfFile *ELF64File) inspectFunctions() error {

	for _, table := range elfFile.SymbolsTables {
		for _, s := range table.dataSymbols {
			k := elfFile.getIndexFctTable(s.elf64sym.Shndx)
			if k != -1 && s.elf64sym.Value > 0 {
				if !isInSlice(elfFile.Name, s.name) {
					function := ELF64Function{Name: s.name, Addr: s.elf64sym.Value,
						Size: s.elf64sym.Size}
					elfFile.FunctionsTables[k].Functions =
						append(elfFile.FunctionsTables[k].Functions, function)
				}
			} else if s.TypeSymbol == byte(elf.STT_FUNC) {
				// If it is a func where the start address starts at 0
				function := ELF64Function{Name: s.name, Addr: s.elf64sym.Value,
					Size: s.elf64sym.Size}
				elfFile.FunctionsTables[k].Functions =
					append(elfFile.FunctionsTables[k].Functions, function)
			}
		}
	}

	return nil
}

func (elfFile *ELF64File) parseFunctions() error {

	if _, ok := elfFile.IndexSections[TextSection]; ok {

		if err := elfFile.inspectFunctions(); err != nil {
			return err
		}

	} else {
		return errors.New("no text section detected")
	}

	for _, table := range elfFile.FunctionsTables {
		// sort Functions

		sort.Slice(table.Functions, func(i, j int) bool {
			return table.Functions[i].Addr < table.Functions[j].Addr
		})

		for i, f := range table.Functions {
			if f.Size == 0 {
				f.Size = elfFile.detectSizeSymbol(table.Functions, i)
			}

			// Special case where symbol of same address can be in different order
			// between the ELF and the object file
			if i < len(table.Functions)-1 && table.Functions[i].Addr == table.Functions[i+1].Addr {
				if strings.Compare(table.Functions[i].Name, table.Functions[i+1].Name) > 0 {
					swap(i, table.Functions)
				}
			}
		}
	}

	return nil
}

func swap(index int, x []ELF64Function) {
	x[index], x[index+1] = x[index+1], x[index]
}

func (table *FunctionTables) displayFunctions(w *tabwriter.Writer, fullDisplay bool) {

	_, _ = fmt.Fprintf(w, "\nTable section '%s' contains %d entries:\n",
		table.Name, table.NbEntries)
	_, _ = fmt.Fprintf(w, "Name:\tAddr:\tSize\tRaw:\n")
	for _, f := range table.Functions {
		_, _ = fmt.Fprintf(w, "%s\t%6.x\t%6.x\t%s\n", f.Name, f.Addr, f.Size)

	}
}

func (elfFile *ELF64File) DisplayFunctionsTables(fullDisplay bool) {

	if len(elfFile.FunctionsTables) == 0 {
		u.PrintWarning("Functions table(s) is/are empty")
		return
	}

	w := new(tabwriter.Writer)
	w.Init(os.Stdout, 0, 8, 0, '\t', 0)
	fmt.Println("-----------------------------------------------------------------------")

	for _, table := range elfFile.FunctionsTables {
		table.displayFunctions(w, fullDisplay)
	}
	_ = w.Flush()
}
