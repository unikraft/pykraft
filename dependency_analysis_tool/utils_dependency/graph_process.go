// Copyright 2019 The UNICORE Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file
//
// Author: Gaulthier Gain <gaulthier.gain@uliege.be>

package utils_dependency

import (
	"math/rand"
	"os"

	util_tools "github.com/unikraft/tools/utils_toolchain"

	"github.com/awalterschulze/gographviz"
)

const letterBytes = "0123456789ABCDEF"

// RandStringBytes generates random string of size n.
//
// It returns a random string of a particular length.
func RandStringBytes(n int) string {

	b := make([]byte, n)
	for i := range b {
		b[i] = letterBytes[rand.Intn(len(letterBytes))]
	}
	return string(b)
}

// ColorGenerator generates a color in RGB format.
//
// It returns a string which represents a random string formatted as RGB color.
func ColorGenerator() string {
	return "#" + RandStringBytes(6)
}

// CreateGraph creates a graph from a map.
//
// It returns a graph which represents all the direct and no-direct dependencies
// of a given application and an error if any, otherwise it returns nil.
func CreateGraph(programName string, data map[string][]string) (*gographviz.
	Escape, error) {
	graph := gographviz.NewEscape()

	if err := graph.SetName(programName); err != nil {
		return nil, err
	}

	// Directed graph
	if err := graph.SetDir(true); err != nil {
		return nil, err
	}

	// Create graph from map
	for key, values := range data {

		colorsMap := map[string]string{}

		// Generate a random color
		if _, in := colorsMap[key]; !in {
			colorsMap[key] = ColorGenerator()
		}

		if values != nil {
			colorAttr := map[string]string{"color": colorsMap[key]}

			// Create nodes
			if err := graph.AddNode("\""+key+"\"", "\""+key+"\"",
				colorAttr); err != nil {
				return nil, err
			}

			// Add edges
			for _, v := range values {
				if err := graph.AddEdge("\""+key+"\"", "\""+v+"\"", true,
					colorAttr); err != nil {
					return nil, err
				}
			}
		}
	}

	return graph, nil
}

// SaveGraphToFile saves a given graph to a file.
//
// It returns an error if any, otherwise it returns nil.
func SaveGraphToFile(filename string, graph *gographviz.Escape) error {
	file, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer file.Close()

	_, err = file.WriteString(graph.String())
	if err != nil {
		return err
	}

	return nil
}

// GenerateGraph generates a given graph to a '.dot' and '.png' files.
//
// It returns an error if any, otherwise it returns nil.
func GenerateGraph(programName, fullPathName string, data map[string][]string) {
	// Create graph
	graph, err := CreateGraph(programName, data)

	// Save graph as '.dot' file
	if err = SaveGraphToFile(fullPathName+".dot", graph); err != nil {
		util_tools.PrintWarning(err)
	}

	// Save graph as '.png' file
	if _, err := util_tools.ExecuteCommand("dot", []string{"-Tpng",
		fullPathName + ".dot", "-o", fullPathName + ".png"}); err != nil {
		util_tools.PrintWarning(err)
	} else {
		util_tools.PrintOk("Graph saved into " + fullPathName + ".png")
	}
}
