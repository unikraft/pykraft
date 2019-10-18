// Copyright 2019 The UNICORE Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file
//
// Author: Gaulthier Gain <gaulthier.gain@uliege.be>

package main

import (
	"errors"
	. "github.com/akamensky/argparse"
	"os"
	u "tools/utils"
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
func ParseArguments(args *u.Arguments) error {

	if args == nil || args.IntArg == nil {
		return errors.New("args structure should be initialized")
	}

	p := NewParser("Unikraft dependencies crawler",
		"Unikraft dependencies crawler allows to create "+
			"dependencies grap")

	args.InitArgParse(p, args, u.BOOL, "f", FULL,
		&Options{Required: false, Default: false,
			Help: "Take all the selected libraries"})

	args.InitArgParse(p, args, u.STRING, "o", OUTPUT,
		&Options{Required: true, Help: "Output folder that will contain" +
			"dependencies graph and images"})
	args.InitArgParse(p, args, u.STRING, "l", LIBS,
		&Options{Required: false, Help: "Path of the file that contains libs"})
	args.InitArgParse(p, args, u.STRING, "r", REPO,
		&Options{Required: false, Help: "Path of the repository"})

	if err := p.Parse(os.Args); err != nil {
		return err
	}

	return nil
}
