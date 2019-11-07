// Copyright 2019 The UNICORE Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file
//
// Author: Gaulthier Gain <gaulthier.gain@uliege.be>

package main

import (
	"os/user"
	"tools/buildtool"
	u "tools/common"
	"tools/crawlertool"
	"tools/dependtool"
)

func main() {

	// Init global arguments
	args := new(u.Arguments)
	parser, err := args.InitArguments()
	if err != nil {
		u.PrintErr(err)
	}

	// Parse arguments
	if err := args.ParseMainArguments(parser, args); err != nil {
		u.PrintErr(err)
	}

	// Checks if the toolchain must be completely executed
	all := false
	if !*args.BoolArg[u.DEP] && !*args.BoolArg[u.BUILD] &&
		!*args.BoolArg[u.VERIF] && !*args.BoolArg[u.PERF] {
		all = true
	}

	// Get user home folder
	usr, err := user.Current()
	if err != nil {
		u.PrintErr(err)
	}

	var data *u.Data

	if *args.BoolArg[u.CRAWLER] {
		u.PrintHeader1("(*) RUN CRAWLER UNIKRAFT ANALYSER")
		crawlertool.RunCrawler()
		return
	}

	if all || *args.BoolArg[u.DEP] {

		// Initialize data
		data = new(u.Data)

		u.PrintHeader1("(1) RUN DEPENDENCIES ANALYSER")
		dependtool.RunAnalyserTool(usr.HomeDir, data)
	}

	if all || *args.BoolArg[u.BUILD] {
		u.PrintHeader1("(2) AUTOMATIC BUILD TOOL")
		buildtool.RunBuildTool(usr.HomeDir, data)
	}

	if all || *args.BoolArg[u.VERIF] {
		u.PrintHeader1("(3) VERIFICATION TOOL")
	}

	if all || *args.BoolArg[u.PERF] {
		u.PrintHeader1("(4) PERFORMANCE OPTIMIZATION TOOL")
	}
}
