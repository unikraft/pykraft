// Copyright 2019 The UNICORE Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file
//
// Author: Gaulthier Gain <gaulthier.gain@uliege.be>

package util_tools

import (
	"fmt"
	"github.com/fatih/color"
	"log"
)

// PrintHeader1 prints a big header formatted string on stdout.
func PrintHeader1(v ...interface{}) {
	d := color.New(color.FgBlue, color.Bold, color.Underline)
	_, _ = d.Println(v)
}

// PrintHeader2 prints a small header formatted string on stdout.
func PrintHeader2(v ...interface{}) {
	d := color.New(color.FgMagenta)
	_, _ = d.Println(v)
}

// PrintWarning prints a warning formatted string on stdout.
func PrintWarning(v ...interface{}) {
	d := color.New(color.FgYellow, color.Bold)
	_, _ = d.Print("[WARNING] ")
	fmt.Println(v)
}

// PrintOk prints a success formatted string on stdout.
func PrintOk(v ...interface{}) {
	d := color.New(color.FgGreen, color.Bold)
	_, _ = d.Print("[SUCCESS] ")
	fmt.Println(v)
}

// PrintInfo prints an info formatted string on stdout.
func PrintInfo(v ...interface{}) {
	d := color.New(color.FgBlue, color.Bold)
	_, _ = d.Print("[INFO] ")
	fmt.Println(v)
}

// PrintErr prints an error formatted string on stdout and exits the app.
func PrintErr(v ...interface{}) {
	d := color.New(color.FgRed, color.Bold)
	_, _ = d.Print("[ERROR] ")
	log.Fatal(v)
}
