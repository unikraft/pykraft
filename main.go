// Copyright 2019 The UNICORE Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file
//
// Author: Gaulthier Gain <gaulthier.gain@uliege.be>

package main

import (
	"fmt"
	"os"
	"os/user"
	"runtime"
	"strconv"
	"strings"

	"github.com/fatih/color"
	build "github.com/unikraft/tools/automatic_build_tool"
	dep "github.com/unikraft/tools/dependency_analysis_tool"
	"github.com/unikraft/tools/dependency_analysis_tool/utils_dependency"
	u "github.com/unikraft/tools/utils_toolchain"
)

const OUT_FOLDER = "output/"

func main() {

	if strings.ToLower(runtime.GOOS) != "linux" {
		u.PrintErr("Only UNIX/Linux platforms are supported")
	}

	// Parse arguments
	args := new(u.Arguments)
	args.InitArguments(args)
	err := args.ParseArguments(args)
	if err != nil {
		u.PrintErr(err)
	}

	// Get program path
	programPath, err := u.GetProgramPath(args.StringArg["program"])
	if err != nil {
		u.PrintErr("Could not determine program path", err)
	}

	// Display Minor Details
	programName := *args.StringArg["program"]
	fmt.Println("----------------------------------------------")
	fmt.Println("Analyze Program: ", color.GreenString(programName))
	fmt.Println("Full Path: ", color.GreenString(programPath))
	if *args.BoolArg["background"] {
		fmt.Println("Background: ", color.GreenString(
			strconv.FormatBool(*args.BoolArg["background"])))
	} else {
		fmt.Println("Background: ", color.RedString(
			strconv.FormatBool(*args.BoolArg["background"])))
	}
	fmt.Println("Options: ", color.GreenString(*args.StringArg["options"]))
	fmt.Println("----------------------------------------------")

	// Check if the program is an ELF
	elfFile, err := utils_dependency.GetElf(programPath)
	if err != nil {
		u.PrintErr(err)
	} else if elfFile == nil {
		programPath = ""
		u.PrintWarning("Only ELF binaries are supported! Some analysis" +
			" procedures will be skipped")
	} else {
		// Get ELF architecture
		architecture, machine := utils_dependency.GetElfArchitecture(elfFile)
		fmt.Println("ELF Class: ", architecture)
		fmt.Println("Machine: ", machine)
		fmt.Println("Entry Point: ", elfFile.Entry)
		fmt.Println("----------------------------------------------")
	}

	// Get user home folder
	usr, err := user.Current()
	if err != nil {
		u.PrintErr(err)
	}

	var data *u.Data

	// Checks if the toolchain must be completely executed
	all := false
	if !*args.BoolArg["dep"] && !*args.BoolArg["build"] &&
		!*args.BoolArg["verif"] && !*args.BoolArg["perf"] {
		all = true
	}

	// Create the folder 'output' if it does not exist
	outFolder := usr.HomeDir + string(os.PathSeparator) + programName +
		"_" + OUT_FOLDER
	if _, err := os.Stat(outFolder); os.IsNotExist(err) {
		if err = os.Mkdir(outFolder, os.ModePerm); err != nil {
			u.PrintErr(err)
		}
	}

	if all || *args.BoolArg["dep"] {

		// Initialize data
		data = new(u.Data)

		// Run static analyser
		u.PrintHeader1("(1) RUN STATIC ANALYSIS")
		runStaticAnalyser(args, programName, programPath, outFolder, data)

		// Run dynamic analyser
		u.PrintHeader1("(2) RUN DYNAMIC ANALYSIS")
		runDynamicAnalyser(args, programName, programPath, outFolder, data)

		// Save Data to JSON
		if err = u.RecordDataJson(outFolder+programName, data); err != nil {
			u.PrintErr(err)
		} else {
			u.PrintOk("JSON Data saved into " + outFolder + programName +
				".json")
		}

		// Save graph if verbose mode is set
		if *args.BoolArg["verbose"] {
			saveGraph(programName, outFolder, data)
		}
	}

	if all || *args.BoolArg["build"] {
		u.PrintHeader1("(3) AUTOMATIC BUILD TOOL")
		build.RunBuildTool(*args, data, outFolder)
	}

	if all || *args.BoolArg["verif"] {
		u.PrintHeader1("(4) VERIFICATION TOOL")
	}

	if all || *args.BoolArg["perf"] {
		u.PrintHeader1("(5) PERFORMANCE OPTIMIZATION TOOL")
	}
}

// runStaticAnalyser runs the static analyser
func runStaticAnalyser(args *u.Arguments, programName, programPath,
	outFolder string, data *u.Data) {

	dep.RunStaticAnalyser(*args, data, programPath, outFolder+"static/")

	// Save static Data into text file if display mode is set
	if args.BoolArg["display"] != nil {

		fn := outFolder + "static/" + programName + ".txt"
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

	dep.RunDynamicAnalyser(*args, data, programPath, outFolder+"dynamic/")

	// Save dynamic Data into text file if display mode is set
	if args.BoolArg["display"] != nil {

		fn := outFolder + "dynamic/" + programName + ".txt"
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
		utils_dependency.GenerateGraph(programName, outFolder+"static/"+
			programName+"_shared_libs", data.StaticData.SharedLibs)
	}

	if len(data.StaticData.SharedLibs) > 0 {
		utils_dependency.GenerateGraph(programName, outFolder+"static/"+
			programName+"_dependencies", data.StaticData.Dependencies)
	}

	if len(data.StaticData.SharedLibs) > 0 {
		utils_dependency.GenerateGraph(programName, outFolder+"dynamic/"+
			programName+"_shared_libs", data.DynamicData.SharedLibs)
	}
}
