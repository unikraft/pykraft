// Copyright 2019 The UNICORE Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file
//
// Author: Gaulthier Gain <gaulthier.gain@uliege.be>

package main

import (
	"os"
	"strconv"
	"strings"
	"time"
	u "tools/utils"
)

// Individual tool (out of the UNICORE toolchain)
func main() {

	mapLabel := make(map[string]string)
	mapConfig := make(map[string][]string)

	args := new(u.Arguments)
	args.InitArguments(args)
	err := ParseArguments(args)
	if err != nil {
		u.PrintErr(err)
	}

	// Used to select all libraries (even those below another Config fields)
	fullSelect := *args.BoolArg[FULL]

	var path string
	if len(*args.StringArg[REPO]) > 0 {

		// Only one folder
		path = *args.StringArg[REPO]
		u.PrintInfo("Parse folder: " + path)
		if err := searchConfigUK(path, fullSelect, mapConfig, mapLabel);
			err != nil {
			u.PrintErr()
		}

	} else if len(*args.StringArg[LIBS]) > 0 {

		// Several folders within a list
		lines, err := u.ReadLinesFile(*args.StringArg[LIBS])
		if err != nil {
			u.PrintErr(err)
		}

		// Process Config.uk of each process
		for _, line := range lines {
			path = strings.TrimSuffix(line, "\n")
			u.PrintInfo("Parse folder: " + path)
			if err := searchConfigUK(path, fullSelect, mapConfig, mapLabel);
				err != nil {
				u.PrintErr(err)
			}
		}
	} else {
		u.PrintErr("You must specify either -r (--repository) or -l (libs)")
	}

	// Create the dependencies graph
	graph, err := u.CreateGraphLabel("Unikraft crawler", mapConfig, mapLabel)
	if err != nil {
		u.PrintErr(err)
	}

	u.PrintInfo("Number of nodes: " + strconv.Itoa(len(graph.Nodes.Nodes)))
	u.PrintInfo("Number of edges: " + strconv.Itoa(len(graph.Edges.Edges)))

	// Generate the folder
	outFolder := *args.StringArg[OUTPUT]
	if outFolder[:len(outFolder)-1] != string(os.PathSeparator) {
		outFolder += string(os.PathSeparator)
	}

	outputPath := outFolder +
		"output_" + time.Now().Format("20060102150405") + ".dot"
	err = u.SaveGraphToFile(outputPath, graph)
	if err != nil {
		u.PrintErr(err)
	}

	u.PrintOk(".dot file is saved: " + outputPath)
	u.PrintOk("Open the following website to display the graph:" +
		" https://dreampuf.github.io/GraphvizOnline/")
}
