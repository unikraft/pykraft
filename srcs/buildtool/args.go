// Copyright 2019 The UNICORE Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file
//
// Author: Gaulthier Gain <gaulthier.gain@uliege.be>

package buildtool

import (
	"github.com/akamensky/argparse"
	"os"
	u "tools/srcs/common"
)

const (
	programArg  = "program"
	unikraftArg = "unikraft"
	sourcesArg  = "sources"
	makefileArg = "makefile"
)

// ParseArguments parses arguments of the application.
//
// It returns an error if any, otherwise it returns nil.
func parseLocalArguments(p *argparse.Parser, args *u.Arguments) error {

	args.InitArgParse(p, args, u.STRING, "p", programArg,
		&argparse.Options{Required: true, Help: "Program name"})

	args.InitArgParse(p, args, u.STRING, "u", unikraftArg,
		&argparse.Options{Required: false, Help: "Unikraft Path"})
	args.InitArgParse(p, args, u.STRING, "s", sourcesArg,
		&argparse.Options{Required: true, Help: "App Sources " +
			"Folder"})
	args.InitArgParse(p, args, u.STRING, "m", makefileArg,
		&argparse.Options{Required: false, Help: "Add additional properties " +
			"for Makefile"})

	return u.ParserWrapper(p, os.Args)
}
