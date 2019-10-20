// Copyright 2019 The UNICORE Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file
//
// Author: Gaulthier Gain <gaulthier.gain@uliege.be>

package buildtool

import (
	"io/ioutil"
	"os"
	"strings"
	"sync"

	u "tools/common"
)

const (
	EXPORT_FILE = "exportsyms.uk"
	PREFIX_URL  = "http://xenbits.xen.org/gitweb/?p=unikraft/libs/"
	SUFFIX_URL  = ";a=blob_plain;f=exportsyms.uk;hb=refs/heads/staging"
)

// -----------------------------Match micro-libs--------------------------------

// processSymbols adds symbols within the 'exportsyms.uk' file into a map.
//
func processSymbols(microLib, output string, mapSymbols map[string][]string) {

	lines := strings.Split(output, "\n")
	for _, line := range lines {
		if len(line) > 0 && !strings.Contains(line, "#") ||
			strings.Compare(line, "none") != 0 {
			mapSymbols[line] = append(mapSymbols[line], microLib)
		}
	}
}

// fetchSymbolsInternalLibs fetches all symbols within 'exportsyms.uk' files
// from Unikraft's internal libs and add them into a map.
//
// It returns an error if any, otherwise it returns nil.
func fetchSymbolsInternalLibs(unikraftLibs string,
	microLibs map[string][]string) error {

	// Read files within the Unikraft directory
	files, err := ioutil.ReadDir(unikraftLibs)
	if err != nil {
		return err
	}

	// Read Unikraft internal libs symbols (exportsyms.uk)
	for _, f := range files {
		if f.IsDir() {
			export := unikraftLibs + f.Name() + string(os.PathSeparator) +
				EXPORT_FILE
			if exists, _ := u.Exists(export); exists {
				u.PrintInfo("Retrieving symbols of internal lib: " + f.Name())
				b, _ := u.OpenTextFile(export)
				processSymbols(f.Name(), string(b), microLibs)
			}
		}
	}
	return nil
}

// fetchSymbolsExternalLibs fetches all symbols within 'exportsyms.uk' files
// from Unikraft's external libs and add them into a map.
//
// It returns a list of symbols and an error if any, otherwise it returns nil.
func fetchSymbolsExternalLibs(url string,
	microLibs map[string][]string) (map[string]string, error) {

	var externalLibs map[string]string
	if body, err := u.DownloadFile(url); err != nil {
		return nil, err
	} else {
		externalLibs = u.GitFindExternalLibs(*body)

		var wg sync.WaitGroup
		wg.Add(len(externalLibs))
		// Iterate through all external libs to parse 'exportsyms.uk' file
		for lib, git := range externalLibs {
			// Use go routine to get better efficiency
			go func(lib, git string, microLibs map[string][]string) {
				defer wg.Done()
				u.PrintInfo("Retrieving symbols of external lib: " + lib)
				if symbols, err := u.DownloadFile(PREFIX_URL + git + SUFFIX_URL); err != nil {
					u.PrintWarning(err)
				} else {
					processSymbols(lib, *symbols, microLibs)
				}
			}(lib, git, microLibs)
		}
		wg.Wait()
	}
	return externalLibs, nil
}

// matchSymbols performs the matching between Unikraft's micro-libs and
// libraries used by a given application based on the list of symbols that both
// contain.
//
// It returns a list of micro-libs that are required by the application
func matchSymbols(matchedLibs []string, data map[string]string,
	microLibs map[string][]string) []string {
	for key := range data {
		if values, ok := microLibs[key]; ok {
			for _, value := range values {

				// todo remove
				if strings.Compare(NOLIBC, value) == 0 {
					value = NEWLIB
				}
				// remove above

				if !u.Contains(matchedLibs, value) {
					matchedLibs = append(matchedLibs, value)
					u.PrintOk("Match lib: " + value)
				}
			}
		}
	}

	return matchedLibs
}

// matchLibs performs the matching between Unikraft's micro-libs and
// libraries used by a given application
//
// It returns a list of micro-libs that are required by the application and an
// error if any, otherwise it returns nil.
func matchLibs(unikraftLibs string, data *u.Data,
	microLibs map[string][]string) ([]string, map[string]string, error) {

	matchedLibs := make([]string, 0)
	if err := fetchSymbolsInternalLibs(unikraftLibs, microLibs); err != nil {
		u.PrintErr(err)
	}

	// Get list of libs from xenbits
	url := "http://xenbits.xen.org/gitweb/?pf=unikraft/libs"
	externalLibs, err := fetchSymbolsExternalLibs(url, microLibs)
	if err != nil {
		return nil, nil, err
	}

	// Perform the matching symbols on static data
	matchedLibs = matchSymbols(matchedLibs, data.StaticData.Symbols, microLibs)

	// Perform the matching symbols on dynamic data
	matchedLibs = matchSymbols(matchedLibs, data.DynamicData.Symbols, microLibs)

	return matchedLibs, externalLibs, nil
}

// -----------------------------Clone micro-libs--------------------------------

// cloneGitRepo clones a specific git repository that hosts an external
// micro-libs on http://xenbits.xen.org/
//
// It returns an error if any, otherwise it returns nil.
func cloneGitRepo(url, unikraftPathLibs string) error {

	u.PrintInfo("Clone git repository " + url)
	if _, _, err := u.GitCloneRepository(url, unikraftPathLibs, true); err != nil {
		return err
	}
	u.PrintOk("Git repository " + url + " has been cloned into " +
		unikraftPathLibs)

	u.PrintInfo("Git branch " + url)
	if _, _, err := u.GitBranchStaging(unikraftPathLibs, true); err != nil {
		return err
	}

	return nil
}

// cloneLibsFolders clones all the needed micro-libs that are needed by a
// given application
//
func cloneLibsFolders(unikraftPath string, matchedLibs []string,
	externalLibs map[string]string) {

	for _, lib := range matchedLibs {
		if _, ok := externalLibs[lib]; ok {
			exists, _ := u.Exists(unikraftPath + LIBS_FOLDER + lib)
			if !exists {
				// If the micro-libs is not in the local host, clone it
				if err := cloneGitRepo("git://xenbits.xen.org/unikraft/"+
					"libs/"+lib+".git", unikraftPath+LIBS_FOLDER); err != nil {
					u.PrintWarning(err)
				}
			} else {
				u.PrintInfo("Library " + lib + " already exists in folder" +
					unikraftPath + LIBS_FOLDER)
			}
		}
	}
}
