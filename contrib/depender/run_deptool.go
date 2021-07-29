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
	"fmt"
	"runtime"
	"strings"
	u "github.com/unikraft/kraft/contrib/common"

	"github.com/fatih/color"
)

// RunAnalyserTool allows to run the dependency analyser tool.
func RunAnalyserTool(homeDir string, data *u.Data) {

	// Support only Unix
	if strings.ToLower(runtime.GOOS) != "linux" {
		u.PrintErr("Only UNIX/Linux platforms are supported")
	}

	// Init and parse local arguments
	args := new(u.Arguments)
	p, err := args.InitArguments("kraft-devel-depender", "")
	if err != nil {
		u.PrintErr(err)
	}
	if err := parseLocalArguments(p, args); err != nil {
		u.PrintErr(err)
	}

	// Get program path
	programPath, err := u.GetProgramPath(&*args.StringArg[programArg])
	if err != nil {
		u.PrintErr("Could not determine program path", err)
	}

	// Get program Name
	programName := *args.StringArg[programArg]

	// Create the folder 'output' if it does not exist
	outFolder := homeDir + u.SEP + programName + "_" + u.OUTFOLDER
	if _, err := u.CreateFolder(outFolder); err != nil {
		u.PrintErr(err)
	}

	// Display Minor Details
	displayProgramDetails(programName, programPath, args)

	// Check if the program is an ELF
	checkElf(&programPath)

	// Run static analyser
	u.PrintHeader1("(1.1) RUN STATIC ANALYSIS")
	runStaticAnalyser(args, programName, programPath, outFolder, data)

	// Run dynamic analyser
	u.PrintHeader1("(1.2) RUN DYNAMIC ANALYSIS")
	runDynamicAnalyser(args, programName, programPath, outFolder, data)

	// Save Data to JSON
	if err = u.RecordDataJson(outFolder+programName, data); err != nil {
		u.PrintErr(err)
	} else {
		u.PrintOk("JSON Data saved into " + outFolder + programName +
			".json")
	}

	// Save graph if full dependencies option is set
	if *args.BoolArg[fullDepsArg] {
		saveGraph(programName, outFolder, data)
	}
}

// displayProgramDetails display various information such path, background, ...
func displayProgramDetails(programName, programPath string, args *u.Arguments) {
	fmt.Println("----------------------------------------------")
	fmt.Println("Analyze Program: ", color.GreenString(programName))
	fmt.Println("Full Path: ", color.GreenString(programPath))
	if len(*args.StringArg[optionsArg]) > 0 {
		fmt.Println("Options: ", color.GreenString(*args.StringArg[optionsArg]))
	}

	if len(*args.StringArg[configFileArg]) > 0 {
		fmt.Println("Config file: ", color.GreenString(*args.StringArg[configFileArg]))
	}

	if len(*args.StringArg[testFileArg]) > 0 {
		fmt.Println("Test file: ", color.GreenString(*args.StringArg[testFileArg]))
	}

	fmt.Println("----------------------------------------------")
}

// checkElf checks if the program (from its path) is an ELF file
func checkElf(programPath *string) {
	elfFile, err := getElf(*programPath)
	if err != nil {
		u.PrintErr(err)
	} else if elfFile == nil {
		*programPath = ""
		u.PrintWarning("Only ELF binaries are supported! Some analysis" +
			" procedures will be skipped")
	} else {
		// Get ELF architecture
		architecture, machine := GetElfArchitecture(elfFile)
		fmt.Println("ELF Class: ", architecture)
		fmt.Println("Machine: ", machine)
		fmt.Println("Entry Point: ", elfFile.Entry)
		fmt.Println("----------------------------------------------")
	}
}

// runStaticAnalyser runs the static analyser
func runStaticAnalyser(args *u.Arguments, programName, programPath,
	outFolder string, data *u.Data) {

	staticAnalyser(*args, data, programPath)

	// Save static Data into text file if display mode is set
	if *args.BoolArg[saveOutputArg] {

		// Create the folder 'output/static' if it does not exist
		outFolderStatic := outFolder + "static" + u.SEP
		if _, err := u.CreateFolder(outFolderStatic); err != nil {
			u.PrintErr(err)
		}

		fn := outFolderStatic + programName + ".txt"
		headersStr := []string{"Dependencies (from apt-cache show) list:",
			"Shared libraries list:", "System calls list:", "Symbols list:"}

		if err := u.RecordDataTxt(fn, headersStr, data.StaticData); err != nil {
			u.PrintWarning(err)
		} else {
			u.PrintOk("Data saved into " + fn)
		}
	}
}

// runDynamicAnalyser runs the dynamic analyser.
func runDynamicAnalyser(args *u.Arguments, programName, programPath,
	outFolder string, data *u.Data) {

	dynamicAnalyser(args, data, programPath)

	// Save dynamic Data into text file if display mode is set
	if *args.BoolArg[saveOutputArg] {

		// Create the folder 'output/dynamic' if it does not exist
		outFolderDynamic := outFolder + "dynamic" + u.SEP
		if _, err := u.CreateFolder(outFolderDynamic); err != nil {
			u.PrintErr(err)
		}

		fn := outFolderDynamic + programName + ".txt"
		headersStr := []string{"Shared libraries list:", "System calls list:",
			"Symbols list:"}

		if err := u.RecordDataTxt(fn, headersStr, data.DynamicData); err != nil {
			u.PrintWarning(err)
		} else {
			u.PrintOk("Data saved into " + fn)
		}
	}
}

// saveGraph saves dependency graphs of a given app into the output folder.
func saveGraph(programName, outFolder string, data *u.Data) {

	if len(data.StaticData.SharedLibs) > 0 {
		u.GenerateGraph(programName, outFolder+"static"+u.SEP+
			programName+"_shared_libs", data.StaticData.SharedLibs, nil)
	}

	if len(data.StaticData.Dependencies) > 0 {
		u.GenerateGraph(programName, outFolder+"static"+u.SEP+
			programName+"_dependencies", data.StaticData.Dependencies, nil)
	}

	if len(data.StaticData.SharedLibs) > 0 {
		u.GenerateGraph(programName, outFolder+"dynamic"+u.SEP+
			programName+"_shared_libs", data.DynamicData.SharedLibs, nil)
	}
}
