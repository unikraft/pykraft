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
	"path/filepath"
	"strings"
	u "github.com/unikraft/kraft/contrib/common"
)

// ----------------------------Generate Makefile--------------------------------

// generateMakefile generates a 'Makefile' file for the Unikraft build system.
//
// It returns an error if any, otherwise it returns nil.
func generateMakefile(filename, unikraftPath, appFolder string,
	matchedLibs []string, externalLibs map[string]string) error {

	var sb strings.Builder

	// Set unikraft root and libs workspace
	sb.WriteString("UK_ROOT ?= " + unikraftPath + "unikraft\n" +
		"UK_LIBS ?= " + unikraftPath + "libs\n")

	var libC = ""
	// Add external libs
	sb.WriteString("LIBS := ")
	if len(matchedLibs) > 0 {
		for _, lib := range matchedLibs {
			// Only write external libs
			if _, ok := externalLibs[lib]; ok {
				if strings.Compare(NEWLIB, lib) == 0 ||
					strings.Compare(MUSL, lib) == 0 {
					libC = lib
				} else {
					sb.WriteString("$(UK_LIBS)/" + lib + ":")
				}
			}
		}
	}

	// Write libC at the end to avoid conflicts
	if len(libC) > 0 {
		sb.WriteString("$(UK_LIBS)/" + libC)
	}

	sb.WriteString("\n\n")

	// Bind UK_ROOT to make
	sb.WriteString("all:\n" +
		"\t@make -C $(UK_ROOT) A=" + appFolder + " L=$(LIBS)\n\n" +
		"$(MAKECMDGOALS):\n" +
		"\t@make -C $(UK_ROOT) A=" + appFolder + " L=$(LIBS) $(MAKECMDGOALS)\n")

	// Save the content to Makefile
	return u.WriteToFile(filename, []byte(sb.String()))
}

// typeFile determines the type of a given file.
//
// It returns a string that represents the used language.
func typeFile(filename string) string {
	var extension = filepath.Ext(filename)
	var flag string
	switch extension {
	case ".c":
		flag = "C"
	case ".cc":
	case ".cpp":
		flag = "CXX"
	case ".S":
	case ".asm":
		flag = "AS"
	}
	return flag
}

// generateMakefileUK generates a 'Makefile.uk' file for the Unikraft build
// system.
//
// It returns an error if any, otherwise it returns nil.
func generateMakefileUK(filename, programName, filetype string,
	makefileLines string, sourceFiles []string) error {

	var sb strings.Builder

	// Add app registration
	sb.WriteString("########################################" +
		"########################################\n" +
		"# App registration\n" +
		"########################################" +
		"########################################\n" +
		"$(eval $(call addlib,app" + strings.ToLower(programName) + "))\n\n")

	// Add app includes (headers)
	sb.WriteString("########################################" +
		"########################################\n" +
		"# App includes\n" +
		"########################################" +
		"########################################\n" +
		"CINCLUDES-y   += -I$(APP" + strings.ToUpper(programName) + "_BASE)" +
		"/include\n\n")

	// Add app global flags
	sb.WriteString("########################################" +
		"########################################\n" +
		"# Global flags\n" +
		"########################################" +
		"########################################\n" +
		"# Suppress some warnings to make the build process look neater\n" +
		"SUPPRESS_FLAGS += -Wno-unused-parameter " +
		"-Wno-unused-variable -Wno-nonnull \\\n" +
		"-Wno-unused-but-set-variable -Wno-unused-label " +
		"-Wno-char-subscripts \\\n-Wno-unused-function " +
		"-Wno-missing-field-initializers -Wno-uninitialized \\\n" +
		"-Wno-array-bounds -Wno-maybe-uninitialized " +
		"-Wno-pointer-sign -Wno-unused-value \\\n" +
		"-Wno-unused-macros -Wno-parentheses " +
		"-Wno-implicit-function-declaration \\\n" +
		"-Wno-missing-braces -Wno-endif-labels " +
		"-Wno-unused-but-set-variable \\\n" +
		"-Wno-implicit-function-declaration -Wno-type-limits " +
		"-Wno-sign-compare\n\n")

	// Add SUPPRESS Flags
	sb.WriteString("APP" + strings.ToUpper(programName) + "_" +
		typeFile(filetype) + "FLAGS-y +=" + "$(SUPPRESS_FLAGS)\n\n" +
		"# ADD the flags of your app HERE\n\n")

	// Add additional lines
	if len(makefileLines) > 0 {
		b, _ := u.OpenTextFile(makefileLines)
		for _, line := range strings.Split(string(b), "\n") {
			if len(line) > 0 {
				sb.WriteString("APP" + strings.ToUpper(programName) +
					"_CFLAGS-y += " + line + "\n")
			}
		}
	}

	// Add source files
	sb.WriteString("########################################" +
		"########################################\n" +
		"# " + programName + "sources\n" +
		"########################################" +
		"########################################\n")

	for _, s := range sourceFiles {
		sb.WriteString("APP" + strings.ToUpper(programName) +
			"_SRCS-y += $(APP" + strings.ToUpper(programName) +
			"_BASE)/" + s + "\n")
	}

	// Save the content to Makefile.uk
	return u.WriteToFile(filename, []byte(sb.String()))
}
