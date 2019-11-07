// Copyright 2019 The UNICORE Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file
//
// Author: Gaulthier Gain <gaulthier.gain@uliege.be>

package crawlertool

import (
	"github.com/akamensky/argparse"
	"os"
	u "tools/common"
)

const (
	FULL   = "full"
	OUTPUT = "output"
	LIBS   = "libraries"
	REPO   = "repository"
)

// ParseArguments parses arguments of the application.
//
// It returns an error if any, otherwise it returns nil.
func parseLocalArguments(p *argparse.Parser, args *u.Arguments) error {

	args.InitArgParse(p, args, u.BOOL, "f", FULL,
		&argparse.Options{Required: false, Default: false,
			Help: "Take all the selected libraries"})

	args.InitArgParse(p, args, u.STRING, "o", OUTPUT,
		&argparse.Options{Required: true, Help: "Output folder that will " +
			"contain dependencies graph and images"})
	args.InitArgParse(p, args, u.STRING, "l", LIBS,
		&argparse.Options{Required: false, Help: "Path of the file that " +
			"contains libs"})
	args.InitArgParse(p, args, u.STRING, "r", REPO,
		&argparse.Options{Required: false, Help: "Path of the repository"})

	return u.ParserWrapper(p, os.Args)
}
