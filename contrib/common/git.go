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
	"regexp"
	"strings"
)

const branch = "staging"

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

	if strings.Contains(*strOut, branch) || strings.Contains(*strErr, branch) {
		PrintInfo("Checkout to " + branch)
		return ExecuteRunCmd("git", dir, v, "checkout", branch)
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
