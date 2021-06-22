import sys

from crossword import *
import queue


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for var in self.domains:
            not_in = set()
            for word in self.domains[var]:
                if len(word) != var.length:
                    not_in.add(word)
            self.domains[var] = self.domains[var].difference(not_in)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        not_in = set()
        revision_made = False
        for word in self.domains[x]:
            works = False
            for word2 in self.domains[y]:
                if(word2[self.crossword.overlaps[x,y][1]] == word[self.crossword.overlaps[x,y][0]]):
                    works = True
                    break
            if(not works):
                revision_made = True
                not_in.add(word)
        self.domains[x] = self.domains[x].difference(not_in)
        return revision_made


    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if(arcs == None):
            arcs = []
            for var in self.domains:
                for var2 in self.crossword.neighbors(var):
                    arcs.append((var, var2))
        q = queue.Queue()
        for arc in arcs:
            q.put(arc)
        while(not q.empty()):
            (x,y) = q.get()
            if(self.revise(x,y)):
                if (len(self.domains[x]) == 0):
                    return False
                y_set = set()
                y_set.add(y)
                for neighbor in self.crossword.neighbors(x).difference(y_set):
                    q.put((neighbor,x))
        return True


    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        variables = list(self.domains.keys()).copy()
        for var in assignment:
            if(assignment[var] != None):
                if(var in variables):
                    variables.remove(var)
            else:
                return False
        if(len(variables) == 0):
            return True
        return False
            


    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        words_used = set()
        for var in assignment:
            if(len(assignment[var]) != var.length):
                return False
            if(assignment[var] in words_used):
                return False
            if(assignment[var] == None):
                return False
            words_used.add(assignment[var])
            for neighbor in self.crossword.neighbors(var):
                if(neighbor in assignment.keys()):
                    if(assignment[neighbor][self.crossword.overlaps[var,neighbor][1]] != assignment[var][self.crossword.overlaps[var,neighbor][0]]):
                        return False
        return True


    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        domain = self.domains[var]
        priority_list = []
        for word1 in domain:
            excount = 0
            for neighbor in self.crossword.neighbor(var):
                if(neighbor in list(assignment.keys())):
                    continue
                n_domain = self.domains[neighbor]
                for word2 in n_domain:
                    letter1 = word1[self.crossword.overlaps[var,neighbor][0]]
                    letter2 = word2[self.crossword.overlaps[var,neighbor][1]]
                    if(letter1 != letter2 or word1 == word2):
                        excount += 1
            priority_list.append((word1, excount))
        return priority_list.sort(key= lambda var: var[1])



    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        unassigned = None
        for var in self.domains:
            if var not in list(assignment.keys()):
                if(unassigned is None):
                    unassigned = var
                elif(len(self.domains[var]) < len(self.domains[unassigned])):
                    unassigned = var
                elif(len(self.domains[unassigned]) == len(self.domains[var])):
                    if(self.crossword.neighbors(var) > self.crossword.neighbors(unassigned)):
                        unassigned = var
        return unassigned


                 

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if(len(assignment) == len(self.domains)):
            return assignment
        var = self.select_unassigned_variable(assignment)
        for value in self.domains[var]:
            new_assignment = assignment.copy()
            new_assignment[var] = value
            if(self.consistent(new_assignment)):
                result = self.backtrack(new_assignment)
                if result is not None:
                    return result
        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
