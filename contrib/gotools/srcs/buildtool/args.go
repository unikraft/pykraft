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

package buildtool

import (
	"os"
	u "tools/srcs/common"

	"github.com/akamensky/argparse"
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
