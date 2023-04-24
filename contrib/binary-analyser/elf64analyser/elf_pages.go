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
	"fmt"
	"io"
	"os"
	"strings"
)

const pageSize = 0x1000

type ElfFileSegment struct {
	Filename string
	NbPages  int
	Pages    []*ElfPage
}

type ElfPage struct {
	number           int
	startAddress     uint64
	contentByteArray []byte
	hash             string
	libName          string
	sectionName      string
	noNullValues     int
	cap              int
}

func (p *ElfPage) pageContentToString() string {

	var builder strings.Builder
	for i, entry := range p.contentByteArray {

		if i > 0 && i%4 == 0 {
			builder.WriteString(" ")
		}

		if i > 0 && i%16 == 0 {
			builder.WriteString("\n")
		}

		_, _ = builder.WriteString(fmt.Sprintf("%02x", entry))

	}
	_, _ = builder.WriteString("")
	return builder.String()
}

func (p *ElfPage) displayPageContent(mw io.Writer) {

	/*
		hexStartAddr, err := strconv.ParseInt(p.startAddress, 16, 64);
		if err != nil {
			panic(err)
		}
	*/
	for i, entry := range p.contentByteArray {

		if i > 0 && i%4 == 0 {
			_, _ = fmt.Fprintf(mw, " ")
		}

		if i > 0 && i%16 == 0 {
			_, _ = fmt.Fprintf(mw, "\n")
		}

		_, _ = fmt.Fprintf(mw, "%02x", entry)

	}
	_, _ = fmt.Fprintln(mw, "")
}

func (p *ElfPage) displayPageContentShort(mw io.Writer) {

	entryLine := 0
	for i, entry := range p.contentByteArray {

		if entry > 0 {
			_, _ = fmt.Fprintf(mw, "[%d] %02x ", i, entry)
			if entryLine > 0 && entryLine%16 == 0 {
				_, _ = fmt.Fprintf(mw, "\n")
			}
			entryLine++
		}
	}
	_, _ = fmt.Fprintln(mw, "")
}

func SavePagesToFile(pageTables []*ElfPage, filename string, shortView bool) error {

	mw := io.MultiWriter(os.Stdout)
	if len(filename) > 0 {
		file, err := os.Create(filename)

		if err != nil {
			return err
		}
		mw = io.MultiWriter(file)
	}

	for i, p := range pageTables {
		_, _ = fmt.Fprintln(mw, "----------------------------------------------------")
		_, _ = fmt.Fprintf(mw, "Page: %d\n", i+1)
		_, _ = fmt.Fprintf(mw, "LibName: %s\n", p.libName)
		_, _ = fmt.Fprintf(mw, "Section: %s\n", p.sectionName)
		_, _ = fmt.Fprintf(mw, "StartAddr: %x (%d)\n", p.startAddress, p.startAddress)
		_, _ = fmt.Fprintf(mw, "Non-Null value: %d\n", p.noNullValues)
		_, _ = fmt.Fprintf(mw, "Hash: %s\n", p.hash)

		if shortView {
			p.displayPageContentShort(mw)
		} else {
			p.displayPageContent(mw)
		}
		_, _ = fmt.Fprintln(mw, "----------------------------------------------------")
	}
	return nil
}
