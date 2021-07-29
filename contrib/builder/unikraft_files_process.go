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
	"errors"
	"fmt"
	"os"
	"path/filepath"
	u "github.com/unikraft/kraft/contrib/common"
)

// ---------------------------Create Include Folder-----------------------------

func createIncludeFolder(appFolder string) (*string, error) {

	includeFolder := appFolder + u.INCLUDEFOLDER
	if _, err := u.CreateFolder(includeFolder); err != nil {
		return nil, err
	}

	return &includeFolder, nil
}

// ----------------------------Set UNIKRAFT Folders-----------------------------
func setUnikraftFolder(homeDir string) (*string, error) {

	unikraftFolder := homeDir + u.UNIKRAFTFOLDER

	created, err := u.CreateFolder(unikraftFolder)
	if err != nil {
		return nil, err
	}

	if created {
		setUnikraftSubFolders(unikraftFolder)
	} else {
		u.PrintInfo("Unikraft folder already exists")
		return &unikraftFolder, nil
	}

	return &unikraftFolder, nil
}

func setUnikraftSubFolders(unikraftFolder string) (*string, error) {

	u.PrintInfo("Create Unikraft folder with apps and libs subfolders")

	// Create 'apps' and 'libs' subfolders
	if _, err := u.CreateFolder(unikraftFolder + u.APPSFOLDER); err != nil {
		return nil, err
	}

	if _, err := u.CreateFolder(unikraftFolder + u.LIBSFOLDER); err != nil {
		return nil, err
	}

	// Download git repo of unikraft
	if _, _, err := u.GitCloneRepository("git://xenbits.xen.org/unikraft/unikraft.git",
		unikraftFolder, true); err != nil {
		return nil, err
	}

	// Use staging branch
	if _, _, err := u.GitBranchStaging(unikraftFolder+"unikraft", true); err != nil {
		return nil, err
	}

	return &unikraftFolder, nil
}

// ---------------------------Check UNIKRAFT Folder-----------------------------

func containsUnikraftFolders(files []os.FileInfo) bool {

	if len(files) == 0 {
		return false
	}

	m := make(map[string]bool)
	m[u.APPSFOLDER], m[u.LIBSFOLDER], m[u.UNIKRAFTFOLDER] = false, false, false

	var folderName string
	for _, f := range files {
		folderName = f.Name() + u.SEP
		if _, ok := m[folderName]; ok {
			m[folderName] = true
		}
	}

	return m[u.APPSFOLDER] == true && m[u.LIBSFOLDER] && m[u.UNIKRAFTFOLDER]
}

// ---------------------------UNIKRAFT APP FOLDER-------------------------------

func createUnikraftApp(programName, unikraftPath string) (*string, error) {

	var appFolder string
	if unikraftPath[len(unikraftPath)-1] != os.PathSeparator {
		appFolder = unikraftPath + u.SEP + u.APPSFOLDER + programName + u.SEP
	} else {
		appFolder = unikraftPath + u.APPSFOLDER + programName + u.SEP
	}

	created, err := u.CreateFolder(appFolder)
	if err != nil {
		return nil, err
	}

	if !created {
		u.PrintWarning(appFolder + " already exists.")
		handleCreationApp(&appFolder)
	}

	return &appFolder, nil
}

// -----------------------------Create App folder-------------------------------

func handleCreationApp(appFolder *string) {
	fmt.Println("Make your choice:\n1: Copy and overwrite files\n2: " +
		"Enter manually the name of the folder\n3: exit program")
	var input int
	for true {
		fmt.Print("Please enter your choice (0 to exit): ")
		if _, err := fmt.Scanf("%d", &input); err != nil {
			u.PrintWarning("Choice must be numeric! Try again")
		} else {
			switch input {
			case 1:
				return
			case 2:
				fmt.Print("Enter text: ")
				reader := bufio.NewReader(os.Stdin)
				text, _ := reader.ReadString('\n')
				appFolder = &text
				return
			case 3:
				os.Exit(1)
			default:
				u.PrintWarning("Invalid input! Try again")
			}
		}
	}
}

// -------------------------MOVE FILES TO APP FOLDER----------------------------

var srcLanguages = map[string]int{
	".c":   0,
	".cpp": 0,
	".cc":  0,
	".S":   0,
	".asm": 0,
	//".py":  0,
	//".go":  0,
}

func processSourceFiles(sourcesPath, appFolder, includeFolder string,
	sourceFiles, includesFiles []string) ([]string, error) {

	err := filepath.Walk(sourcesPath, func(path string, info os.FileInfo,
		err error) error {

		if !info.IsDir() {
			extension := filepath.Ext(info.Name())
			if _, ok := srcLanguages[extension]; ok {
				// Add source files to sourceFiles list
				sourceFiles = append(sourceFiles, info.Name())

				// Count the number of extension
				srcLanguages[extension] += 1

				// Copy source files to the appFolder
				if err = u.CopyFileContents(path, appFolder+info.Name()); err != nil {
					return err
				}
			} else if extension == ".h" {
				// Add source files to includesFiles list
				includesFiles = append(includesFiles, info.Name())

				// Copy header files to the INCLUDEFOLDER
				if err = u.CopyFileContents(path, includeFolder+info.Name()); err != nil {
					return err
				}
			} else {
				u.PrintWarning("Unsupported extension for file: " + info.Name())
			}
		}

		return nil
	})

	if err != nil {
		return nil, err
	}

	// If no source file, exit the program
	if len(sourceFiles) == 0 {
		return nil, errors.New("unable to find source files")
	}

	return sourceFiles, nil
}

func languageUsed() string {

	max := -1
	var mostUsedFiles string
	for key, value := range srcLanguages {
		if max < value {
			max = value
			mostUsedFiles = key
		}
	}

	return mostUsedFiles
}
