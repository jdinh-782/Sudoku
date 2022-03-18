#!/usr/bin/env python3

import sys
import os
import math
import SudokuBoard
import Constraint
import ConstraintNetwork
import BTSolver
import Trail
import time

"""
    Main driver file, which is responsible for interfacing with the
    command line and properly starting the backtrack solver.
"""

def main ( ):
    args = sys.argv

    # Important Variables
    file   = "sample_board.TXT";
    var_sh = "";
    val_sh = "";
    cc     = "norvigCheck";

    for arg in [args[i] for i in range(1, len(args))]:
        print(f"arg: {arg}")

        if arg == "MRV":
            var_sh = "MinimumRemainingValue"

        elif arg == "MAD":
            var_sh = "MRVwithTieBreaker"

        elif arg == "LCV":
            val_sh = "LeastConstrainingValue"

        elif arg == "FC":
            cc = "forwardChecking"

        elif arg == "NOR":
            cc = "norvigCheck"

        elif arg == "TOURN":
            var_sh = "tournVar"
            val_sh = "tournVal"
            cc     = "tournCC"

        else:
            file = arg;

    trail = Trail.Trail();

    # if no file is specified
    if file == "":
        sudokudata = SudokuBoard.SudokuBoard( 3, 3, 7 )
        print(sudokudata)

        solver = BTSolver.BTSolver( sudokudata, trail, val_sh, var_sh, cc )

        # checks if cc is defined
        if cc in ["forwardChecking","norvigCheck","tournCC"]:
            solver.checkConsistency()

        # where the actual solving occurs
        solver.solve()

        if solver.hassolution:
            print("solution!")
            print( solver.getSolution() )
            print( "Trail Pushes: " + str(trail.getPushCount()) )
            print( "Backtracks: " + str(trail.getUndoCount()) )

        else:
            print("Trail Pushes: " + str(trail.getPushCount()))
            print("Backtracks: " + str(trail.getUndoCount()))

            print(sudokudata)
            print( "Failed to find a solution" )

        return

    if os.path.isdir(file):
        listOfBoards = None

        try:
            listOfBoards = os.listdir ( file )
        except:
            print ( "[ERROR] Failed to open directory." )
            return

        numSolutions = 0
        for f in listOfBoards:
            print ( "Running board: " + str(f) )
            sudokudata = SudokuBoard.SudokuBoard( filepath=os.path.join( file, f ) )

            solver = BTSolver.BTSolver( sudokudata, trail, val_sh, var_sh, cc )
            if cc in ["forwardChecking","norvigCheck","tournCC"]:
                solver.checkConsistency() # this is where solver checks for heuristics and checking techniques
            solver.solve()

            if solver.hassolution:
                numSolutions += 1;

        print ( "Solutions Found: " + str(numSolutions) )
        print ( "Trail Pushes: " + str(trail.getPushCount()) )
        print ( "Backtracks: "  + str(trail.getUndoCount()) )

        return

    sudokudata =  SudokuBoard.SudokuBoard( filepath=os.path.abspath( file ) )
    print(sudokudata)

    solver = BTSolver.BTSolver( sudokudata, trail, val_sh, var_sh, cc )
    if cc in ["forwardChecking","norvigCheck","tournCC"]:
        solver.checkConsistency()
    solver.solve()

    if solver.hassolution:
        print( solver.getSolution() )
        print( "Trail Pushes: " + str(trail.getPushCount()) )
        print( "Backtracks: " + str(trail.getUndoCount()) )

    else:
        print( "Failed to find a solution" )

start_time = time.time()
main()
print(f"algorithm took {time.time() - start_time} seconds")

