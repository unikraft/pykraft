// Copyright 2019 The UNICORE Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file
//
// Author: Gaulthier Gain <gaulthier.gain@uliege.be>

package buildtool

import (
	"bufio"
	"errors"
	"fmt"
	"os"
	"path/filepath"

	u "tools/common"
)

// Folder
const (
	APPSFOLDER     = "apps" + u.SEP
	UNIKRAFTFOLDER = "unikraft" + u.SEP
	LIBSFOLDER     = "libs" + u.SEP
	INCLUDEFOLDER  = "include" + u.SEP
)

// ---------------------------Create Include Folder-----------------------------

func createIncludeFolder(appFolder string) (*string, error) {

	if _, err := u.CreateFolder(appFolder, INCLUDEFOLDER); err != nil {
		return nil, err
	}

	includeFolder := appFolder + INCLUDEFOLDER
	return &includeFolder, nil
}

// ----------------------------Set UNIKRAFT Folders-----------------------------
func setUnikraftFolder(homeDir string) (*string, error) {

	unikraftFolder := homeDir + UNIKRAFTFOLDER

	created, err := u.CreateFolder(homeDir, UNIKRAFTFOLDER)
	if err != nil {
		return nil, err
	}

	if created {
		u.PrintInfo("Create Unikraft folder with apps and libs subfolders")

		// Create 'apps' and 'libs' subfolders
		if _, err := u.CreateFolder(unikraftFolder, APPSFOLDER); err != nil {
			return nil, err
		}

		if _, err := u.CreateFolder(unikraftFolder, LIBSFOLDER); err != nil {
			return nil, err
		}

		// Download git repo of unikraft
		if _, _, err := u.GitCloneRepository("git://xenbits.xen.org/unikraft/unikraft.git",
			unikraftFolder, true); err != nil {
			return nil, err
		}

		// Use staging branch
		if _, _, err := u.GitBranchStaging(unikraftFolder+"unikraft", true);
			err != nil {
			return nil, err
		}

	} else {
		u.PrintInfo("Unikraft folder already exists")
		return &unikraftFolder, nil
	}

	return &unikraftFolder, nil
}

// ---------------------------Check UNIKRAFT Folder-----------------------------

func ContainsUnikraftFolders(files []os.FileInfo) bool {

	if len(files) == 0 {
		return false
	}

	m := make(map[string]bool)
	m[APPSFOLDER], m[LIBSFOLDER], m[UNIKRAFTFOLDER] = false, false, false

	var folderName string
	for _, f := range files {
		folderName = f.Name() + u.SEP
		if _, ok := m[folderName]; ok {
			m[folderName] = true
		}
	}

	return m[APPSFOLDER] == true && m[LIBSFOLDER] && m[UNIKRAFTFOLDER]
}

// ---------------------------UNIKRAFT APP FOLDER-------------------------------

func createUnikraftApp(programName, unikraftPath string) (*string, error) {

	var appFolder string
	if unikraftPath[len(unikraftPath)-1] != os.PathSeparator {
		appFolder = unikraftPath + u.SEP + APPSFOLDER
	} else {
		appFolder = unikraftPath + APPSFOLDER
	}

	created, err := u.CreateFolder(appFolder, programName)
	if err != nil {
		return nil, err
	}

	if created {
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
	".py":  0,
	".go":  0,
}

func ProcessSourceFiles(sourcesPath, appFolder, includeFolder string,
	sourceFiles, includesFiles []string) error {

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
		return err
	}

	// If no source file, exit the program
	if len(sourceFiles) == 0 {
		return errors.New("unable to find source files")
	}

	return nil
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
