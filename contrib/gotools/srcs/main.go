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
	"os/user"
	"tools/srcs/buildtool"
	u "tools/srcs/common"
	"tools/srcs/crawlertool"
	"tools/srcs/dependtool"
	"tools/srcs/veriftool"
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
		veriftool.RunVerificationTool()
	}

	if all || *args.BoolArg[u.PERF] {
		u.PrintHeader1("(4) PERFORMANCE OPTIMIZATION TOOL")
	}
}
