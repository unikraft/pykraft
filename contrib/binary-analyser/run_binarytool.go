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

package main

import (
	"errors"
	"fmt"
	u "github.com/unikraft/kraft/contrib/common"
	"os"
	"strings"
	"github.com/unikraft/kraft/contrib/binary-analyser/elf64analyser"
)

const diffPath = "diff" + u.SEP
const pagesPath = "pages" + u.SEP

// RunBinaryAnalyser allows to run the binary analyser tool.
func RunBinaryAnalyser(homeDir string) {

	// Init and parse local arguments
	args := new(u.Arguments)
	p, err := args.InitArguments("kraft-devel-binary-analyser", "")
	if err != nil {
		u.PrintErr(err)
	}
	if err := parseLocalArguments(p, args); err != nil {
		u.PrintErr(err)
	}

	// Check if a json file is used or if it is via command line
	var unikernels *Unikernels
	if len(*args.StringArg[listArg]) > 0 {
		unikernels = new(Unikernels)
		unikernels.Unikernel = make([]Unikernel, len(*args.StringArg[listArg]))
		mapping := false
		if *args.BoolArg[mappingArg] {
			mapping = true
		}
		list := strings.Split(*args.StringArg[listArg], ",")
		for i, arg := range list {
			unikernels.Unikernel[i] = Unikernel{
				BuildPath:      arg,
				DisplayMapping: mapping,
			}
		}
	} else if len(*args.StringArg[filesArg]) > 0 {
		var err error
		unikernels, err = ReadJsonFile(*args.StringArg[filesArg])
		if err != nil {
			u.PrintErr(err)
		}
	} else {
		u.PrintErr(errors.New("argument(s) must be provided"))
	}

	var comparison elf64analyser.ComparisonElf
	comparison.GroupFileSegment = make([]*elf64analyser.ElfFileSegment, 0)

	for i, uk := range unikernels.Unikernel {

		uk.Analyser = new(elf64analyser.ElfAnalyser)
		if len(uk.BuildPath) > 0 {
			if uk.BuildPath[len(uk.BuildPath)-1] != os.PathSeparator {
				uk.BuildPath += u.SEP
			}
			if err := uk.GetFiles(); err != nil {
				u.PrintErr(err)
			}

			// Perform the inspection of micro-libs since we have the buildPath
			uk.Analyser.InspectMappingList(uk.ElfFile, uk.ListObjs)
		} else {
			if err := uk.GetKernel(); err != nil {
				u.PrintErr(err)
			}
		}

		if len(uk.DisplayElfFile) > 0 {
			uk.DisplayElfInfo()
		}

		if uk.DisplayMapping && len(uk.BuildPath) > 0 {
			fmt.Printf("==========[(%d): %s]==========\n", i, uk.BuildPath)
			uk.Analyser.DisplayMapping()
			fmt.Println("=====================================================")
		}

		if uk.DisplayStatSize {
			uk.Analyser.DisplayStatSize(uk.ElfFile)
		}

		if len(uk.DisplaySectionInfo) > 0 {
			uk.Analyser.DisplaySectionInfo(uk.ElfFile, uk.DisplaySectionInfo)
		}

		if len(uk.FindSectionByAddress) > 0 {
			uk.Analyser.FindSectionByAddress(uk.ElfFile, uk.FindSectionByAddress)
		}

		if uk.CompareGroup > 0 {

			foundSection := false
			section := uk.SectionSplit
			for _, s := range uk.ElfFile.SectionsTable.DataSect {
				if s.Name == section {
					foundSection = true
					break
				}
			}

			if foundSection {

				path := homeDir + u.SEP + pagesPath
				if _, err := os.Stat(path); os.IsNotExist(err) {
					err := os.Mkdir(path, os.ModePerm)
					if err != nil {
						u.PrintErr(err)
					}
				}

				u.PrintInfo(fmt.Sprintf("Splitting %s section of %s into pages...", section, uk.ElfFile.Name))
				uk.Analyser.SplitIntoPagesBySection(uk.ElfFile, section)

				out := path + section[1:] + u.SEP

				if _, err := os.Stat(out); os.IsNotExist(err) {
					err := os.Mkdir(out, os.ModePerm)
					if err != nil {
						u.PrintErr(err)
					}
				}

				if err := elf64analyser.SavePagesToFile(uk.Analyser.ElfPage, out+uk.ElfFile.Name+".txt", false); err != nil {
					u.PrintErr(err)
				}
				u.PrintOk(fmt.Sprintf("Pages of section %s (%s) are saved into %s", section, uk.ElfFile.Name, out))

				comparison.GroupFileSegment = append(comparison.GroupFileSegment,
					&elf64analyser.ElfFileSegment{Filename: uk.ElfFile.Name,
						NbPages: len(uk.Analyser.ElfPage), Pages: uk.Analyser.ElfPage})
			} else {
				u.PrintWarning("Section '" + section + "' is not found in the ELF file")
			}

		}
	}

	if len(comparison.GroupFileSegment) > 1 {

		// Perform the comparison
		path := homeDir + u.SEP + diffPath
		if _, err := os.Stat(path); os.IsNotExist(err) {
			err := os.Mkdir(path, os.ModePerm)
			if err != nil {
				u.PrintErr(err)
			}
		}

		comparison.ComparePageTables()
		if err := comparison.DiffComparison(path); err != nil {
			u.PrintWarning(err)
		}
		comparison.DisplayComparison()
	}
}
