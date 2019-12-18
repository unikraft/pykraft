// Copyright 2019 The UNICORE Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file
//
// Author: Gaulthier Gain <gaulthier.gain@uliege.be>

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
