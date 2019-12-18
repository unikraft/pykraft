// Copyright 2019 The UNICORE Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file
//
// Author: Gaulthier Gain <gaulthier.gain@uliege.be>

package crawlertool

import (
	"os"
	"path/filepath"
	"strings"
	"time"
	u "tools/srcs/common"
)

// RunCrawler allows to run the crawler analyser tool (which is out of the
// UNICORE toolchain).
func RunCrawler() {

	mapLabel := make(map[string]string)
	mapConfig := make(map[string][]string)

	// Init and parse local arguments
	args := new(u.Arguments)
	p, err := args.InitArguments()
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
