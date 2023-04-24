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

package elf64analyser

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"github.com/unikraft/kraft/contrib/binary-analyser/elf64core"
	u "github.com/unikraft/kraft/contrib/common"
	"os"
	"sort"
	"strings"
	"text/tabwriter"
)

type ElfAnalyser struct {
	ElfLibs []ElfLibs
	ElfPage []*ElfPage
}

type ElfLibs struct {
	Name      string
	StartAddr uint64
	EndAddr   uint64
	Size      uint64
	NbSymbols int
}

func (analyser *ElfAnalyser) DisplayMapping() {

	if len(analyser.ElfLibs) == 0 {
		fmt.Println("Mapping is empty")
		return
	}

	w := new(tabwriter.Writer)
	w.Init(os.Stdout, 0, 8, 0, '\t', 0)
	fmt.Println("-----------------------------------------------------------------------")
	_, _ = fmt.Fprintln(w, "Name \tStart \tEnd \tSize \tNbSymbols\tnbDiv")
	for _, lib := range analyser.ElfLibs {

		var name = lib.Name
		if strings.Contains(lib.Name, string(os.PathSeparator)) {
			split := strings.Split(lib.Name, string(os.PathSeparator))
			name = split[len(split)-1]
		}

		_, _ = fmt.Fprintf(w, "%s \t0x%x \t0x%x \t0x%x\t%d\t%f\n",
			name, lib.StartAddr, lib.EndAddr, lib.Size,
			lib.NbSymbols, float32(lib.StartAddr)/float32(pageSize))
	}
	_ = w.Flush()
}

func filterFunctions(objFuncsAll []elf64core.ELF64Function, elfFuncsAll []elf64core.ELF64Function) []*elf64core.ELF64Function {

	i := 0
	filteredFuncs := make([]*elf64core.ELF64Function, len(objFuncsAll))
	for j, _ := range elfFuncsAll {

		if strings.Compare(objFuncsAll[i].Name, elfFuncsAll[j].Name) == 0 {
			filteredFuncs[i] = &elfFuncsAll[j]
			i++
		} else {
			// Reset the counter if we do not have consecutive functions
			i = 0
			// Special case where we can skip a function if we do not check again
			if strings.Compare(objFuncsAll[i].Name, elfFuncsAll[j].Name) == 0 {
				filteredFuncs[i] = &elfFuncsAll[j]
				i++
			}
		}

		if i == len(objFuncsAll) {
			return filteredFuncs
		}
	}
	return nil
}

func compareFunctions(elf *elf64core.ELF64File, obj *elf64core.ELF64File) (uint64, uint64, int) {

	// Obj: Merge all functions table(s) in one slice for simplicity
	objFuncs := make([]elf64core.ELF64Function, 0)
	for i := len(obj.FunctionsTables) - 1; i >= 0; i-- {
		if strings.Compare(obj.FunctionsTables[i].Name, elf64core.BootTextSection) != 0 {
			// Ignore the '.text.boot' section since it can be split through
			// different places
			objFuncs = append(objFuncs, obj.FunctionsTables[i].Functions...)
		}
	}
	// Elf: Merge all functions table(s) in one slice for simplicity
	elfFuncs := make([]elf64core.ELF64Function, 0)
	for i := len(elf.FunctionsTables) - 1; i >= 0; i-- {
		if strings.Compare(elf.FunctionsTables[i].Name, elf64core.BootTextSection) != 0 {
			// Ignore the '.text.boot' section since it can be split through
			// different places
			elfFuncs = append(elfFuncs, elf.FunctionsTables[i].Functions...)
		}
	}

	// Add functions into a map for better search
	mapObjFuncs := make(map[string]*elf64core.ELF64Function)
	for i := 0; i < len(objFuncs); i++ {
		mapObjFuncs[objFuncs[i].Name] = &objFuncs[i]
	}

	elfFuncsAll := make([]elf64core.ELF64Function, 0)
	mapArrayFuncs := make(map[string]uint64, 0)
	for _, elfFunc := range elfFuncs {
		if _, ok := mapObjFuncs[elfFunc.Name]; ok {
			// Check if the function is already in mapArrayFuncs
			val, ok := mapArrayFuncs[elfFunc.Name]
			// Do not add duplicate functions (check on addresses)
			if !ok {
				mapArrayFuncs[elfFunc.Name] = elfFunc.Addr
				elfFuncsAll = append(elfFuncsAll, elfFunc)
			} else if val != elfFunc.Addr {
				elfFuncsAll = append(elfFuncsAll, elfFunc)
			}

		}
	}

	if len(elfFuncsAll) == 0 {
		u.PrintWarning(fmt.Sprintf("Cannot extract mapping of lib %s: No function", obj.Name))
		return 0, 0, 0
	}

	if len(elfFuncsAll) != len(objFuncs) {
		// We do not have the same set of functions, need to filter it.
		filteredFuncs := filterFunctions(objFuncs, elfFuncsAll)
		if filteredFuncs == nil {
			u.PrintWarning(fmt.Sprintf("Cannot extract mapping of lib %s: Different size", obj.Name))
			return 0, 0, 0
		}
		return filteredFuncs[0].Addr, filteredFuncs[len(filteredFuncs)-1].Size +
			filteredFuncs[len(filteredFuncs)-1].Addr, len(filteredFuncs)
	}

	return elfFuncsAll[0].Addr, elfFuncsAll[len(elfFuncsAll)-1].Size +
		elfFuncsAll[len(elfFuncsAll)-1].Addr, len(elfFuncsAll)
}

