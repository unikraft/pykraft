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
	"bufio"
	"io"
	"io/ioutil"
	"os"
)

// Exported constants for folder management
const (
	SEP       = string(os.PathSeparator)
	OUTFOLDER = "output" + SEP
	PERM      = 0755
)

// OpenTextFile opens a file named by filename.
//
// It returns a slice of bytes which represents its content and an error if
// any, otherwise it returns nil.
func OpenTextFile(filename string) ([]byte, error) {
	file, err := os.Open(filename)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	return ioutil.ReadAll(file)
}

// UpdateFile updates a file named by filename by adding new bytes at the end.
//
// It returns a slice of bytes which represents its content and an error if
// any, otherwise it returns nil.
func UpdateFile(filename string, dataByte []byte) error {
	input, err := ioutil.ReadFile(filename)
	if err != nil {
		return err
	}

	result := append(input, dataByte...)

	return WriteToFile(filename, result)
}

// WriteToFile creates and writes bytes content to a new file named by filename.
//
// It returns an error if any, otherwise it returns nil.
func WriteToFile(filename string, dataByte []byte) error {
	err := ioutil.WriteFile(filename, dataByte, PERM)
	return err
}

// OSReadDir reads the content of a folder named by root.
//
// It returns a slice of FileInfo values and an error if any, otherwise it
// returns nil.
func OSReadDir(root string) ([]os.FileInfo, error) {
	var files []os.FileInfo
	f, err := os.Open(root)
	if err != nil {
		return files, err
	}
	fileInfo, err := f.Readdir(-1)
	f.Close()
	if err != nil {
		return files, err
	}

	for _, file := range fileInfo {
		files = append(files, file)
	}
	return files, nil
}

// Exists checks if a given file exists.
//
// It returns true if the file exists and an error if any, otherwise it
// returns nil.
func Exists(path string) (bool, error) {
	_, err := os.Stat(path)
	if err == nil {
		return true, nil
	}

	if os.IsNotExist(err) {
		return false, nil
	}

	return true, err
}

// CreateFolder creates a folder if it does not exist.
//
// It returns true if the folder is created and an error if any, otherwise it
// returns nil.
func CreateFolder(path string) (bool, error) {
	if _, err := os.Stat(path); os.IsNotExist(err) {
		if err = os.Mkdir(path, PERM); err != nil {
			return false, err
		}
		return true, nil
	}
	return false, nil
}

// ReadLinesFile Reads a file line by line and saves its content into a slice.
//
// It returns a slice of string which represents each line of a file and an
// error if any, otherwise it returns nil.
func ReadLinesFile(path string) ([]string, error) {

	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	rd := bufio.NewReader(f)

	var lines []string
	for {
		line, err := rd.ReadString('\n')

		if len(line) == 0 {
			break
		}

		// End of file, break the reading
		if err == io.EOF {
			lines = append(lines, line)
			break
		}

		if err != nil {
			return nil, err
		}
		lines = append(lines, line)
	}

	return lines, err
}

// CopyFileContents copies the contents of the file named src to the file named
// by dst. The file will be created if it does not already exist. If the
// destination file exists, all it's contents will be replaced by the contents
// of the source file.
//
// It returns an error if any, otherwise it returns nil.
func CopyFileContents(src, dst string) (err error) {
	in, err := os.Open(src)
	if err != nil {
		return
	}
	defer in.Close()
	out, err := os.Create(dst)
	if err != nil {
		return
	}
	defer func() {
		cErr := out.Close()
		if err == nil {
			err = cErr
		}
	}()
	if _, err = io.Copy(out, in); err != nil {
		return
	}
	err = out.Sync()
	return
}
