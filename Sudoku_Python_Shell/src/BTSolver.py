# from xml import dom

# from sklearn.neighbors import NeighborhoodComponentsAnalysis
import SudokuBoard
import Variable
import Domain
import Trail
import Constraint
import ConstraintNetwork
import time
import random

from pprint import pprint


class BTSolver:

    # ==================================================================
    # Constructors
    # ==================================================================

    def __init__ ( self, gb, trail, val_sh, var_sh, cc ):
        self.network = ConstraintNetwork.ConstraintNetwork(gb)
        self.hassolution = False
        self.gameboard = gb
        self.trail = trail

        self.varHeuristics = var_sh
        self.valHeuristics = val_sh
        self.cChecks = cc

    # ==================================================================
    # Consistency Checks
    # ==================================================================

    # Basic consistency check, no propagation done
    def assignmentsCheck ( self ):
        for c in self.network.getConstraints():
            if not c.isConsistent():
                return False
        return True

    """
        Part 1 TODO: Implement the Forward Checking Heuristic

        This function will do both Constraint Propagation and check
        the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        Note: remember to trail.push variables before you assign them
        Return: a tuple of a dictionary and a bool. The dictionary contains all MODIFIED variables, mapped to their MODIFIED domain.
                The bool is true if assignment is consistent, false otherwise.
    """
    def forwardChecking ( self ):
        # these are the variables that are already assigned from the start
        # assignedVars = []
        #
        # for c in self.network.constraints:
        #     # print(f"c -> {c}")
        #     for v in c.vars:
        #         # print(f"v -> {v}")
        #         if v.isAssigned():
        #             # print(f"assigned v -> {v}")
        #             assignedVars.append(v)

        modified = dict()

        # these are the variables that are already assigned from the start
        assignedVars = []
        for c in self.network.constraints:
            for v in c.vars:
                if v.assigned is True and v not in assignedVars:
                    assignedVars.append(v)

        while len(assignedVars) != 0:
            av = assignedVars.pop(0)

            # variable to look at
            # print(av)

            # value of variable to look at (cannot be used again in its box, row and col)
            val = av.getAssignment()

            for neighbor in self.network.getNeighborsOfVariable(av):
                if neighbor.assigned is False and neighbor.getDomain().contains(val) and neighbor.isChangeable:
                    self.trail.push(neighbor)

                    neighbor.removeValueFromDomain(val)

                    # add MODIFIED variable with its MODIFIED DOMAIN to dictionary
                    modified[neighbor.name] = neighbor.getDomain()

                    if neighbor.domain.size() == 0:
                        return (modified, False)
                    elif neighbor.domain.size() == 1:
                        assignedVars.append(neighbor)


        return (modified, self.assignmentsCheck())


    # =================================================================
	# Arc Consistency
	# =================================================================
    def arcConsistency( self ):
        assignedVars = []
        for c in self.network.constraints:
            for v in c.vars:
                if v.isAssigned():
                    assignedVars.append(v)
        while len(assignedVars) != 0:
            av = assignedVars.pop(0)
            for neighbor in self.network.getNeighborsOfVariable(av):
                if neighbor.isChangeable and not neighbor.isAssigned() and neighbor.getDomain().contains(av.getAssignment()):
                    neighbor.removeValueFromDomain(av.getAssignment())
                    if neighbor.domain.size() == 1:
                        neighbor.assignValue(neighbor.domain.values[0])
                        assignedVars.append(neighbor)

    
    """
        Part 2 TODO: Implement both of Norvig's Heuristics

        This function will do both Constraint Propagation and check
        the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        (2) If a constraint has only one possible place for a value
            then put the value there.

        Note: remember to trail.push variables before you assign them
        Return: a pair of a dictionary and a bool. The dictionary contains all variables 
		        that were ASSIGNED during the whole NorvigCheck propagation, and mapped to the values that they were assigned.
                The bool is true if assignment is consistent, false otherwise.
    """
    def norvigCheck ( self ):
        assigned = dict()
        assignedVars = []

        # FIRST CONDITION OF NORVIG'S CHECK
        for c in self.network.constraints:
            for v in c.vars:
                if v.assigned is True and v not in assignedVars:
                    assignedVars.append(v)

        while len(assignedVars) != 0:
            av = assignedVars.pop(0)
            val = av.getAssignment()

            # print(f"variable -> {av}")

            for neighbor in self.network.getNeighborsOfVariable(av):
                if neighbor.assigned is False and neighbor.getDomain().contains(val) and neighbor.isChangeable:
                    self.trail.push(neighbor)

                    neighbor.removeValueFromDomain(val)

                    if neighbor.domain.size() == 0:
                        return (assigned, False)
                    elif neighbor.domain.size() == 1:
                        # add ASSIGNED variable with its ASSIGNED VALUE to dictionary
                        assigned[neighbor.name] = neighbor.domain.values[0]

                        neighbor.assignValue(neighbor.domain.values[0])

                        assignedVars.append(neighbor)

        # KEEP TESTING
        # second condition of Norvig's Check
        # look at all constraints
        # as long as a variable contains a certain value in which none of its peers in a constraint have,
        # assign it THAT value
        # e.g. want to assign value to v1, v1 = {1, 2, 3, 4}
        # v2, v3, v4 are in a constraint along with v1
        # v2 = v3 = v4 = {1, 2, 3}
        # since v2, v3, v4 don't contain a '4', v1 must be '4'

        # iterate through all constraints in network
        for c in self.network.getConstraints():
            # for v in c.vars:
            #     print(v)

            # create a list of unassigned variables that are in a constraint
            ls = [var for var in c.vars if not var.assigned and var.isChangeable]

            possible_values = []

            # get all values from unassigned variables (these are all the possible values that COULD BE assigned)
            for v in ls:
                for val in v.domain.values:
                    possible_values.append(val)

            # since more than one domain can have same values, only want to iterate through unique values
            non_duplicates = list(set(possible_values))

            # check for each unique value, if it only appears once => there must be only one variable that has that value
            for val in non_duplicates:
                occurrences = possible_values.count(val)

                # can only happen once since specific value can only be present in one variable (for this condition)
                # domains must have size > 1 since variables should be unassigned
                if occurrences == 1:
                    for var in c.vars:
                        # find which variable's domain the value is present in
                        if val in var.domain.values:
                            self.trail.push(var)

                            # add ASSIGNED variable with its ASSIGNED VALUE to dictionary
                            assigned[var.name] = val  # has an effect
                            var.assignValue(val)  # has an effect


                            # assignedVars.append(var)  # commented

                            # remove the rest of the values in variable's domain (this may not have an effect)
                            for x in non_duplicates:
                                if x != val:
                                    var.removeValueFromDomain(x)
                            break

        #     print('')
        # print('\n')


        return (assigned, self.assignmentsCheck())

    """
         Optional TODO: Implement your own advanced Constraint Propagation

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournCC ( self ):
        assignedVars = [v for v in self.network.getVariables() if v.assigned]
        assigned = dict()

        # for var in assignedVars:
        #     print(var)

        while len(assignedVars) != 0:
            av = assignedVars.pop(0)
            val = av.getAssignment()

            for neighbor in self.network.getNeighborsOfVariable(av):
                if neighbor.assigned is False and neighbor.getDomain().contains(val) and neighbor.isChangeable:
                    self.trail.push(neighbor)

                    neighbor.removeValueFromDomain(val)

                    if neighbor.domain.size() == 0:
                        return (assigned, False)
                    elif neighbor.domain.size() == 1:
                        # add ASSIGNED variable with its ASSIGNED VALUE to dictionary
                        assigned[neighbor.name] = neighbor.domain.values[0]

                        neighbor.assignValue(neighbor.domain.values[0])

                        assignedVars.append(neighbor)

        for c in self.network.getConstraints():
            # for v in c.vars:
            #     print(v)

            # create a list of unassigned variables that are in a constraint
            ls = [var for var in c.vars if var.assigned is False and var.isChangeable]
            possible_values = []

            # get all values from unassigned variables (these are the possible values it can have)
            for v in ls:
                for val in v.domain.values:
                    possible_values.append(val)

            # since more than one domain can have same values, only want to iterate through unique values
            non_duplicates = list(set(possible_values))

            # check for each unique value, if it only appears once => there must be only one variable that has that value
            for val in non_duplicates:
                occurrences = possible_values.count(val)

                # can only happen once since specific value can only be present in one variable (for this condition)
                # domains must have size > 1 since variables should be unassigned
                if occurrences == 1:
                    # print(val)
                    for var in c.vars:
                        if val in var.domain.values:
                            self.trail.push(var)

                            # add ASSIGNED variable with its ASSIGNED VALUE to dictionary
                            assigned[var.name] = val  # has an effect
                            var.assignValue(val)  # has an effect


        return (self.assignmentsCheck())

    # ==================================================================
    # Variable Selectors
    # ==================================================================

    # Basic variable selector, returns first unassigned variable
    def getfirstUnassignedVariable ( self ):
        for v in self.network.variables:
            if not v.isAssigned():
                return v

        # Everything is assigned
        return None

    """
        Part 1 TODO: Implement the Minimum Remaining Value Heuristic

        Return: The unassigned variable with the smallest domain
    """
    def getMRV ( self ):
        # look at ALL unassigned variables, then return the variable with the smallest domain
        unassigned_var = self.getfirstUnassignedVariable()

        for v in self.network.variables:
            if not v.isAssigned() and v.domain.size() < unassigned_var.domain.size():
                unassigned_var = v
                # print(unassigned_var)

        # print('\n')

        if unassigned_var is not None:
            return unassigned_var
        return None

    """
        Part 2 TODO: Implement the Minimum Remaining Value Heuristic
                       with Degree Heuristic as a Tie Breaker

        Return: The unassigned variable with the smallest domain and affecting the most unassigned neighbors.
                If there are multiple variables that have the same smallest domain with the same number of unassigned neighbors, add them to the list of Variables.
                If there is only one variable, return the list of size 1 containing that variable.
    """

    def MRVwithTieBreaker ( self ):
        # consider a matrix of "degrees" where each entry is the degree of that variable => take min of matrix


        # use MRV to get the unassigned variable with smallest domain
        var_MRV = self.getMRV()
        unassigned_vars = []

        # now check if there are other variables whose domain size are <= var_MRV's
        for v in self.network.variables:
            if not v.isAssigned() and v.domain.size() <= var_MRV.domain.size():
                unassigned_vars.append(v)

        # return [None] if no unassigned variables remain
        if len(unassigned_vars) == 0:
            return [None]

        # then check which of the unassigned variables has the greatest number of unassigned neighbors
        vars_dict = dict()

        for v in unassigned_vars:
            unassigned_neighbors = 0

            for neighbor in self.network.getNeighborsOfVariable(v):
                if not neighbor.isAssigned():
                    unassigned_neighbors += 1
            # print(unassigned_neighbors)

            vars_dict[v] = unassigned_neighbors

        # get maximum number of unassigned neighbors, then find all unassigned variables whose 'key' matches the max
        max_unassignedNeighbors = max(vars_dict.values())
        unassigned_vars = [key for key in vars_dict if vars_dict[key] == max_unassignedNeighbors]

        return unassigned_vars

    """
         Optional TODO: Implement your own advanced Variable Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournVar ( self ):
        var_domains = []

        for var in self.network.getVariables():
            if var.isChangeable and not var.isAssigned():
                var_domains.append((var, var.size()))

        if (len(var_domains) == 0):
            return None

        return min(var_domains, key=lambda v: v[1])[0]

    # ==================================================================
    # Value Selectors
    # ==================================================================

    # Default Value Ordering
    def getValuesInOrder ( self, v ):
        values = v.domain.values
        return sorted( values )

    """
        Part 1 TODO: Implement the Least Constraining Value Heuristic

        The Least constraining value is the one that will knock the least
        values out of it's neighbors domain.

        Return: A list of v's domain sorted by the LCV heuristic
                The LCV is first and the MCV is last
    """
    def getValuesLCVOrder ( self, v ):
        # variable has empty domain
        if v is None:
            return []

        values_to_look_at = v.getDomain().values
        all_values = list()

        for network in self.network.getNeighborsOfVariable(v):
            all_values.extend(network.getDomain().values)

        # cannot find any more values from neighbors' domains
        if all_values is None:
            return []

        # find number of occurrences for each value in v
        values_LCV_order = dict()
        for val in values_to_look_at:
            values_LCV_order[val] = all_values.count(val)

        # print(values_LCV_order)
        # print(sorted(values_LCV_order, key=values_LCV_order.get))

        return sorted(values_LCV_order, key=values_LCV_order.get)

    """
         Optional TODO: Implement your own advanced Value Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournVal ( self, v ):
        # variable has empty domain
        if v is None:
            return []

        values_to_look_at = v.getDomain().values
        all_values = list()

        for network in self.network.getNeighborsOfVariable(v):
            all_values.extend(network.getDomain().values)

        # cannot find any more values from neighbors' domains
        if all_values is None:
            return []

        # find number of occurrences for each value in v
        values_LCV_order = dict()
        for val in values_to_look_at:
            values_LCV_order[val] = all_values.count(val)

        return sorted(values_LCV_order, key=values_LCV_order.get)

    # ==================================================================
    # Engine Functions
    # ==================================================================

    def solve ( self, time_left=600): # default time is 600 seconds
        if time_left <= 60:
            print("ran out of time")

            return -1

        start_time = time.time()
        if self.hassolution:
            return 0

        # Variable Selection
        v = self.selectNextVariable()
        # print(v)

        # check if the assigment is complete
        if ( v == None ):
            # print(v)

            # Success
            self.hassolution = True
            return 0

        # Attempt to assign a value
        for i in self.getNextValues( v ):

            # Store place in trail and push variable's state on trail
            self.trail.placeTrailMarker()
            self.trail.push( v )

            # Assign the value
            v.assignValue( i )

            # print(v)

            # Propagate constraints, check consistency, recur
            if self.checkConsistency():
                elapsed_time = time.time() - start_time 
                new_start_time = time_left - elapsed_time
                if self.solve(time_left=new_start_time) == -1:
                    return -1
                
            # If this assignment succeeded, return
            if self.hassolution:
                return 0

            # Otherwise backtrack
            self.trail.undo()

        return 0

    def checkConsistency ( self ):
        if self.cChecks == "forwardChecking":
            # print(self.forwardChecking()[1])
            return self.forwardChecking()[1]

        if self.cChecks == "norvigCheck":
            return self.norvigCheck()[1]

        if self.cChecks == "tournCC":
            return self.getTournCC()

        else:
            return self.assignmentsCheck()

    def selectNextVariable ( self ):
        if self.varHeuristics == "MinimumRemainingValue":
            return self.getMRV()

        if self.varHeuristics == "MRVwithTieBreaker":
            return self.MRVwithTieBreaker()[0]

        if self.varHeuristics == "tournVar":
            return self.getTournVar()

        else:
            return self.getfirstUnassignedVariable()

    def getNextValues ( self, v ):
        if self.valHeuristics == "LeastConstrainingValue":
            return self.getValuesLCVOrder( v )

        if self.valHeuristics == "tournVal":
            return self.getTournVal( v )

        else:
            return self.getValuesInOrder( v )

    def getSolution ( self ):
        return self.network.toSudokuBoard(self.gameboard.p, self.gameboard.q)
