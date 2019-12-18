// Copyright 2019 The UNICORE Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file
//
// Author: Gaulthier Gain <gaulthier.gain@uliege.be>

package buildtool

import (
	"path/filepath"
	"strings"

	u "tools/srcs/common"
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
