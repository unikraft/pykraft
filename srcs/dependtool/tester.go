// Copyright 2019 The UNICORE Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file
//
// Author: Gaulthier Gain <gaulthier.gain@uliege.be>
package dependtool

import (
	"bytes"
	"fmt"
	"io"
	"os"
	"os/exec"
	"strconv"
	"strings"
	"syscall"
	"time"
	u "tools/srcs/common"
)

const (
	stdinCmd    = "[STDIN]"
	testCmd     = "[TEST]"
	startupTime = 3
)

// launchTestsExternal runs external tests written in the 'test.txt' file.
//
func launchTestsExternal(cmdTests []string) {

	for _, cmd := range cmdTests {
		if len(cmd) > 0 {
			cmd = strings.TrimSuffix(cmd, "\n")
			// Execute each line as a command
			if _, err := u.ExecutePipeCommand(cmd); err != nil {
				u.PrintWarning("Impossible to execute test: " + cmd)
			} else {
				u.PrintInfo("Test executed: " + cmd)
			}
		}
	}
}

// launchTestsStdin runs external tests written in the 'test.txt' file on stdin.
//
func launchTestsStdin(cmdTests []string, bufIn *bytes.Buffer) {

	stdinFlag := false

	for _, cmd := range cmdTests {
		if len(cmd) > 0 {
			if strings.Contains(cmd, stdinCmd) {
				stdinFlag = true
			} else if strings.Contains(cmd, testCmd) {
				stdinFlag = false
			} else if stdinFlag {
				if _, err := bufIn.Write([]byte(cmd)); err != nil {
					u.PrintWarning("Impossible to execute test: " + cmd)
				}
			}
		}
	}
}

// checkTestStdin checks if [STDIN] flag is present within test files.
//
// It returns true if the [STDIN] flag is present.
func checkTestStdin(tests []string) bool {
	return u.Contains(tests, stdinCmd+"\n")
}

// captureOutput captures stdout and stderr of a the executed command. It will
// also run the Tester to explore several execution paths of the given app.
//
// It returns to string which are respectively stdout and stderr.
func captureOutput(programPath, programName, command, option string,
	tests []string, dArgs DynamicArgs, data *u.DynamicData) (string, string) {

	args := strings.Fields("-f " + programPath + " " + option)
	cmd := exec.Command(command, args...)
	cmd.SysProcAttr = &syscall.SysProcAttr{Setpgid: true}

	bufOut, bufErr, bufIn := &bytes.Buffer{}, &bytes.Buffer{}, &bytes.Buffer{}
	cmd.Stdout = bufOut // Add io.MultiWriter(os.Stdout) to record on stdout
	cmd.Stderr = bufErr // Add io.MultiWriter(os.Stderr) to record on stderr
	cmd.Stdin = os.Stdin

	// Check if [STDIN] flag is present within test files
	stdin := checkTestStdin(tests)
	if stdin {

		// Use MultiReader to handle bufIn and os.stdin
		cmd.Stdin = io.MultiReader(bufIn, os.Stdin)

		// Run tests on stdin
		u.PrintInfo(stdinCmd + " detected: run tests on stdin")
		launchTestsStdin(tests, bufIn)
	}

	// Run the process (traced by strace/ltrace)
	if err := cmd.Start(); err != nil {
		u.PrintErr(err)
	}

	// Add timer for background process
	timerBackground := time.NewTimer(startupTime * time.Second)
	go func() {
		<-timerBackground.C

		// If background, run Testers
		Tester(programName, cmd, data, tests, dArgs, stdin)

		timerKill := time.NewTimer(startupTime * time.Second)

		// Kill process after elapsed time
		u.PrintInfo("Kill '" + programName + "'")
		if err := cmd.Process.Kill(); err != nil {
			u.PrintErr(err)
		} else {
			u.PrintOk("'" + programName + "' Killed")
		}

		runTimerKill(timerKill, programName)

		timerKill.Stop()

		if stdin {
			u.PrintInfo("Hit 'enter' key to continue")
		}
	}()

	// Ignore the error because the program is killed (waitTime)
	_ = cmd.Wait()

	// Stop timer
	timerBackground.Stop()

	return bufOut.String(), bufErr.String()
}

func runTimerKill(timerKill *time.Timer, programName string) {

	// Add timeout if program is not killed
	var canceled = make(chan struct{})

	// Run timer kill
	go func() {
		select {
		case <-timerKill.C:
			u.PrintInfo("Timer expired, try to kill again " + programName)
			if err := u.PKill(programName, syscall.SIGINT); err != nil {
				u.PrintErr(err)
			}
		case <-canceled:
		}
	}()
}

// Tester runs the executable file of a given application to perform tests to
// get program dependencies.
//
func Tester(programName string, cmd *exec.Cmd, data *u.DynamicData,
	cmdTests []string, dArgs DynamicArgs, stdin bool) {

	if len(dArgs.testFile) > 0 {
		u.PrintInfo("Run internal tests from file " + dArgs.testFile)

		// Wait until the program has started
		time.Sleep(time.Second * startupTime)

		// Launch Tests
		if !stdin {
			launchTestsExternal(cmdTests)
		}
	} else {
		u.PrintInfo("Waiting for external tests for " + strconv.Itoa(
			dArgs.waitTime) + " sec")
		ticker := time.Tick(time.Second)
		for i := 1; i <= dArgs.waitTime; i++ {
			<-ticker
			fmt.Printf("-")
		}
		fmt.Printf("\n")
	}

	// Gather shared libs
	u.PrintHeader2("(*) Gathering shared libs")
	if err := gatherDynamicSharedLibs(programName, cmd.Process.Pid, data,
		dArgs.fullDeps); err != nil {
		u.PrintWarning(err)
	}
}
