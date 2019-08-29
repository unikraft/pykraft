// Copyright 2019 The UNICORE Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file
//
// Author: Gaulthier Gain <gaulthier.gain@uliege.be>

package util_tools

import (
	"bytes"
	"io"
	"os"
	"os/exec"
)

// ExecutePipeCommand executes a piped command.
//
// It returns a string which represents stdout and an error if any, otherwise
// it returns nil.
func ExecutePipeCommand(command string) (string, error) {
	out, err := exec.Command("bash", "-c", command).Output()
	if err != nil {
		return "", err
	}
	return string(out), nil
}

// ExecuteRunCmd runs a command and display the output to stdout and stderr.
//
// It returns two pointers of string which are respectively stdout and stderr
// and an error if any, otherwise it returns nil.
func ExecuteRunCmd(name, dir string, v bool, args ...string) (*string, *string,
	error) {
	cmd := exec.Command(name, args...)
	cmd.Dir = dir
	bufOut, bufErr := &bytes.Buffer{}, &bytes.Buffer{}
	if v {
		cmd.Stderr = io.MultiWriter(bufErr, os.Stderr)
		cmd.Stdout = io.MultiWriter(bufOut, os.Stdout)
	} else {
		cmd.Stderr = bufErr
		cmd.Stdout = bufOut
	}
	cmd.Stdin = os.Stdin
	_ = cmd.Run()

	strOut, strErr := bufOut.String(), bufErr.String()

	return &strOut, &strErr, nil
}

// ExecuteCommand a single command without displaying the output.
//
// It returns a string which represents stdout and an error if any, otherwise
// it returns nil.
func ExecuteCommand(command string, arguments []string) (string, error) {
	out, err := exec.Command(command, arguments...).CombinedOutput()
	if err != nil {
		return "", err
	}
	return string(out), nil
}