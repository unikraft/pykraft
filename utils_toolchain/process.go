// Copyright 2019 The UNICORE Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file
//
// Author: Gaulthier Gain <gaulthier.gain@uliege.be>

package util_tools

import (
	"bytes"
	"errors"
	"io"
	"io/ioutil"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"syscall"
	"unicode"
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

// PKill kills a given running process with a particular signal
//
// It returns an error if any, otherwise it returns nil.
func PKill(programName string, sig syscall.Signal) error {
	if len(programName) == 0 {
		return errors.New("program name should not be empty")
	}
	re, err := regexp.Compile(programName)
	if err != nil {
		return err
	}

	pids := getPids(re)
	if len(pids) == 0 {
		return nil
	}

	for _, pid := range pids {
		_ = syscall.Kill(pid, sig)
	}

	return nil
}

// getPids gets PIDs of a particular process.
//
// It returns a list of integer which represents the pids of particular process.
func getPids(re *regexp.Regexp) []int {
	var pids []int

	dirFD, err := os.Open("/proc")
	if err != nil {
		return nil
	}
	defer dirFD.Close()

	for {
		// Read a small number at a time in case there are many entries, we don't want to
		// allocate a lot here.
		ls, err := dirFD.Readdir(10)
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil
		}

		for _, entry := range ls {
			if !entry.IsDir() {
				continue
			}

			// If the directory is not a number (i.e. not a PID), skip it
			pid, err := strconv.Atoi(entry.Name())
			if err != nil {
				continue
			}

			cmdline, err := ioutil.ReadFile(filepath.Join("/proc", entry.Name(), "cmdline"))
			if err != nil {
				println("Error reading file %s: %+v", filepath.Join("/proc",
					entry.Name(), "cmdline"), err)
				continue
			}

			// The bytes we read have '\0' as a separator for the command line
			parts := bytes.SplitN(cmdline, []byte{0}, 2)
			if len(parts) == 0 {
				continue
			}
			// Split the command line itself we are interested in just the first part
			exe := strings.FieldsFunc(string(parts[0]), func(c rune) bool {
				return unicode.IsSpace(c) || c == ':'
			})
			if len(exe) == 0 {
				continue
			}
			// Check if the name of the executable is what we are looking for
			if re.MatchString(exe[0]) {
				// Grab the PID from the directory path
				pids = append(pids, pid)
			}
		}
	}

	return pids
}
