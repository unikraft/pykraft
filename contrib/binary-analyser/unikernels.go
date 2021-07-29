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
	"github.com/unikraft/kraft/contrib/binary-analyser/elf64analyser"
	"github.com/unikraft/kraft/contrib/binary-analyser/elf64core"
	u "github.com/unikraft/kraft/contrib/common"
	"io/ioutil"
	"path/filepath"
	"strings"
)

const (
	makefile = "Makefile"
	config   = "config"
	objExt   = ".o"
	ldExt    = ".ld.o"
	dbgExt   = ".dbg"
)

type Unikernels struct {
	Unikernel []Unikernel `json:"unikernels"`
}

type Unikernel struct {
	BuildPath            string   `json:"buildPath"`
	Kernel               string   `json:"kernel"`
	SectionSplit         string   `json:"splitSection"`
	DisplayMapping       bool     `json:"displayMapping"`
	DisplayStatSize      bool     `json:"displayStatSize"`
	IgnoredPlats         []string `json:"ignoredPlats"`
	DisplayElfFile       []string `json:"displayElfFile"`
	DisplaySectionInfo   []string `json:"displaySectionInfo"`
	FindSectionByAddress []string `json:"findSectionByAddress"`
	CompareGroup         int      `json:"compareGroup"`

	ElfFile  *elf64core.ELF64File
	ListObjs []*elf64core.ELF64File
	Analyser *elf64analyser.ElfAnalyser
}

func parseFile(path, name string) (*elf64core.ELF64File, error) {
	var elfFile *elf64core.ELF64File
	elfFile = new(elf64core.ELF64File)
	if err := elfFile.ParseAll(path, name); err != nil {
		return nil, err
	}
	return elfFile, nil
}

func (uk *Unikernel) GetKernel() error {
	var err error
	uk.ElfFile, err = parseFile("", uk.Kernel)
	if err != nil {
		return err
	}
	return nil
}

func (uk *Unikernel) GetFiles() error {
	files, err := ioutil.ReadDir(uk.BuildPath)
	if err != nil {
		return err
	}

	uk.ListObjs = make([]*elf64core.ELF64File, 0)
	foundExec := false
	for _, f := range files {

		if f.IsDir() || strings.Contains(f.Name(), makefile) ||
			strings.Contains(f.Name(), config) ||
			strings.Contains(f.Name(), ldExt) {
			continue
		}
		if filepath.Ext(strings.TrimSpace(f.Name())) == objExt &&
			!stringInSlice(f.Name(), uk.IgnoredPlats) {
			objFile, err := parseFile(uk.BuildPath, f.Name())
			if err != nil {
				return err
			}

			uk.ListObjs = append(uk.ListObjs, objFile)
		} else if filepath.Ext(strings.TrimSpace(f.Name())) == dbgExt &&
			!stringInSlice(f.Name(), uk.IgnoredPlats) && !foundExec {

			execName := f.Name()
			if len(uk.Kernel) > 0 {
				execName = uk.Kernel
			}
			uk.ElfFile, err = parseFile(uk.BuildPath, execName)
			if err != nil {
				return err
			}
			foundExec = true
		}
	}

	if len(uk.Kernel) > 0 {
		u.PrintInfo("Use specified ELF file: " + uk.ElfFile.Name)
	} else {
		u.PrintInfo("Use ELF file found in build folder: " + uk.ElfFile.Name)
	}
	return nil
}

func (uk *Unikernel) displayAllElfInfo() {
	uk.ElfFile.Header.DisplayHeader()
	uk.ElfFile.SectionsTable.DisplaySections()
	uk.ElfFile.DisplayRelocationTables()
	uk.ElfFile.DisplaySymbolsTables()
	uk.ElfFile.DynamicTable.DisplayDynamicEntries()
	uk.ElfFile.SegmentsTable.DisplayProgramHeader()
	uk.ElfFile.SegmentsTable.DisplaySegmentSectionMapping()
	uk.ElfFile.DisplayNotes()
	uk.ElfFile.DisplayFunctionsTables(false)
}

func (uk *Unikernel) DisplayElfInfo() {

	if len(uk.DisplayElfFile) == 1 && uk.DisplayElfFile[0] == "all" {
		uk.displayAllElfInfo()
	} else {
		for _, d := range uk.DisplayElfFile {
			if d == "header" {
				uk.ElfFile.Header.DisplayHeader()
			} else if d == "sections" {
				uk.ElfFile.SectionsTable.DisplaySections()
			} else if d == "relocations" {
				uk.ElfFile.DisplayRelocationTables()
			} else if d == "symbols" {
				uk.ElfFile.DisplaySymbolsTables()
			} else if d == "dynamics" {
				uk.ElfFile.DynamicTable.DisplayDynamicEntries()
			} else if d == "segments" {
				uk.ElfFile.SegmentsTable.DisplayProgramHeader()
			} else if d == "mapping" {
				uk.ElfFile.SegmentsTable.DisplaySegmentSectionMapping()
			} else if d == "notes" {
				uk.ElfFile.DisplayNotes()
			} else if d == "functions" {
				uk.ElfFile.DisplayFunctionsTables(false)
			} else {
				u.PrintWarning("No display configuration found for argument: " + d)
			}
		}
	}
}
