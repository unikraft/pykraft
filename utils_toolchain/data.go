// Copyright 2019 The UNICORE Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file
//
// Author: Gaulthier Gain <gaulthier.gain@uliege.be>

package util_tools

type Data struct {
	StaticData  StaticData  `json:"static_data"`
}

type StaticData struct {
	Dependencies map[string][]string `json:"dependencies"`
	SharedLibs   map[string][]string `json:"shared_libs"`
	SystemCalls  map[string]string   `json:"system_calls"`
	Symbols      map[string]string   `json:"symbols"`
}