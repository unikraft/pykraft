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
	APPS_FOLDER     = "apps/"
	UNIKRAFT_FOLDER = "unikraft/"
	LIBS_FOLDER     = "libs/"
	INCLUDE_FOLDER  = "include/"
)

// ---------------------------Create Include Folder-----------------------------

func createIncludeFolder(appFolder string) (*string, error) {

	if _, err := u.CreateFolder(appFolder, INCLUDE_FOLDER); err != nil {
		return nil, err
	}

	includeFolder := appFolder + INCLUDE_FOLDER
	return &includeFolder, nil
}

// ----------------------------Set UNIKRAFT Folders-----------------------------
func setUnikraftFolder(homeDir string) (*string, error) {

	unikraftFolder := homeDir + UNIKRAFT_FOLDER

	created, err := u.CreateFolder(homeDir, UNIKRAFT_FOLDER)
	if err != nil {
		return nil, err
	}

	if created {
		// Create 'apps' and 'libs' subfolders
		if _, err := u.CreateFolder(unikraftFolder, APPS_FOLDER); err != nil {
			return nil, err
		}

		if _, err := u.CreateFolder(unikraftFolder, LIBS_FOLDER); err != nil {
			return nil, err
		}

		// Download git repo of unikraft
		if _, _, err := u.GitCloneRepository("git://xenbits.xen.org/unikraft/unikraft.git",
			unikraftFolder, true); err != nil {
			return nil, err
		}

	} else {
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
	m[APPS_FOLDER], m[LIBS_FOLDER], m[UNIKRAFT_FOLDER] = false, false, false

	var folderName string
	for _, f := range files {
		folderName = f.Name() + string(os.PathSeparator)
		if _, ok := m[folderName]; ok {
			m[folderName] = true
		}
	}

	return m[APPS_FOLDER] == true && m[LIBS_FOLDER] && m[UNIKRAFT_FOLDER]
}

// ---------------------------UNIKRAFT APP FOLDER-------------------------------

func createUnikraftApp(programName, unikraftPath string) string {

	var appFolder string
	sep := string(os.PathSeparator)
	if unikraftPath[len(unikraftPath)-1] != os.PathSeparator {
		appFolder = unikraftPath + sep + APPS_FOLDER + programName + sep
	} else {
		appFolder = unikraftPath + APPS_FOLDER + programName + sep
	}

	// Create the folder 'appFolder' if it does not exist
	if _, err := os.Stat(appFolder); os.IsNotExist(err) {
		if err = os.Mkdir(appFolder, u.PERM); err != nil {
			u.PrintErr(err)
		}
	} else {
		u.PrintWarning(appFolder + " already exists.")
		handleCreationApp(&appFolder)
	}

	return appFolder
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

			// Copy header files to the INCLUDE_FOLDER
			if err = u.CopyFileContents(path, includeFolder+info.Name()); err != nil {
				return err
			}
		} else {
			u.PrintWarning("Unsupported extension for file: " + info.Name())
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
