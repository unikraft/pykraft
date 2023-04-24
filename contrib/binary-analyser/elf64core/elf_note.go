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
	"encoding/binary"
	"fmt"
	u "github.com/unikraft/kraft/contrib/common"
	"os"
	"text/tabwriter"
)

type NotesTables struct {
	name     string
	dataNote dataNote
}

type dataNote struct {
	name        string
	description string
	elf64note   ELF64Note
}

type ELF64Note struct {
	Namesz   uint32
	Descsz   uint32
	TypeNote uint32
}

func (elfFile *ELF64File) parseNote(index int) error {

	var notesTable NotesTables
	notesTable.name = elfFile.SectionsTable.DataSect[index].Name

	content, err := elfFile.GetSectionContent(uint16(index))

	if err != nil {
		return fmt.Errorf("failed reading note section: %s", err)
	}

	data := bytes.NewReader(content)
	err = binary.Read(data, elfFile.Endianness, &notesTable.dataNote.elf64note)
	if err != nil {
		return fmt.Errorf("failed reading elf64note: %s", err)
	}

	return nil
}

func (elfFile *ELF64File) DisplayNotes() {

	if len(elfFile.NotesTables) == 0 {
		u.PrintWarning("Notes are empty")
		return
	}

	w := new(tabwriter.Writer)
	w.Init(os.Stdout, 0, 8, 0, '\t', 0)
	fmt.Println("-----------------------------------------------------------------------")
	for _, t := range elfFile.NotesTables {
		_, _ = fmt.Fprintf(w, "\nDisplaying notes found in: %s\n", t.name)
		_, _ = fmt.Fprintln(w, " Owner\tData size\tDescription")
		_, _ = fmt.Fprintf(w, " %s\t0x%.6x\t%x\n", t.dataNote.name,
			t.dataNote.elf64note.Descsz, t.dataNote.description)
	}

	_ = w.Flush()
}
