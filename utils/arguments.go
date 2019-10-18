// Copyright 2019 The UNICORE Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file
//
// Author: Gaulthier Gain <gaulthier.gain@uliege.be>

package util_tools

import (
	"errors"
	. "github.com/akamensky/argparse"
	"os"
)

const (
	INT = iota
	BOOL
	STRING
)

type Arguments struct {
	IntArg    map[string]*int
	BoolArg   map[string]*bool
	StringArg map[string]*string
}

func (*Arguments) InitArguments(args *Arguments) {
	args.IntArg = make(map[string]*int)
	args.BoolArg = make(map[string]*bool)
	args.StringArg = make(map[string]*string)
}

// ParseArguments parses arguments of the application.
//
// It returns an error if any, otherwise it returns nil.
func (*Arguments) ParseArguments(args *Arguments) error {

	if args == nil || args.IntArg == nil {
		return errors.New("args structure should be initialized")
	}

	p := NewParser("UNICORE toolchain",
		"The UNICORE toolchain allows to build unikernels")

	args.InitArgParse(p, args, BOOL, "", "dep",
		&Options{Required: false, Default: false,
			Help: "Execute only the dependency analysis tool"})
	args.InitArgParse(p, args, BOOL, "", "build",
		&Options{Required: false, Default: false,
			Help: "Execute only the automatic build tool"})
	args.InitArgParse(p, args, BOOL, "", "verif",
		&Options{Required: false, Default: false,
			Help: "Execute only the verification tool"})
	args.InitArgParse(p, args, BOOL, "", "perf",
		&Options{Required: false, Default: false,
			Help: "Execute only the performance tool"})

	args.InitArgParse(p, args, STRING, "p",
		"program", &Options{Required: true, Help: "Program name"})
	args.InitArgParse(p, args, STRING, "t", "testFile",
		&Options{Required: false, Help: "Path of the test file"})
	args.InitArgParse(p, args, STRING, "o", "options",
		&Options{Required: false, Default: "", Help: "Extra options for " +
			"launching program"})
	args.InitArgParse(p, args, INT, "w", "waitTime",
		&Options{Required: false, Default: 60, Help: "Time wait (" +
			"sec) for external tests (default: 60 sec)"})
	args.InitArgParse(p, args, STRING, "u", "unikraft",
		&Options{Required: false, Default: "", Help: "Unikraft Path"})
	args.InitArgParse(p, args, STRING, "s", "sources",
		&Options{Required: false, Default: "", Help: "App Source Folder"})
	args.InitArgParse(p, args, STRING, "m", "makefile",
		&Options{Required: false, Help: "Add additional properties for Makefile"})

	args.InitArgParse(p, args, BOOL, "d", "display",
		&Options{Required: false, Default: false,
			Help: "Save results as TXT file and graphs as PNG file"})
	args.InitArgParse(p, args, BOOL, "v", "verbose",
		&Options{Required: false, Default: false, Help: "Verbose mode"})
	args.InitArgParse(p, args, BOOL, "b", "background",
		&Options{Required: false, Default: true,
			Help: "Specify if the given process is a background process (" +
				"web server, database)"})

	if err := p.Parse(os.Args); err != nil {
		return err
	}

	return nil
}

// InitArgParse initializes the Arguments structure depending the type of
// the variable.
//
func (*Arguments) InitArgParse(p *Parser, args *Arguments, typeVar int, short,
	long string, options *Options) {
	switch typeVar {
	case INT:
		args.IntArg[long] = new(int)
		args.IntArg[long] = p.Int(short, long, options)
	case BOOL:
		args.BoolArg[long] = new(bool)
		args.BoolArg[long] = p.Flag(short, long, options)
	case STRING:
		args.StringArg[long] = new(string)
		args.StringArg[long] = p.String(short, long, options)
	}
}
