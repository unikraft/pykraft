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
	"math/rand"
	"os"

	"github.com/awalterschulze/gographviz"
)

const letters = "0123456789ABCDEF"

// RandStringBytes generates random string of size n.
//
// It returns a random string of a particular length.
func RandStringBytes(n int) string {

	b := make([]byte, n)
	for i := range b {
		b[i] = letters[rand.Intn(len(letters))]
	}
	return string(b)
}

// ColorGenerator generates a color in RGB format.
//
// It returns a string which represents a random string formatted as RGB color.
func ColorGenerator() string {
	return "#" + RandStringBytes(6)
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
func GenerateGraph(programName, fullPathName string, data map[string][]string,
	mapLabel map[string]string) {
	// Create graph
	graph, err := CreateGraphLabel(programName, data, mapLabel)

	// Save graph as '.dot' file
	if err = SaveGraphToFile(fullPathName+".dot", graph); err != nil {
		PrintWarning(err)
	}

	// Save graph as '.png' file
	if _, err := ExecuteCommand("dot", []string{"-Tpng",
		fullPathName + ".dot", "-o", fullPathName + ".png"}); err != nil {
		PrintWarning(err)
		PrintWarning("Open the following website to display the graph:" +
			" https://dreampuf.github.io/GraphvizOnline/")
	} else {
		PrintOk("Graph saved into " + fullPathName + ".png")
	}
}
