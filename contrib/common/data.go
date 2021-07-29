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

// Exported struct that represents static and dynamic data.
type Data struct {
	StaticData  StaticData  `json:"static_data"`
	DynamicData DynamicData `json:"dynamic_data"`
}

// Exported struct that represents data for static dependency analysis.
type StaticData struct {
	Dependencies map[string][]string `json:"dependencies"`
	SharedLibs   map[string][]string `json:"shared_libs"`
	SystemCalls  map[string]int      `json:"system_calls"`
	Symbols      map[string]string   `json:"symbols"`
}

// Exported struct that represents data for dynamic dependency analysis.
type DynamicData struct {
	SharedLibs  map[string][]string `json:"shared_libs"`
	SystemCalls map[string]int      `json:"system_calls"`
	Symbols     map[string]string   `json:"symbols"`
}
