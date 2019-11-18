// Copyright 2019 The UNICORE Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file
//
// Author: Gaulthier Gain <gaulthier.gain@uliege.be>

package buildtool

import (
	"errors"
	"io/ioutil"
	"os"
	"path/filepath"
	"regexp"
	"strings"

	u "tools/common"
)

// STATES
const (
	compilerError = iota
	linkingError
	success
)

// -----------------------------Generate Config---------------------------------

// generateConfigUk generates a 'Config.uk' file for the Unikraft build system.
//
// It returns an error if any, otherwise it returns nil.
func generateConfigUk(filename, programName string, matchedLibs []string) error {

	var sb strings.Builder
	sb.WriteString("### Invisible option for dependencies\n" +
		"config APP" + programName + "_DEPENDENCIES\n" + "\tbool\n" +
		"\tdefault y\n")

	for _, lib := range matchedLibs {
		sb.WriteString("\tselect " + lib + "\n")
	}

	// Save the content to Makefile.uk
	return u.WriteToFile(filename, []byte(sb.String()))
}

// ---------------------------Process make output-------------------------------

// checkMakeOutput checks if errors or warning are displayed during the
// execution of the 'make' command.
//
// It returns an integer that defines the result of 'make':
// 	<SUCCESS, LINKING_ERROR, COMPILER_ERROR>
func checkMakeOutput(appFolder string, stderr *string) int {

	if stderr == nil {
		return success
	}

	// Linking errors during make
	if strings.Contains(*stderr, "undefined") {

		str := parseMakeOutput(*stderr)
		if len(str) > 0 {
			if err := u.WriteToFile(appFolder+"stub.c", []byte(str)); err != nil {
				u.PrintWarning(err)
			}
		}

		return linkingError
	}

	// Compiler errors during make
	if strings.Contains(*stderr, "error:") {

		return compilerError
	}

	return success
}

// parseMakeOutput parses the output of the 'make' command.
//
// It returns a string that contains stubs of undefined function(s).
func parseMakeOutput(output string) string {

	var sb strings.Builder
	sb.WriteString("#include <stdio.h>\n")

	undefinedSymbols := make(map[string]*string)
	var re = regexp.MustCompile(`(?mi).*undefined reference to\s\x60(.*)'`)
	for _, match := range re.FindAllStringSubmatch(output, -1) {
		if _, ok := undefinedSymbols[match[1]]; !ok {
			sb.WriteString("void ")
			sb.WriteString(match[1])
			sb.WriteString("(void){\n\tprintf(\"STUB\\n\");\n}\n\n")
			undefinedSymbols[match[1]] = nil
			u.PrintInfo("Add stub to function: " + match[1])
		}
	}

	return sb.String()
}

// -------------------------------------Run-------------------------------------

// RunBuildTool runs the automatic build tool to build a unikernel of a
// given application.
//
func RunBuildTool(homeDir string, data *u.Data) {

	// Init and parse local arguments
	args := new(u.Arguments)
	p, err := args.InitArguments()
	if err != nil {
		u.PrintErr(err)
	}
	if err := parseLocalArguments(p, args); err != nil {
		u.PrintErr(err)
	}

	// Get program Name
	programName := *args.StringArg[PROGRAM]

	// Take base path if absolute path is used
	if filepath.IsAbs(programName) {
		programName = filepath.Base(programName)
	}

	var unikraftPath string
	if len(*args.StringArg[UNIKRAFT]) == 0 {
		path, err := setUnikraftFolder(homeDir + u.SEP)
		if err != nil {
			u.PrintErr(err)
		}
		unikraftPath = *path
	} else {
		unikraftPath = *args.StringArg[UNIKRAFT]
	}

	// Check if sources argument is set
	if len(*args.StringArg[SOURCES]) == 0 {
		u.PrintErr("sources argument '-s' must be set")
	}

	// Check if the unikraft folder contains the 3 required folders
	if folder, err := ioutil.ReadDir(unikraftPath); err != nil {
		u.PrintErr(err)
	} else {
		if !ContainsUnikraftFolders(folder) {
			u.PrintErr(errors.New("unikraft, apps and libs folders must exist"))
		}
	}

	// If data is not initialized, read output from dependency analysis tool
	if data == nil {
		u.PrintInfo("Initialize data")
		outFolder := homeDir + u.SEP + programName + "_" + u.OUTFOLDER
		if data, err = u.ReadDataJson(outFolder+programName, data); err != nil {
			u.PrintErr(err)
		}
	}

	// Create unikraft application path
	appFolderPtr, err := createUnikraftApp(programName, unikraftPath)
	if err != nil {
		u.PrintErr(err)
	}
	appFolder := *appFolderPtr

	// Create the folder 'include' if it does not exist
	includeFolder, err := createIncludeFolder(appFolder)
	if err != nil {
		u.PrintErr(err)
	}

	// Get sources files
	sourcesPath := *args.StringArg[SOURCES]

	// Copy all .h into the include folder
	sourceFiles, includesFiles := make([]string, 0), make([]string, 0)

	// Move source files to Unikraft folder
	if err = ProcessSourceFiles(sourcesPath, appFolder, *includeFolder,
		sourceFiles, includesFiles); err != nil {
		u.PrintErr(err)
	}

	// Match micro-libs
	matchedLibs, externalLibs, err := matchLibs(unikraftPath+"unikraft"+u.SEP+
		"lib"+u.SEP, data)
	if err != nil {
		u.PrintErr(err)
	}

	// Clone the external git repositories
	cloneLibsFolders(unikraftPath, matchedLibs, externalLibs)

	// Match internal dependencies between micro-libs
	if err := searchInternalDependencies(unikraftPath, &matchedLibs,
		externalLibs); err != nil {
		u.PrintErr(err)
	}

	for _, lib := range matchedLibs {
		u.PrintOk("Match lib: " + lib)
	}

	// Clone the external git repositories (if changed)
	cloneLibsFolders(unikraftPath, matchedLibs, externalLibs)

	// Generate Makefiles
	if err := generateMake(programName, appFolder, unikraftPath, *args.StringArg[MAKEFILE],
		matchedLibs, sourceFiles, externalLibs); err != nil {
		u.PrintErr(err)
	}

	// Delete Build folder
	deleteBuildFolder(appFolder)

	// Initialize config files
	initConfig(appFolder, matchedLibs)

	// Run make
	runMake(programName, appFolder)
}

