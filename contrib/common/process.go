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
	"bytes"
	"context"
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
	"time"
	"unicode"
)

const TIMEOUT = 5 //in seconds

// ExecutePipeCommand executes a piped command.
//
// It returns a string which represents stdout and an error if any, otherwise
// it returns nil.
func ExecutePipeCommand(command string) (string, error) {

	ctx, cancel := context.WithTimeout(context.Background(), TIMEOUT*time.Second)
	defer cancel()

	cmd := exec.CommandContext(ctx, "/bin/bash", "-c", command)
	out, err := cmd.Output()
	if err != nil {
		return "", err
	}

	if ctx.Err() == context.DeadlineExceeded {
		return string(out), errors.New("Time out during with: " + command)
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

// ExecuteRunCmdStdin runs a command and saves stdout and stderr as bytes.
//
// It returns two byte arrays which are respectively stdout and stderr
// and an error if any, otherwise it returns nil.
func ExecuteRunCmdStdin(name string, stdinArgs []byte, args ...string) ([]byte,
	[]byte) {

	bufOut, bufErr := &bytes.Buffer{}, &bytes.Buffer{}

	var buffer bytes.Buffer
	if len(stdinArgs) > 0 {
		buffer = bytes.Buffer{}
		buffer.Write(stdinArgs)
	}

	ctx, cancel := context.WithTimeout(context.Background(), TIMEOUT*time.Second)
	defer cancel()

	cmd := exec.CommandContext(ctx, name, args...)
	if len(stdinArgs) > 0 {
		cmd.Stdin = &buffer
	}
	cmd.Stdout = bufOut
	cmd.Stderr = bufErr

	_ = cmd.Run()

	if ctx.Err() == context.DeadlineExceeded {
		PrintWarning("Time out during executing: " + cmd.String())
		return bufOut.Bytes(), bufErr.Bytes()
	}

	return bufOut.Bytes(), bufErr.Bytes()
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

// ExecuteWaitCommand runs command and waits to its termination without
// displaying the output.
//
// It returns a string which represents stdout and an error if any, otherwise
// it returns nil.
func ExecuteWaitCommand(dir, command string, args ...string) (*string, *string,
	error) {

	cmd := exec.Command(command, args...)
	cmd.Dir = dir
	cmd.SysProcAttr = &syscall.SysProcAttr{Setpgid: true}

	bufOut, bufErr := &bytes.Buffer{}, &bytes.Buffer{}
	cmd.Stdout = io.MultiWriter(bufOut) // Add os.Stdin to record on stdout
	cmd.Stderr = io.MultiWriter(bufErr) // Add os.Stdin to record on stderr
	cmd.Stdin = os.Stdin

	if err := cmd.Start(); err != nil {
		return nil, nil, err
	}

	PrintInfo("Waiting command: " + command + " " + strings.Join(args, " "))

	// Ignore error
	_ = cmd.Wait()

	strOut, strErr := bufOut.String(), bufErr.String()

	return &strOut, &strErr, nil
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

	current := os.Getpid()
	for _, pid := range pids {
		if current != pid {
			_ = syscall.Kill(pid, sig)
		}
	}

	return nil
}

// PidOf gets PIDs of a particular process.
//
// It returns a list of integer which represents the pids of particular process
// and  an error if any, otherwise it returns nil.
func PidOf(name string) ([]int, error) {
	if len(name) == 0 {
		return []int{}, errors.New("name should not be empty")
	}
	re, err := regexp.Compile("(^|/)" + name + "$")
	if err != nil {
		return []int{}, err
	}
	return getPids(re), nil
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
