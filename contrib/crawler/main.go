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
	"os"
	"path/filepath"
	"strings"
	"time"
	u "github.com/unikraft/kraft/contrib/common"
)

// RunCrawler allows to run the crawler analyser tool (which is out of the
// UNICORE toolchain).
func main() {

	mapLabel := make(map[string]string)
	mapConfig := make(map[string][]string)

	// Init and parse local arguments
	args := new(u.Arguments)
	p, err := args.InitArguments("kraft-devel-crawler",
		"")
	if err != nil {
		u.PrintErr(err)
	}
	if err := parseLocalArguments(p, args); err != nil {
		u.PrintErr(err)
	}

	// Used to select all libraries (even those below another Config fields)
	fullSelect := *args.BoolArg[fullLibsArg]

	var path string
	if len(*args.StringArg[repoArg]) > 0 {
		// Only one folder
		path = *args.StringArg[repoArg]
		u.PrintInfo("Parse folder: " + path)
		if err := searchConfigUK(path, fullSelect, mapConfig, mapLabel); err != nil {
			u.PrintErr()
		}

	} else if len(*args.StringArg[libsArg]) > 0 {

		// Several folders within a list
		lines, err := u.ReadLinesFile(*args.StringArg[libsArg])
		if err != nil {
			u.PrintErr(err)
		}

		// Process Config.uk of each process
		for _, line := range lines {
			path = strings.TrimSuffix(line, "\n")
			u.PrintInfo("Parse folder: " + path)
			if err := searchConfigUK(path, fullSelect, mapConfig, mapLabel); err != nil {
				u.PrintErr(err)
			}
		}
	} else {
		u.PrintErr("You must specify either -r (--repository) or -l (libs)")
	}

	// Generate the out folder
	outFolder := *args.StringArg[outputArg]
	if outFolder[len(outFolder)-1:] != string(os.PathSeparator) {
		outFolder += string(os.PathSeparator)
	}

	outputPath := outFolder +
		"output_" + time.Now().Format("20060102150405")

	// Create the dependencies graph
	u.GenerateGraph("Unikraft Crawler", outputPath, mapConfig,
		mapLabel)

	u.PrintOk(".dot file is saved: " + outputPath)
}

// searchConfigUK performs a look-up to find "Config.uk" files.
//
// It returns an error if any, otherwise it returns nil.
func searchConfigUK(path string, fullSelect bool,
	mapConfig map[string][]string, mapLabel map[string]string) error {

	err := filepath.Walk(path, func(path string, info os.FileInfo,
		err error) error {
		if err != nil {
			return err
		}

		// Consider only CONFIGUK files
		if !info.IsDir() && info.Name() == u.CONFIGUK {
			lines, err := u.ReadLinesFile(path)
			if err != nil {
				return err
			}
			u.ProcessConfigUK(lines, fullSelect, mapConfig, mapLabel)
		}

		return nil
	})

	if err != nil {
		return err
	}

	return nil
}
