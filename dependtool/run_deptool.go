package dependtool

import (
	"fmt"
	"github.com/fatih/color"
	"os"
	u "tools/common"
)

func RunAnalyserTool(homeDir string, data *u.Data) {

	// Support only Unix
	/*if strings.ToLower(runtime.GOOS) != "linux" {
		u.PrintErr("Only UNIX/Linux platforms are supported")
	}*/

	// Init and parse local arguments
	args := new(u.Arguments)
	p, err := args.InitArguments(args)
	if err != nil {
		u.PrintErr(err)
	}
	parseLocalArguments(p, args)

	// Get program path
	programPath, err := u.GetProgramPath(&*args.StringArg[PROGRAM])
	if err != nil {
		u.PrintErr("Could not determine program path", err)
	}

	// Get program Name
	programName := *args.StringArg[PROGRAM]

	// Create the folder 'output' if it does not exist
	outFolder := homeDir + string(os.PathSeparator) + programName +
		"_" + u.OUT_FOLDER
	if _, err := os.Stat(outFolder); os.IsNotExist(err) {
		if err = os.Mkdir(outFolder, os.ModePerm); err != nil {
			u.PrintErr(err)
		}
	}

	// Display Minor Details
	displayProgramDetails(programName, programPath, args)

	// Check if the program is an ELF
	checkElf(&programPath)

	// Run static analyser
	u.PrintHeader1("(1.1) RUN STATIC ANALYSIS")
	runStaticAnalyser(args, programName, programPath, outFolder, data)

	// Run dynamic analyser
	u.PrintHeader1("(1.2) RUN DYNAMIC ANALYSIS")
	runDynamicAnalyser(args, programName, programPath, outFolder, data)

	// Save Data to JSON
	if err = u.RecordDataJson(outFolder+programName, data); err != nil {
		u.PrintErr(err)
	} else {
		u.PrintOk("JSON Data saved into " + outFolder + programName +
			".json")
	}

	// Save graph if full dependencies option is set
	if *args.BoolArg[FULL_DEPS] {
		saveGraph(programName, outFolder, data)
	}
}

// displayProgramDetails display various information such path, background, ...
func displayProgramDetails(programName, programPath string, args *u.Arguments) {
	fmt.Println("----------------------------------------------")
	fmt.Println("Analyze Program: ", color.GreenString(programName))
	fmt.Println("Full Path: ", color.GreenString(programPath))
	if len(*args.StringArg[OPTIONS]) > 0 {
		fmt.Println("Options: ", color.GreenString(*args.StringArg[OPTIONS]))
	}

	if len(*args.StringArg[CONFIG_FILE]) > 0 {
		fmt.Println("Config file: ", color.GreenString(*args.StringArg[OPTIONS]))
	}

	if len(*args.StringArg[TEST_FILE]) > 0 {
		fmt.Println("Test file: ", color.GreenString(*args.StringArg[OPTIONS]))
	}

	fmt.Println("----------------------------------------------")
}

// checkElf checks if the program (from its path) is an ELF file
func checkElf(programPath *string) {
	elfFile, err := GetElf(*programPath)
	if err != nil {
		u.PrintErr(err)
	} else if elfFile == nil {
		*programPath = ""
		u.PrintWarning("Only ELF binaries are supported! Some analysis" +
			" procedures will be skipped")
	} else {
		// Get ELF architecture
		architecture, machine := GetElfArchitecture(elfFile)
		fmt.Println("ELF Class: ", architecture)
		fmt.Println("Machine: ", machine)
		fmt.Println("Entry Point: ", elfFile.Entry)
		fmt.Println("----------------------------------------------")
	}
}

// runStaticAnalyser runs the static analyser
func runStaticAnalyser(args *u.Arguments, programName, programPath,
	outFolder string, data *u.Data) {

	staticAnalyser(*args, data, programPath)

	// Save static Data into text file if display mode is set
	if *args.BoolArg[SAVE_OUTPUT] {

		// Create the folder 'output/static' if it does not exist
		outFolderStatic := outFolder + "static" + string(os.PathSeparator)
		if _, err := os.Stat(outFolderStatic); os.IsNotExist(err) {
			if err = os.Mkdir(outFolderStatic, os.ModePerm); err != nil {
				u.PrintErr(err)
			}
		}

		fn := outFolderStatic + programName + ".txt"
		headersStr := []string{"Dependencies (from apt-cache show) list:",
			"Shared libraries list:", "System calls list:", "Symbols list:"}

		if err := u.RecordDataTxt(fn, headersStr, data.StaticData); err != nil {
			u.PrintWarning(err)
		} else {
			u.PrintOk("Data saved into " + fn)
		}
	}
}

// runDynamicAnalyser runs the dynamic analyser.
func runDynamicAnalyser(args *u.Arguments, programName, programPath,
	outFolder string, data *u.Data) {

	dynamicAnalyser(args, data, programPath)

	// Save dynamic Data into text file if display mode is set
	if *args.BoolArg[SAVE_OUTPUT] {

		// Create the folder 'output/dynamic' if it does not exist
		outFolderDynamic := outFolder + "dynamic" + string(os.PathSeparator)
		if _, err := os.Stat(outFolderDynamic); os.IsNotExist(err) {
			if err = os.Mkdir(outFolderDynamic, os.ModePerm); err != nil {
				u.PrintErr(err)
			}
		}

		fn := outFolderDynamic + programName + ".txt"
		headersStr := []string{"Shared libraries list:", "System calls list:",
			"Symbols list:"}

		if err := u.RecordDataTxt(fn, headersStr, data.DynamicData); err != nil {
			u.PrintWarning(err)
		} else {
			u.PrintOk("Data saved into " + fn)
		}
	}
}

// saveGraph saves dependency graphs of a given app into the output folder.
func saveGraph(programName, outFolder string, data *u.Data) {

	sep := string(os.PathSeparator)
	if len(data.StaticData.SharedLibs) > 0 {
		u.GenerateGraph(programName, outFolder+"static"+sep+
			programName+"_shared_libs", data.StaticData.SharedLibs)
	}

	if len(data.StaticData.Dependencies) > 0 {
		u.GenerateGraph(programName, outFolder+"static"+sep+
			programName+"_dependencies", data.StaticData.Dependencies)
	}

	if len(data.StaticData.SharedLibs) > 0 {
		u.GenerateGraph(programName, outFolder+"dynamic"+sep+
			programName+"_shared_libs", data.DynamicData.SharedLibs)
	}
}
