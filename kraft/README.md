# Kraft - One stop tool to do unikraft

The core script “Kraft” has following three parts –  

**kraft.py:** The core script implementation.   
**modules:** Contins all the custom modules used by the scripts.  
**commands:** This contains individual command implementations. 


# Configuration
Install `Python3.7 or above`
Add `modules` directory path to `PYTHONPATH` environmental variable.

**If you are on Linux**  
- Open your favorite terminal program.
- Open the file `~/.bashrc` in your text editor – e.g. `vim ~/.bashrc`
- Add the following line to the end:  
`export PYTHONPATH=$PYTHONPATH:/path/to/modules`  
- Save the file.
- Close your terminal application.
- Start your terminal application again, to read in the new settings, and type this:
`echo $PYTHONPATH`  
- It should show your `modules` path

**If you are on a Mac**  
- Open Terminal.app.  
- Open the file `~/.bash_profile` in your text editor – e.g. atom `~/.bash_profile`
- Add the following line to the end -  
`export PYTHONPATH=$PYTHONPATH:/path/to/modules`  
- Save the file.
- Close your terminal application.
- Start your terminal application again, to read in the new settings, and type this:
`echo $PYTHONPATH`  
- It should show your `modules` path

**If you are on Windows**
- Got to the Windows menu, right-click on “Computer” and select “Properties”
- From the computer properties dialog, select `Advanced system settings` on the left.
- From the advanced system settings dialog, choose the `Environment variables` button.
- In the Environment variables dialog, click the `New` button in the top half of the dialog, to make a new user variable.
- Give the variable name as `PYTHONPATH` and the value is the path to the `modules` directory. Choose OK and OK again to save this variable.
- Now open a `cmd` Window (Windows key, then type cmd and press Return). Type: `
echo %PYTHONPATH%`
to confirm the environment variable is correctly set.

# Usage

```
usage: kraft <command> [<args>]

Available kraft <command> are:
   list         :Lists all available app repos and internal/extermal plats on unikraft github
   fetch        :Clones the chosen app repo and its dependencies, and set the right branches/commits.
   configure    :Uses the default .config file in the app repo and Unikraft's build system's
                 make defconfig to set up a .config file to build from
   build        :Essentially runs make. If kraft fetch and kraft configure haven't been run, kraft build
                 runs these first. If the arch's not given, uses the local host's CPU arch
   createfs     :Generates filesystems for multiple libs and apps.
   run          :Runs the unikraft generated unikernels on multiple platforms
                 (Requires kvm-guest, xen-guest and solo5-hvt installed)
   update       :git pull's from all cloned repos. If git-tag is given, checkout that tag and pull.
   create       :Creates the repo skeleton which can be directly pushed on to Github

```

 

