// Copyright 2019 The UNICORE Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file
//
// Author: Gaulthier Gain <gaulthier.gain@uliege.be>

package common

import (
	"math/rand"
	"os"

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

// CreateGraph is a wrapper to CreateGraphLabel.
//
// It returns a graph which represents all the direct and no-direct dependencies
// of a given application and an error if any, otherwise it returns nil.
func CreateGraph(name string, data map[string][]string) (*gographviz.Escape, error) {
	return CreateGraphLabel(name, data, nil)
}

// CreateGraphLabel creates a graph from a map.
//
// It returns a graph which represents all the direct and no-direct dependencies
// of a given application and an error if any, otherwise it returns nil.
func CreateGraphLabel(name string, data map[string][]string,
	mapLabel map[string]string) (*gographviz.Escape, error) {

	graph := gographviz.NewEscape()

	if err := graph.SetName(name); err != nil {
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

		attributes := map[string]string{"color": colorsMap[key]}

		// Create nodes
		if err := graph.AddNode("\""+key+"\"", "\""+key+"\"",
			attributes); err != nil {
			return nil, err
		}

		if values != nil {

			// Add edges
			for _, v := range values {

				if label, ok := mapLabel[v]; ok {
					attributes["label"] = label
				}

				if err := graph.AddEdge("\""+key+"\"", "\""+v+"\"", true,
					attributes); err != nil {
					return nil, err
				}

				// Delete label attributes if necessary
				if _, ok := mapLabel[v]; ok {
					delete(attributes, "label")
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
		PrintWarning(err)
	}

	// Save graph as '.png' file
	if _, err := ExecuteCommand("dot", []string{"-Tpng",
		fullPathName + ".dot", "-o", fullPathName + ".png"}); err != nil {
		PrintWarning(err)
	} else {
		PrintOk("Graph saved into " + fullPathName + ".png")
	}
}
