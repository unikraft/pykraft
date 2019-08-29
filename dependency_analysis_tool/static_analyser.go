// Copyright 2019 The UNICORE Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file
//
// Author: Gaulthier Gain <gaulthier.gain@uliege.be>

package dependency_analysis_tool

import (
	"bufio"
	"fmt"
	"os"
	"tools/dependency_analysis_tool/utils_dependency"
	u "tools/utils_toolchain"
)

// ---------------------------------Gather Data---------------------------------

// gatherStaticSymbols gathers symbols of a given application.
//
// It returns an error if any, otherwise it returns nil.
func gatherStaticSymbols(programPath string, data *u.StaticData) error {

	// Use 'readelf' to get symbols
	if output, err := u.ExecuteCommand("readelf", []string{"-s",
		programPath}); err != nil {
		return err
	} else {
		// Init symbols members
		data.Symbols = make(map[string]string)
		utils_dependency.ParseReadELF(output, data)
	}
	return nil
}

// gatherStaticSymbols gathers system calls of a given application.
//
// It returns an error if any, otherwise it returns nil.
func gatherStaticSystemCalls(programPath string, data *u.StaticData) error {

	// Use 'nm' to get symbols and system calls
	if output, err := u.ExecuteCommand("nm", []string{"-D",
		programPath}); err != nil {
		return err
	} else {
		// Init system calls members
		data.SystemCalls = make(map[string]string)
		utils_dependency.ParseNM(output, data)
	}
	return nil
}

// gatherStaticSymbols gathers shared libs of a given application.
//
// It returns an error if any, otherwise it returns nil.
func gatherStaticSharedLibs(programPath string, data *u.StaticData,
	v bool) error {

	// Use 'ldd' to get shared libraries
	if output, err := u.ExecutePipeCommand("ldd " + programPath +
		" | awk '/ => / { print $1,$3 }'"); err != nil {
		return err
	} else {
		// Init SharedLibs
		data.SharedLibs = make(map[string][]string)
		lddGlMap := make(map[string][]string)
		_ = utils_dependency.ParseLDD(output, data.SharedLibs, lddGlMap, v)
	}
	return nil
}

// gatherDependencies gathers dependencies of a given application.
//
// It returns an error if any, otherwise it returns nil.
func gatherDependencies(programName string, data *u.StaticData, v bool) error {

	//  Use 'apt-cache pkgnames' to get the name of the package
	output, err := u.ExecuteCommand("apt-cache",
		[]string{"pkgnames", programName})
	if err != nil {
		return err
	}

	// If the name of the package is know, execute apt-cache depends
	if len(output) > 0 {
		// Parse package name
		packageName := utils_dependency.ParsePackagesName(output)

		if len(packageName) > 0 {
			return executeDependAptCache(packageName, data, v)
		}
	} else {
		// Enter manually the name of the package
		u.PrintWarning(programName + " not found in apt-cache")
		var output string
		for len(output) == 0 {
			fmt.Print("Please enter manually the name of the package " +
				"(empty string to exit): ")
			scanner := bufio.NewScanner(os.Stdin)
			if err := scanner.Err(); err != nil {
				return err
			}

			if scanner.Scan() {

				// Get the new package name
				input := scanner.Text()
				if input == "" {
					break
				}

				output, err = u.ExecuteCommand("apt-cache",
					[]string{"pkgnames", input})
				if err != nil {
					return err
				}
			}
		}

		if len(output) == 0 {
			u.PrintWarning("Skip dependencies analysis from apt-cache depends")
		} else {
			packageName := utils_dependency.ParsePackagesName(output)
			return executeDependAptCache(packageName, data, v)
		}
	}

	return nil
}

// executeDependAptCache gathers dependencies by executing 'apt-cache depends'.
//
// It returns an error if any, otherwise it returns nil.
func executeDependAptCache(programName string, data *u.StaticData,
	verbose bool) error {

	//  Use 'apt-cache depends' to get dependencies
	if output, err := u.ExecutePipeCommand("apt-cache depends " +
		programName + " | awk '/Depends/ { print $2 }'"); err != nil {
		return err
	} else {
		// Init Dependencies (from apt cache depends)
		data.Dependencies = make(map[string][]string)
		dependenciesMap := make(map[string][]string)
		printDep := make(map[string][]string)
		_ = utils_dependency.ParseDependencies(output, data.Dependencies, dependenciesMap,
			printDep, verbose, 0)
	}

	fmt.Println("----------------------------------------------")
	return nil
}

// -------------------------------------Run-------------------------------------

// RunStaticAnalyser runs the static analysis to get shared libraries,
// system calls and library calls of a given application.
//
func RunStaticAnalyser(args u.Arguments, data *u.Data, programPath,
	outFolder string) {

	programName := *args.StringArg["program"]
	v := *args.BoolArg["verbose"]

	staticData := &data.StaticData

	// If the program is a binary, runs static analysis tools
	if len(programPath) > 0 {
		// Gather Data from binary file
		u.PrintHeader2("(*) Gathering symbols from ELF file")
		if err := gatherStaticSymbols(programPath, staticData); err != nil {
			u.PrintWarning(err)
		}

		u.PrintHeader2("(*) Gathering symbols & system calls rom ELF file")
		if err := gatherStaticSystemCalls(programPath, staticData); err != nil {
			u.PrintWarning(err)
		}

		u.PrintHeader2("(*) Gathering shared libraries rom ELF file")
		if err := gatherStaticSharedLibs(programPath, staticData,
			v); err != nil {
			u.PrintWarning(err)
		}
	}

	// Gather Data from apt-cache
	u.PrintHeader2("(*) Gathering dependencies from apt-cache depends")
	if err := gatherDependencies(programName, staticData, v); err != nil {
		u.PrintWarning(err)
	}

	// Create the folder 'output/static' if it does not exist
	if _, err := os.Stat(outFolder); os.IsNotExist(err) {
		if err = os.Mkdir(outFolder, os.ModePerm); err != nil {
			u.PrintErr(err)
		}
	}
}
