// Copyright 2019 The UNICORE Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file
//
// Author: Gaulthier Gain <gaulthier.gain@uliege.be>

package common

import (
	"errors"
	"github.com/akamensky/argparse"
	"os"
	"strings"
)

const (
	INT = iota
	BOOL
	STRING
)

const (
	CRAWLER = "crawler"
	DEP     = "dep"
	BUILD   = "build"
	VERIF   = "verif"
	PERF    = "perf"
)

const (
	unknownArgs = "unknown arguments"
)

type Arguments struct {
	IntArg    map[string]*int
	BoolArg   map[string]*bool
	StringArg map[string]*string
}

func (args *Arguments) InitArguments() (*argparse.Parser, error) {

	args.IntArg = make(map[string]*int)
	args.BoolArg = make(map[string]*bool)
	args.StringArg = make(map[string]*string)

	p := argparse.NewParser("UNICORE toolchain",
		"The UNICORE toolchain allows to build unikernels")

	return p, nil
}

func ParserWrapper(p *argparse.Parser, args []string) error {
	err := p.Parse(args)
	if err != nil && strings.Contains(err.Error(), unknownArgs) {
		return nil
	}

	return err
}

// ParseArguments parses arguments of the application.
//
// It returns an error if any, otherwise it returns nil.
func (*Arguments) ParseMainArguments(p *argparse.Parser, args *Arguments) error {

	if args == nil {
		return errors.New("args structure should be initialized")
	}

	args.InitArgParse(p, args, BOOL, "", CRAWLER,
		&argparse.Options{Required: false, Default: false,
			Help: "Execute the crawler unikraft tool"})
	args.InitArgParse(p, args, BOOL, "", DEP,
		&argparse.Options{Required: false, Default: false,
			Help: "Execute only the dependency analysis tool"})
	args.InitArgParse(p, args, BOOL, "", BUILD,
		&argparse.Options{Required: false, Default: false,
			Help: "Execute only the automatic build tool"})
	args.InitArgParse(p, args, BOOL, "", VERIF,
		&argparse.Options{Required: false, Default: false,
			Help: "Execute only the verification tool"})
	args.InitArgParse(p, args, BOOL, "", PERF,
		&argparse.Options{Required: false, Default: false,
			Help: "Execute only the performance tool"})

	// Parse only the two first arguments <program name, [tools]>
	if len(os.Args) > 2 {
		return ParserWrapper(p, os.Args[:2])
	}

	return nil
}

// InitArgParse initializes the Arguments structure depending the type of
// the variable.
//
func (*Arguments) InitArgParse(p *argparse.Parser, args *Arguments, typeVar int,
	short, long string, options *argparse.Options) {
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
