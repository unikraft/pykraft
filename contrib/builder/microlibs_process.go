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
	"io/ioutil"
	"strings"
	"sync"
	u "github.com/unikraft/kraft/contrib/common"
)

const (
	exportFile = "exportsyms.uk"
	prefixUrl  = "http://xenbits.xen.org/gitweb/?p=unikraft/libs/"
	suffixUrl  = ";a=blob_plain;f=exportsyms.uk;hb=refs/heads/staging"
)

// -----------------------------Match micro-libs--------------------------------

// processSymbols adds symbols within the 'exportsyms.uk' file into a map.
//
func processSymbols(microLib, output string, mapSymbols map[string][]string) {

	lines := strings.Split(output, "\n")
	for _, line := range lines {
		if len(line) > 0 && !strings.Contains(line, "#") &&
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
			export := unikraftLibs + f.Name() + u.SEP + exportFile
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
				if symbols, err := u.DownloadFile(prefixUrl + git + suffixUrl); err != nil {
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
func matchLibs(unikraftLibs string, data *u.Data) ([]string, map[string]string, error) {

	mapSymbols := make(map[string][]string)

	matchedLibs := make([]string, 0)
	if err := fetchSymbolsInternalLibs(unikraftLibs, mapSymbols); err != nil {
		return nil, nil, err
	}

	// Get list of libs from xenbits
	url := "http://xenbits.xen.org/gitweb/?pf=unikraft/libs"
	externalLibs, err := fetchSymbolsExternalLibs(url, mapSymbols)
	if err != nil {
		return nil, nil, err
	}

	// Perform the matching symbols on static data
	matchedLibs = matchSymbols(matchedLibs, data.StaticData.Symbols, mapSymbols)

	// Perform the matching symbols on dynamic data
	matchedLibs = matchSymbols(matchedLibs, data.DynamicData.Symbols, mapSymbols)

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
			exists, _ := u.Exists(unikraftPath + u.LIBSFOLDER + lib)
			if !exists {
				// If the micro-libs is not in the local host, clone it
				if err := cloneGitRepo("git://xenbits.xen.org/unikraft/"+
					"libs/"+lib+".git", unikraftPath+u.LIBSFOLDER); err != nil {
					u.PrintWarning(err)
				}
			} else {
				u.PrintInfo("Library " + lib + " already exists in folder" +
					unikraftPath + u.LIBSFOLDER)
			}
		}
	}
}
