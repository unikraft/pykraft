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

const CONFIG_UK = "Config.uk"
const MENUCONFIG = "menuconfig"
const CONFIG = "config"
const SELECT = "select"

// processConfigUK processes each line of a "Config.uk" file.
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
