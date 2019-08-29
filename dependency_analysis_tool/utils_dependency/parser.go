// Copyright 2019 The UNICORE Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file
//
// Author: Gaulthier Gain <gaulthier.gain@uliege.be>

package utils_dependency

import (
	"fmt"
	"regexp"
	"strings"
	"tools/utils_toolchain"
)

type RecursiveData struct {
	data, glMap, printDep map[string][]string
	cmd, line             string
	listStr               []string
	level                 int
}

// --------------------------------Static Output--------------------------------

// ParseReadELF parses the output of the 'readelf' command.
//
func ParseReadELF(output string, data *util_tools.StaticData) {
	types := map[string]bool{"FUNC": true, "FILE": true, "OBJECT": true}

	// Check the output of 'readelf' command
	for _, line := range strings.Split(output, "\n") {
		words := strings.Fields(line)

		if len(words) > 8 && types[words[3]] {
			symbol := strings.Split(words[7], "@")
			data.Symbols[symbol[0]] = symbol[1]
		}
	}
}

// ParseNM parses the output of the 'nm' command.
//
func ParseNM(output string, data *util_tools.StaticData) {
	// Get the list of system calls
	systemCalls := InitSystemCalls()

	// Check the output of 'nm' command
	var re = regexp.MustCompile(`(?m)([U|T|B|D]\s)(.*)\s*`)
	for _, match := range re.FindAllStringSubmatch(output, -1) {
		// Add to system calls map if symbol is a system call
		if _, isSyscall := systemCalls[match[2]]; isSyscall {
			data.SystemCalls[match[2]] = ""
		} else {
			data.Symbols[match[2]] = ""
		}
	}
}

// ParsePackagesName parses the output of the 'apt-cache pkgnames' command.
//
// It returns a string which represents the name of application used by the
// package manager (apt, ...).
func ParsePackagesName(output string) string {

	var i = 1
	lines := strings.Split(output, "\n")
	for _, line := range lines {
		if len(line) > 0 {
			fmt.Printf("%d) %s\n", i, line)
			i++
		}
	}

	var input int
	for true {
		fmt.Print("Please enter your choice (0 to exit): ")
		if _, err := fmt.Scanf("%d", &input); err != nil {
			util_tools.PrintWarning("Choice must be numeric! Try again")
		} else {
			if input == 0 {
				util_tools.PrintWarning("Abort dependencies analysis from apt-cache")
				return ""
			} else if (input >= 0) && (input <= i) {
				return lines[input-1]
			} else {
				util_tools.PrintWarning("Invalid input! Try again")
			}
		}
	}
	return ""
}

const LEVEL = 5

// ParseDependencies parses the output of the 'apt-cache depends' command.
//
// It returns a slice of strings which represents all the dependencies of
// a particular package.
func ParseDependencies(output string, data, dependenciesMap,
	printDep map[string][]string, verbose bool, level int) []string {
	listDep := make([]string, 0)
	for _, line := range strings.Split(output, "\n") {
		if len(line) > 0 && !strings.Contains(line, "<") {

			if _, in := printDep[line]; !in {
				fmt.Println(line)
				printDep[line] = nil
			}

			if verbose && level < LEVEL {
				rd := RecursiveData{
					data:     data,
					glMap:    dependenciesMap,
					printDep: printDep,
					cmd: "apt-cache depends " + line +
						" | awk '/Depends/ { print $2 }'",
					line:    line,
					listStr: listDep,
					level:   level,
				}
				listDep = append(listDep, line)
				parseRecursive(rd)
			}
		} else {
			data[line] = nil
		}
	}
	return listDep
}

// ParseLDD parses the output of the 'ldd' command.
//
// It returns a slice of strings which represents all the shared libs of
// a particular package.
func ParseLDD(output string, data map[string][]string, lddMap map[string][]string,
	v bool) []string {

	listLdd := make([]string, 0)
	for _, line := range strings.Split(output, "\n") {
		words := strings.Fields(line)

		if len(words) == 2 {

			lib, path := words[0], words[1]

			if v {
				rd := RecursiveData{
					data:     data,
					glMap:    lddMap,
					printDep: nil,
					cmd:      "ldd " + path + " | awk '/ => / { print $1,$3 }'",
					line:     lib,
					listStr:  listLdd,
					level:    -1,
				}
				listLdd = append(listLdd, lib)
				parseRecursive(rd)
			} else {
				data[lib] = nil
			}
		}
	}
	return listLdd
}

// parseRecursive is used by ParseDependencies and ParseLDD to factorize code.
//
func parseRecursive(rD RecursiveData) {

	if _, in := rD.glMap[rD.line]; in {
		// Use additional map to avoid executing again ldd
		rD.data[rD.line] = rD.glMap[rD.line]
	} else {

		var libsAcc []string
		out, err := util_tools.ExecutePipeCommand(rD.cmd)
		if err != nil {
			util_tools.PrintErr(err)
		}

		if rD.printDep == nil {
			libsAcc = ParseLDD(out, rD.data, rD.glMap, true)
		} else {
			libsAcc = ParseDependencies(out, rD.data, rD.glMap, rD.printDep,
				true, rD.level+1)
		}

		// Add return libsAcc to map
		rD.data[rD.line] = libsAcc
		rD.glMap[rD.line] = libsAcc
	}
}
