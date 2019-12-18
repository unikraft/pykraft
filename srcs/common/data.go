// Copyright 2019 The UNICORE Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file
//
// Author: Gaulthier Gain <gaulthier.gain@uliege.be>

package common

// Exported struct that represents static and dynamic data.
type Data struct {
	StaticData  StaticData  `json:"static_data"`
	DynamicData DynamicData `json:"dynamic_data"`
}

// Exported struct that represents data for static dependency analysis.
type StaticData struct {
	Dependencies map[string][]string `json:"dependencies"`
	SharedLibs   map[string][]string `json:"shared_libs"`
	SystemCalls  map[string]string   `json:"system_calls"`
	Symbols      map[string]string   `json:"symbols"`
}

// Exported struct that represents data for dynamic dependency analysis.
type DynamicData struct {
	SharedLibs  map[string][]string `json:"shared_libs"`
	SystemCalls map[string]string   `json:"system_calls"`
	Symbols     map[string]string   `json:"symbols"`
}