func (analyser *ElfAnalyser) InspectMapping(elf *elf64core.ELF64File, objs ...interface{}) {

	if len(objs) == 0 {
		return
	}

	analyser.ElfLibs = make([]ElfLibs, 0)
	for _, iobj := range objs {
		obj := iobj.(*elf64core.ELF64File)
		start, end, nbSymbols := compareFunctions(elf, obj)
		analyser.ElfLibs = append(analyser.ElfLibs, ElfLibs{
			Name:      obj.Name,
			StartAddr: start,
			EndAddr:   end,
			Size:      end - start,
			NbSymbols: nbSymbols,
		})
		return
	}

	// sort functions
	sort.Slice(analyser.ElfLibs, func(i, j int) bool {
		return analyser.ElfLibs[i].StartAddr < analyser.ElfLibs[j].StartAddr
	})
}

func (analyser *ElfAnalyser) InspectMappingList(elf *elf64core.ELF64File,
	objs []*elf64core.ELF64File) {

	if len(objs) == 0 {
		return
	}

	analyser.ElfLibs = make([]ElfLibs, 0)
	for _, obj := range objs {
		start, end, nbSymbols := compareFunctions(elf, obj)
		analyser.ElfLibs = append(analyser.ElfLibs, ElfLibs{
			Name:      obj.Name,
			StartAddr: start,
			EndAddr:   end,
			Size:      end - start,
			NbSymbols: nbSymbols,
		})
	}

	// sort functions by start address.
	sort.Slice(analyser.ElfLibs, func(i, j int) bool {
		return analyser.ElfLibs[i].StartAddr < analyser.ElfLibs[j].StartAddr
	})
}

func (analyser *ElfAnalyser) SplitIntoPagesBySection(elfFile *elf64core.ELF64File, sectionName string) {

	if len(analyser.ElfPage) == 0 {
		analyser.ElfPage = make([]*ElfPage, 0)
	}

	if strings.Contains(sectionName, elf64core.TextSection) {
		// An ELF might have several text sections
		for _, indexSection := range elfFile.TextSectionIndex {
			sectionName := elfFile.SectionsTable.DataSect[indexSection].Name
			analyser.computePage(elfFile, sectionName, indexSection)
		}
	} else if indexSection, ok := elfFile.IndexSections[sectionName]; ok {
		analyser.computePage(elfFile, sectionName, indexSection)
	} else {
		u.PrintWarning(fmt.Sprintf("Cannot split section %s into pages", sectionName))
	}
}

func CreateNewPage(startAddress uint64, k int, raw []byte) *ElfPage {
	byteArray := make([]byte, pageSize)
	b := raw
	if cpd := copy(byteArray, b); cpd == 0 {
		u.PrintWarning("0 bytes were copied")
	}
	page := &ElfPage{
		number:           k,
		startAddress:     startAddress,
		contentByteArray: byteArray,
	}
	h := sha256.New()
	h.Write(page.contentByteArray)
	page.hash = hex.EncodeToString(h.Sum(nil))
	return page
}

func (analyser *ElfAnalyser) computePage(elfFile *elf64core.ELF64File, section string, indexSection int) {
	offsetTextSection := elfFile.SectionsTable.DataSect[indexSection].Elf64section.FileOffset
	k := 0
	for i := offsetTextSection; i < offsetTextSection+elfFile.SectionsTable.DataSect[indexSection].Elf64section.Size; i += pageSize {

		end := i + pageSize
		if end >= uint64(len(elfFile.Raw)) {
			end = uint64(len(elfFile.Raw) - 1)
		}
		page := CreateNewPage(i, k, elfFile.Raw[i:end])
		page.sectionName = section
		analyser.ElfPage = append(analyser.ElfPage, page)
		k++
	}
}