func searchInternalDependencies(unikraftPath string, matchedLibs *[]string,
	externalLibs map[string]string) error {

	for _, lib := range *matchedLibs {
		// Consider only external libs
		if _, ok := externalLibs[lib]; ok {

			// Get and read Config.UK from external lib
			configUk := unikraftPath + LIBSFOLDER + lib + u.SEP + "Config.uk"
			lines, err := u.ReadLinesFile(configUk)
			if err != nil {
				return err
			}

			// Process Config.UK file
			mapConfig := make(map[string][]string)
			u.ProcessConfigUK(lines, false, mapConfig, nil)

			for config := range mapConfig {

				// Remove LIB prefix
				if strings.Contains(config, "LIB") {
					config = strings.TrimPrefix(config, "LIB")
				}

				// Replace underscore by dash
				if strings.Contains(config, "_") {
					config = strings.ReplaceAll(config, "_", "-")
				}

				// Check if matchedLibs already contains the lib
				config = strings.ToLower(config)
				if !u.Contains(*matchedLibs, config) {
					*matchedLibs = append(*matchedLibs, config)
				}
			}
		}
	}

	return nil
}

func generateMake(programName, appFolder, unikraftPath, makefile string,
	matchedLibs, sourceFiles []string, externalLibs map[string]string) error {
	// Generate Makefile
	if err := generateMakefile(appFolder+"Makefile", unikraftPath,
		appFolder, matchedLibs, externalLibs); err != nil {
		return err
	}

	// Generate Config.uk
	if err := generateConfigUk(appFolder+"Config.uk",
		strings.ToUpper(programName), matchedLibs); err != nil {
		return err
	}

	// Get the file type for UNIKRAFT flag
	fileType := languageUsed()

	// Generate Makefile.uk
	if err := generateMakefileUK(appFolder+"Makefile.uk", programName,
		fileType, makefile, sourceFiles); err != nil {
		return err
	}

	return nil
}

func deleteBuildFolder(appFolder string) {
	// Delete build folder if already exists
	if file, err := u.OSReadDir(appFolder); err != nil {
		u.PrintWarning(err)
	} else {
		for _, f := range file {
			if f.IsDir() && f.Name() == "build" {
				u.PrintWarning("build folder already exists. Delete it.")
				if err := os.RemoveAll(appFolder + "build"); err != nil {
					u.PrintWarning(err)
				}
			}
		}
	}
}

func initConfig(appFolder string, matchedLibs []string) {

	// Run make allNoConfig to generate a .config file
	if strOut, strErr, err := u.ExecuteWaitCommand(appFolder, "make",
		"allnoconfig"); err != nil {
		u.PrintErr(err)
	} else if len(*strErr) > 0 {
		u.PrintErr("error during generating .config: " + *strErr)
	} else if len(*strOut) > 0 && !strings.Contains(*strOut,
		"configuration written") {
		u.PrintWarning("Default .config cannot be generated")
	}

	// Parse .config
	kConfigMap := make(map[string]*KConfig)
	items := make([]*KConfig, 0)
	items, err := parseConfig(appFolder+".config", kConfigMap, items,
		matchedLibs)
	if err != nil {
		u.PrintErr(err)
	}

	// Update .config
	items = updateConfig(kConfigMap, items)

	// Write .config
	if err := writeConfig(appFolder+".config", items); err != nil {
		u.PrintErr(err)
	}
}

func runMake(programName, appFolder string) {
	// Run make
	stdout, stderr, _ := u.ExecuteRunCmd("make", appFolder, true)

	// Check the state of the make command
	state := checkMakeOutput(appFolder, stderr)
	if state == linkingError {

		// Add new stub.c in Makefile.uk
		d := "APP" + strings.ToUpper(programName) +
			"_SRCS-y += $(APP" + strings.ToUpper(programName) +
			"_BASE)/stub.c"
		if err := u.UpdateFile(appFolder+"Makefile.uk", []byte(d)); err != nil {
			u.PrintErr(err)
		}

		// Run make a second time
		stdout, stderr, _ = u.ExecuteRunCmd("make", appFolder, true)

		// Check the state of the make command
		checkMakeOutput(appFolder, stderr)
	}

	out := appFolder + programName

	// Save make output into warnings.txt if warnings are here
	if stderr != nil && strings.Contains(*stderr, "warning:") {
		if err := u.WriteToFile(out+"_warnings.txt", []byte(*stderr)); err != nil {
			u.PrintWarning(err)
		} else {
			u.PrintInfo("Warnings are written in file: " + out + "_warnings.txt")
		}
	}

	// Save make output into output.txt
	if stdout != nil {
		if err := u.WriteToFile(out+"_output.txt", []byte(*stdout)); err != nil {
			u.PrintWarning(err)
		} else {
			u.PrintInfo("Output is written in file: " + out + "_output.txt")
		}
	}

	if state == compilerError {
		u.PrintErr("Fix compilation errors")
	} else if state == success {
		u.PrintOk("Unikernel created in Folder: 'build/'")
	}
}
