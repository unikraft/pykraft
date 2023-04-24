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

const CONFIGUK = "Config.uk"
const MENUCONFIG = "menuconfig"
const CONFIG = "config"
const SELECT = "select"

// ProcessConfigUK processes each line of a "Config.uk" file.
//
// //
func ProcessConfigUK(lines []string, fullSelect bool,
	mapConfig map[string][]string, mapLabel map[string]string) {

	var libName string
	var otherConfig = false

	for i, line := range lines {
		parseConfigUK(i, line, &libName, fullSelect, &otherConfig,
			mapConfig, mapLabel)
	}
}

// parseConfigUK parses each line of to detect selected libraries (dependencies)
//
// //
func parseConfigUK(index int, line string, libName *string, fullSelect bool,
	otherConfig *bool, mapConfig map[string][]string, mapLabel map[string]string) {

	space := regexp.MustCompile(`\s+|\t+`)
	line = space.ReplaceAllString(line, " ")
	line = strings.TrimSpace(line)

	switch {
	case strings.Contains(line, MENUCONFIG),
		strings.Contains(line, CONFIG) && index == 0:
		{
			// First case: get the name of the lib

			// Split the line to retrieve the name of the lib
			split := strings.Split(line, " ")
			if len(split) < 2 {
				break
			}

			*libName = strings.TrimSuffix(split[1], "\n")
		}
	case strings.Contains(line, CONFIG) && index > 0:
		{
			// Second case: check if other Config lines
			*otherConfig = true
		}
	case strings.Contains(line, SELECT) && index > 0:
		{
			// Third case: add select libs

			// if there are other Config flag, check the dependencies if
			// specified (fullDep), otherwise break
			if !*otherConfig && !fullSelect {
				break
			}

			// Split the line to retrieve the name of the dependency
			split := strings.Split(line, " ")
			var library string
			if len(split) < 2 {
				break
			} else if len(split) > 2 {
				// If we have complex select (e.g., select LIBUKTIME if
				// !HAVE_LIBC && ARCH_X86_64)
				var re = regexp.MustCompile(`(?m)select\s(\w*)\sif\s([a-zA-Z0-9!_& ]*)`)
				match := re.FindAllStringSubmatch(line, -1)
				if len(match) > 0 {
					library = match[0][1]
					if mapLabel != nil {
						mapLabel[library] = match[0][2]
					}
				} else {
					break
				}
			} else {
				library = split[1]
			}

			// Current selected library
			selectedLib := strings.TrimSuffix(library, "\n")

			// Links between current lib and its dependencies
			mapConfig[*libName] = append(mapConfig[*libName], selectedLib)

			// Add selected lib in the map in order to generate a node
			// if it does not exist
			if _, ok := mapConfig[selectedLib]; !ok {
				mapConfig[selectedLib] = nil
			}
		}
	}
}
