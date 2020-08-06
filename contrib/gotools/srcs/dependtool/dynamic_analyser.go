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

package dependtool

import (
	"encoding/json"
	"errors"
	"io/ioutil"
	"os"
	"strconv"
	"strings"
	"syscall"
	u "tools/srcs/common"
)

// Exported struct that represents the arguments for dynamic analysis.
type DynamicArgs struct {
	waitTime             int
	fullDeps, saveOutput bool
	testFile             string
	options              []string
}

const (
	systrace = "strace"
	libtrace = "ltrace"
)

// ---------------------------------Read Json-----------------------------------

// readTestFileJson load Testing json from a json file named by filename.
//
// It returns a Testing structure initialized and an error if any, otherwise it
// returns nil.
func readTestFileJson(filename string) (*Testing, error) {

	testingStruct := &Testing{}
	jsonFile, err := os.Open(filename)
	if err != nil {
		return nil, err
	}
	defer jsonFile.Close()

	byteValue, err := ioutil.ReadAll(jsonFile)
	if err != nil {
		return nil, err
	}

	if err = json.Unmarshal(byteValue, &testingStruct); err != nil {
		return nil, err
	}

	if testingStruct.ListCommands == nil || len(testingStruct.ListCommands) == 0 {
		return nil, errors.New("ListCommands cannot be empty")
	}

	return testingStruct, nil
}

// --------------------------------Gather Data----------------------------------

// gatherDataAux gathers symbols and system calls of a given application (helper
// function.
//
// It returns true if a command must be run with sudo.
func gatherDataAux(command, programPath, programName, option string,
	data *u.DynamicData, dArgs DynamicArgs) bool {

	testingStruct := &Testing{}
	if len(dArgs.testFile) > 0 {
		var err error
		testingStruct, err = readTestFileJson(dArgs.testFile)
		if err != nil {
			u.PrintWarning("Cannot find test file: " + err.Error())
		}
	}
	_, errStr := runCommandTester(programPath, programName, command, option,
		testingStruct, dArgs, data)

	ret := false
	if command == systrace {
		ret = parseTrace(errStr, data.SystemCalls)
	} else {
		ret = parseTrace(errStr, data.Symbols)
	}
	return ret
}

// gatherData gathers symbols and system calls of a given application.
//
func gatherData(command, programPath, programName string,
	data *u.DynamicData, dArgs DynamicArgs) {

	if len(dArgs.options) > 0 {
		// Iterate through configs present in config file
		for _, option := range dArgs.options {
			// Check if program name is used in config file
			if strings.Contains(option, programName) {
				// If yes, take only arguments
				split := strings.Split(option, programName)
				option = strings.TrimSuffix(strings.Replace(split[1],
					" ", "", -1), "\n")
			}

			u.PrintInfo("Run " + programName + " with option: '" +
				option + "'")
			if requireSudo := gatherDataAux(command, programPath, programName,
				option, data, dArgs); requireSudo {
				u.PrintErr(programName + " requires superuser " +
					"privileges: Run command with sudo")
			}
		}
	} else {
		// Run without option/config
		if requireSudo := gatherDataAux(command, programPath, programName,
			"", data, dArgs); requireSudo {
			u.PrintErr(programName + " requires superuser " +
				"privileges: Run command with sudo")
		}
	}
}

// gatherDynamicSharedLibs gathers shared libraries of a given application.
//
// It returns an error if any, otherwise it returns nil.
func gatherDynamicSharedLibs(programName string, pid int, data *u.DynamicData,
	fullDeps bool) error {

	// Get the pid
	pidStr := strconv.Itoa(pid)
	u.PrintInfo("PID '" + programName + "' : " + pidStr)

	// Use 'lsof' to get open files and thus .so files
	if output, err := u.ExecutePipeCommand(
		"lsof -p " + pidStr + " | uniq | awk '{print $9}'"); err != nil {
		return err
	} else {
		// Parse 'lsof' output
		if err := parseLsof(output, data, fullDeps); err != nil {
			u.PrintErr(err)
		}
	}

	// Use 'cat /proc/pid' to get open files and thus .so files
	if output, err := u.ExecutePipeCommand(
		"cat /proc/" + pidStr + "/maps | awk '{print $6}' | " +
			"grep '\\.so' | sort | uniq"); err != nil {
		return err
	} else {
		// Parse 'cat' output
		if err := parseLsof(output, data, fullDeps); err != nil {
			u.PrintErr(err)
		}
	}

	return nil
}

// ------------------------------------ARGS-------------------------------------

// getDArgs returns a DynamicArgs struct which contains arguments specific to
// the dynamic dependency analysis.
//
// It returns a DynamicArgs struct.
func getDArgs(args *u.Arguments, options []string) DynamicArgs {
	return DynamicArgs{*args.IntArg[waitTimeArg],
		*args.BoolArg[fullDepsArg], *args.BoolArg[saveOutputArg],
		*args.StringArg[testFileArg], options}
}

// -------------------------------------RUN-------------------------------------

// RunDynamicAnalyser runs the dynamic analysis to get shared libraries,
// system calls and library calls of a given application.
//
func dynamicAnalyser(args *u.Arguments, data *u.Data, programPath string) {

	// Check options
	var configs []string
	if len(*args.StringArg[configFileArg]) > 0 {
		// Multi-lines options (config)
		var err error
		configs, err = u.ReadLinesFile(*args.StringArg[configFileArg])
		if err != nil {
			u.PrintWarning(err)
		}
	} else if len(*args.StringArg[optionsArg]) > 0 {
		// Single option (config)
		configs = append(configs, *args.StringArg[optionsArg])
	}

	// Get dynamic structure
	dArgs := getDArgs(args, configs)
	programName := *args.StringArg[programArg]

	// Kill process if it is already launched
	u.PrintInfo("Kill '" + programName + "' if it is already launched")
	if err := u.PKill(programName, syscall.SIGINT); err != nil {
		u.PrintErr(err)
	}

	// Init dynamic data
	dynamicData := &data.DynamicData
	dynamicData.SharedLibs = make(map[string][]string)
	dynamicData.SystemCalls = make(map[string]string)
	dynamicData.Symbols = make(map[string]string)

	// Run strace
	u.PrintHeader2("(*) Gathering system calls from ELF file")
	gatherData(systrace, programPath, programName, dynamicData, dArgs)

	// Kill process if it is already launched
	u.PrintInfo("Kill '" + programName + "' if it is already launched")
	if err := u.PKill(programName, syscall.SIGINT); err != nil {
		u.PrintErr(err)
	}

	// Run ltrace
	u.PrintHeader2("(*) Gathering symbols from ELF file")
	gatherData(libtrace, programPath, programName, dynamicData, dArgs)
}
