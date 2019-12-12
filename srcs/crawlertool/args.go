// Copyright 2019 The UNICORE Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file
//
// Author: Gaulthier Gain <gaulthier.gain@uliege.be>

package crawlertool

import (
	"github.com/akamensky/argparse"
	"os"
	u "tools/srcs/common"
)

const (
	fullLibsArg = "full"
	outputArg   = "output"
	libsArg     = "libraries"
	repoArg     = "repository"
)

// ParseArguments parses arguments of the application.
//
// It returns an error if any, otherwise it returns nil.
func parseLocalArguments(p *argparse.Parser, args *u.Arguments) error {

	args.InitArgParse(p, args, u.BOOL, "f", fullLibsArg,
		&argparse.Options{Required: false, Default: false,
			Help: "Take all the selected libraries"})

	args.InitArgParse(p, args, u.STRING, "o", outputArg,
		&argparse.Options{Required: true, Help: "Output folder that will " +
			"contain dependencies graph and images"})
	args.InitArgParse(p, args, u.STRING, "l", libsArg,
		&argparse.Options{Required: false, Help: "Path of the file that " +
			"contains libs"})
	args.InitArgParse(p, args, u.STRING, "r", repoArg,
		&argparse.Options{Required: false, Help: "Path of the repository"})

	return u.ParserWrapper(p, os.Args)
}
