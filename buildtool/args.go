// Copyright 2019 The UNICORE Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file
//
// Author: Gaulthier Gain <gaulthier.gain@uliege.be>

package buildtool

import (
	. "github.com/akamensky/argparse"
	"os"
	u "tools/common"
)

const (
	PROGRAM  = "program"
	OUTPUT   = "output"
	UNIKRAFT = "unikraft"
	SOURCES  = "sources"
	MAKEFILE = "makefile"
)

// ParseArguments parses arguments of the application.
//
// It returns an error if any, otherwise it returns nil.
func parseLocalArguments(p *Parser, args *u.Arguments) error {

	args.InitArgParse(p, args, u.STRING, "p", PROGRAM,
		&Options{Required: true, Help: "Program name"})

	args.InitArgParse(p, args, u.STRING, "u", UNIKRAFT,
		&Options{Required: false, Default: "", Help: "Unikraft Path"})
	args.InitArgParse(p, args, u.STRING, "s", SOURCES,
		&Options{Required: false, Default: "", Help: "App Sources Folder"})
	args.InitArgParse(p, args, u.STRING, "m", MAKEFILE,
		&Options{Required: false, Help: "Add additional properties for Makefile"})

	return u.ParserWrapper(p, os.Args)
}
