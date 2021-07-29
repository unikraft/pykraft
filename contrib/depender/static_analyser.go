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
	"bufio"
	"fmt"
	"os"
	u "github.com/unikraft/kraft/contrib/common"
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
		parseReadELF(output, data)
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
		parseNM(output, data)
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
		_ = parseLDD(output, data.SharedLibs, lddGlMap, v)
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
		packageName := parsePackagesName(output)

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
			packageName := parsePackagesName(output)
			return executeDependAptCache(packageName, data, v)
		}
	}

	return nil
}

// executeDependAptCache gathers dependencies by executing 'apt-cache depends'.
//
// It returns an error if any, otherwise it returns nil.
func executeDependAptCache(programName string, data *u.StaticData,
	fullDeps bool) error {

	//  Use 'apt-cache depends' to get dependencies
	if output, err := u.ExecutePipeCommand("apt-cache depends " +
		programName + " | awk '/Depends/ { print $2 }'"); err != nil {
		return err
	} else {
		// Init Dependencies (from apt cache depends)
		data.Dependencies = make(map[string][]string)
		dependenciesMap := make(map[string][]string)
		printDep := make(map[string][]string)
		_ = parseDependencies(output, data.Dependencies, dependenciesMap,
			printDep, fullDeps, 0)
	}

	fmt.Println("----------------------------------------------")
	return nil
}

// -------------------------------------Run-------------------------------------

// staticAnalyser runs the static analysis to get shared libraries,
// system calls and library calls of a given application.
//
func staticAnalyser(args u.Arguments, data *u.Data, programPath string) {

	programName := *args.StringArg[programArg]
	fullDeps := *args.BoolArg[fullDepsArg]

	staticData := &data.StaticData

	// If the program is a binary, runs static analysis tools
	if len(programPath) > 0 {
		// Gather Data from binary file
		u.PrintHeader2("(*) Gathering symbols from ELF file")
		if err := gatherStaticSymbols(programPath, staticData); err != nil {
			u.PrintWarning(err)
		}

		u.PrintHeader2("(*) Gathering symbols & system calls from ELF file")
		if err := gatherStaticSystemCalls(programPath, staticData); err != nil {
			u.PrintWarning(err)
		}

		u.PrintHeader2("(*) Gathering shared libraries from ELF file")
		if err := gatherStaticSharedLibs(programPath, staticData,
			fullDeps); err != nil {
			u.PrintWarning(err)
		}
	}

	// Gather Data from apt-cache
	u.PrintHeader2("(*) Gathering dependencies from apt-cache depends")
	if err := gatherDependencies(programName, staticData, fullDeps); err != nil {
		u.PrintWarning(err)
	}
}
