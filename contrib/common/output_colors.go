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

package common

import (
	"fmt"
	"github.com/fatih/color"
	"log"
)

// PrintHeader1 prints a big header formatted string on stdout.
func PrintHeader1(v ...interface{}) {
	header := color.New(color.FgBlue, color.Bold, color.Underline).SprintFunc()
	fmt.Printf("%v\n", header(v))
}

// PrintHeader2 prints a small header formatted string on stdout.
func PrintHeader2(v ...interface{}) {
	magenta := color.New(color.FgMagenta).SprintFunc()
	fmt.Printf("%v\n", magenta(v))
}

// PrintWarning prints a warning formatted string on stdout.
func PrintWarning(v ...interface{}) {
	yellow := color.New(color.FgYellow, color.Bold).SprintFunc()
	fmt.Printf("[%s] %v\n", yellow("WARNING"), v)
}

// PrintOk prints a success formatted string on stdout.
func PrintOk(v ...interface{}) {
	green := color.New(color.FgGreen, color.Bold).SprintFunc()
	fmt.Printf("[%s] %v\n", green("SUCCESS"), v)
}

// PrintInfo prints an info formatted string on stdout.
func PrintInfo(v ...interface{}) {
	blue := color.New(color.FgBlue, color.Bold).SprintFunc()
	fmt.Printf("[%s] %v\n", blue("INFO"), v)
}

// PrintErr prints an error formatted string on stdout and exits the app.
func PrintErr(v ...interface{}) {
	red := color.New(color.FgRed).SprintFunc()
	log.Fatalf("[%s] %v\n", red("ERROR"), v)
}
