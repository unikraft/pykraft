// Copyright 2019 The UNICORE Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file
//
// Author: Gaulthier Gain <gaulthier.gain@uliege.be>

package common

import (
	"regexp"
	"strings"
)

const BRANCH = "staging"

// GitCloneRepository clones a git repository at the the given url.
//
// It returns two pointers of string which are respectively stdout and stderr
// and an error if any, otherwise it returns nil.
func GitCloneRepository(url, dir string, v bool) (*string, *string, error) {
	return ExecuteRunCmd("git", dir, v, "clone", url)
}

// GitBranchStaging updates the current branch of a git repository to the
// 'staging' branch.
//
// It returns two pointers of string which are respectively stdout and stderr
// and an error if any, otherwise it returns nil.
func GitBranchStaging(dir string, v bool) (*string, *string, error) {
	strOut, strErr, err := ExecuteRunCmd("git", dir, v, "branch", "-r")
	if err != nil {
		return strOut, strErr, err
	}

	if strings.Contains(*strOut, BRANCH) || strings.Contains(*strErr, BRANCH) {
		PrintInfo("Checkout to " + BRANCH)
		return ExecuteRunCmd("git", dir, v, "checkout", BRANCH)
	}

	return strOut, strErr, err
}

// GitPull pulls the current git repository.
//
// It returns two pointers of string which are respectively stdout and stderr
// and an error if any, otherwise it returns nil.
func GitPull(dir string, v bool) (*string, *string, error) {
	return ExecuteRunCmd("git", dir, v, "pull")
}

// GitFindExternalLibs finds all the external libraries of Unikraft which are
// hosted on Xenbits.
//
// It returns a map of all the external libs of Unikraft.
func GitFindExternalLibs(output string) map[string]string {
	var re = regexp.MustCompile(
		`(?m)<a class="list"\s+href="(.*);a=summary">.*</a>`)

	matches := re.FindAllStringSubmatch(output, -1)
	externalLibs := make(map[string]string, len(matches))
	for _, match := range matches {
		git := strings.Split(match[1], "/")
		lib := strings.Split(git[len(git)-1], ".git")
		externalLibs[lib[0]] = git[len(git)-1]
	}
	return externalLibs
}
