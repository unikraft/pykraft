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
	"errors"
	"fmt"
	"github.com/unikraft/kraft/contrib/binary-analyser/elf64core"
	u "github.com/unikraft/kraft/contrib/common"
	"os"
	"strconv"
	"strings"
	"text/tabwriter"
)

type ComparisonElf struct {
	GroupFileSegment []*ElfFileSegment
	dictSamePage     map[string]int
	dictFile         map[string]map[string]int
}

func (comparison *ComparisonElf) processDictName(filename, hash string) {
	m := comparison.dictFile[hash]
	if _, ok := m[filename]; !ok {
		m[filename] = 1
	} else {
		t := m[filename]
		t += 1
		m[filename] = t
	}
	comparison.dictFile[hash] = m
}

func (comparison *ComparisonElf) ComparePageTables() {

	comparison.dictSamePage = make(map[string]int)
	comparison.dictFile = make(map[string]map[string]int)

	for _, file := range comparison.GroupFileSegment {

		for _, p := range file.Pages {
			if _, ok := comparison.dictSamePage[p.hash]; !ok {
				comparison.dictSamePage[p.hash] = 1
				comparison.dictFile[p.hash] = make(map[string]int)
			} else {
				comparison.dictSamePage[p.hash] += 1
			}
			comparison.processDictName(file.Filename, p.hash)
		}

	}
}

func (comparison *ComparisonElf) DisplayComparison() {

	fmt.Println("\n\nHash comparison:")
	for key, value := range comparison.dictFile {
		fmt.Println(key, ";", value)
	}

	fmt.Println("---------------------------")
	fmt.Println("\n\nStats:")
	countSamePage := 0
	singlePage := 0
	for _, value := range comparison.dictSamePage {
		if value > 1 {
			countSamePage += value
		} else {
			singlePage++
		}
	}

	totalNbPages := 0
	for i, _ := range comparison.GroupFileSegment {
		totalNbPages += comparison.GroupFileSegment[i].NbPages
	}
	ratio := (float64(countSamePage) / float64(totalNbPages)) * 100

	fmt.Printf("- Total Nb of pages: %d\n", totalNbPages)
	fmt.Printf("- Nb page(s) sharing: %d\n", countSamePage)
	fmt.Printf("- Page alone: %d\n", singlePage)
	fmt.Printf("- Ratio: %f\n", ratio)
}

func filterOutput(text1, text2 []string) string {
	header := "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><title>Diff Pages</title></head><body style=\"font-family:Menlo\">"
	footer := "</body></html>"

	maxArray := text1
	minArray := text2
	if len(text1) < len(text2) {
		maxArray = text2
		minArray = text1
	}

	var builder strings.Builder
	for i := 0; i < len(maxArray); i++ {
		builder.WriteString("<span>" + maxArray[i] + "</span><br>")
		if i < len(minArray)-1 && maxArray[i] != minArray[i] {
			builder.WriteString("<p><del style=\"background:#ffe6e6;\">" + minArray[i] + "</del><br>")
			builder.WriteString("<ins style=\"background:#e6ffe6;\">" + maxArray[i] + "</ins></p>")
		}
	}

	return header + builder.String() + footer
}

func (comparison *ComparisonElf) DiffComparison(path string) error {

	if len(comparison.GroupFileSegment) != 2 {
		return errors.New("multi-comparison (more than 2) is still not supported")
	}

	minPage := comparison.GroupFileSegment[0].Pages
	for _, file := range comparison.GroupFileSegment {
		if len(minPage) > len(file.Pages) {
			minPage = file.Pages
		}
	}

	println(len(comparison.GroupFileSegment[0].Pages))
	println(len(comparison.GroupFileSegment[1].Pages))

	for i := 0; i < len(minPage); i++ {

		page1 := comparison.GroupFileSegment[0].Pages[i]
		page2 := comparison.GroupFileSegment[1].Pages[i]
		if page1.hash != page2.hash {

			text1String := comparison.GroupFileSegment[0].Pages[i].pageContentToString()
			text2String := comparison.GroupFileSegment[1].Pages[i].pageContentToString()
			text1 := strings.Split(text1String, "\n")
			text2 := strings.Split(text2String, "\n")
			str := filterOutput(text1, text2)

			file, err := os.Create(path + "page_" + strconv.Itoa(page1.number) + "_diff.html")
			if err != nil {
				return err
			}
			if _, err := file.WriteString(str); err != nil {
				return err
			}
			file.Close()

		}
	}

	return nil
}

func (analyser *ElfAnalyser) DisplaySectionInfo(elfFile *elf64core.ELF64File, info []string) {

	w := new(tabwriter.Writer)
	w.Init(os.Stdout, 10, 8, 0, '\t', 0)
	_, _ = fmt.Fprintln(w, "Name\tAddress\tOffset\tSize")
	for _, sectionName := range info {
		if indexSection, ok := elfFile.IndexSections[sectionName]; ok {
			section := elfFile.SectionsTable.DataSect[indexSection].Elf64section

			_, _ = fmt.Fprintf(w, "- %s\t0x%.6x\t0x%.6x\t%d\n",
				sectionName, section.VirtualAddress, section.FileOffset,
				section.Size)

		} else {
			u.PrintWarning("Wrong section name " + sectionName)
		}
	}
	_ = w.Flush()
}

func (analyser *ElfAnalyser) FindSectionByAddress(elfFile *elf64core.ELF64File, addresses []string) {
	if len(elfFile.SectionsTable.DataSect) == 0 {
		u.PrintWarning("Sections table is empty")
		return
	}
	for _, addr := range addresses {
		hexStr := strings.Replace(addr, "0x", "", -1)
		intAddr, err := strconv.ParseUint(hexStr, 16, 64)
		if err != nil {
			u.PrintWarning(fmt.Sprintf("Error %s: Cannot convert %s to integer. Skip.", err, addr))
		} else {
			found := false
			for _, s := range elfFile.SectionsTable.DataSect {
				if s.Elf64section.VirtualAddress <= intAddr && intAddr < s.Elf64section.VirtualAddress+s.Elf64section.Size {
					fmt.Printf("Address %s is in section %s\n", addr, s.Name)
					found = true
				}
			}
			if !found {
				u.PrintWarning(fmt.Sprintf("Cannot find a section for address: %s", addr))
			}
		}
	}
}

func (analyser *ElfAnalyser) DisplayStatSize(elfFile *elf64core.ELF64File) {
	if len(elfFile.SectionsTable.DataSect) == 0 {
		u.PrintWarning("Sections table is empty")
		return
	}
	w := new(tabwriter.Writer)
	w.Init(os.Stdout, 0, 8, 0, '\t', 0)

	var totalSizeText uint64
	var totalSizeElf uint64
	_, _ = fmt.Fprintf(w, "Name\tFile size (Bytes/Hex)\n")
	for _, s := range elfFile.SectionsTable.DataSect {
		if len(s.Name) > 0 {
			_, _ = fmt.Fprintf(w, "%s\t%d (0x%x)\n", s.Name, s.Elf64section.Size, s.Elf64section.Size)
		}
		if strings.Contains(s.Name, elf64core.TextSection) {
			totalSizeText += s.Elf64section.Size
		}
		totalSizeElf += s.Elf64section.Size
	}
	_, _ = fmt.Fprintf(w, "----------------------\t----------------------\n")
	_, _ = fmt.Fprintf(w, "Total Size:\n")
	_, _ = fmt.Fprintf(w, "Section .text:\t%d (0x%x)\n", totalSizeText, totalSizeText)
	_, _ = fmt.Fprintf(w, "All sections:\t%d (0x%x)\n", totalSizeElf, totalSizeElf)
	_, _ = fmt.Fprintf(w, "#Pages (.text):\t%d\n", totalSizeText/pageSize)
	_, _ = fmt.Fprintf(w, "#Pages (all sections):\t%d\n", totalSizeElf/pageSize)
	_ = w.Flush()
}
