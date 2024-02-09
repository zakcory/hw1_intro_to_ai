from collections import namedtuple
import search
import random
import math
from itertools import product


ids = ["342663978", "111111111"]


def test(ships):
    all_actions = []
    for ship in ships:
        for k, v in ship.items():
            name = k
            loc = v
            print((v[0]-1, v[1]))


State = namedtuple('State', ['map', 'pirate_ships', 'treasures', 'marine_ships', 'base_location', 'treasures_num'])


class OnePieceProblem(search.Problem):
    """This class implements a medical problem according to problem description file"""

    def __init__(self, initial):
        """Don't forget to implement the goal test
        You should change the initial to your own representation.
        search.Problem.__init__(self, initial) creates the root node"""
        # Adding all the parameters to the list to then pass on the list to the constructor
        state_params = []
        for k, v in initial.items():
            state_params.append(v)

        base_loc = list(initial['pirate_ships'].values())[0]
        state_params.append(base_loc)
        state_params.append(0)

        initial_state = State(*state_params)
        search.Problem.__init__(self, initial_state)
        
    
        
        
        
    def actions(self, state: namedtuple):
        """
        Indicates if a given location is within the map.

        Parameters:
        location (tuple of integers): a tuple of two integers that defines the location on the map

        Returns:
        boolean: if the location is within the map, returns True. Returns False otherwise
        """
        def legal_move(location):
            row_length = len(state.map[0])
            col_length = len(state.map)
            return (0 <= location[0] < col_length and 0 <= location[1] < row_length)
        
        def find_key_by_value(dictionary, value):
            for key, val in dictionary.items():
                if val == value:
                    return key
            return None
        
        actions = []
        offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        actions_per_ship = []
        for m, (i, j) in enumerate(offsets):
            
            for k, (name, loc) in enumerate(state.pirate_ships.items()):
                print(k)
                combo = []
                # Check if the ship is at the base (deposit available)
                if state.base_location == loc and state.treasures_num > 0:
                    combo.append(('deposit_treasures', name))
                    
                
                # Iterating through possible 'sail' and 'collect' actions
                next_location = (loc[0] + i, loc[1] + j)
                print(next_location)
                if legal_move(next_location):
                    print("got in")
                    print(state.map[next_location[0]][next_location[1]])
                    if state.map[next_location[0]][next_location[1]]=='S':
                        combo.append(("sail", name, next_location))
                    elif state.map[next_location[0]][next_location[1]]=='I':
                        combo.append(("collect_treasure", name, find_key_by_value(state.treasures, next_location)))
                    
                if m!=0:
                    combo.append(('wait', name))
                    actions_per_ship[k].append(combo)
            print(actions_per_ship)        
            pro = list(product(*(aps for aps in actions_per_ship)))
            

        return pro
                        
        


    def result(self, state, action):
        """Return the state that results from executing the given
        action in the given state. The action must be one of
        self.actions(state)."""
        if action in self.actions(state):
            pass

    def goal_test(self, state):
        """ Given a state, checks if this is the goal state.
         Returns True if it is, False otherwise."""

    def h(self, node):
        """ This is the heuristic. It gets a node (not a state,
        state can be accessed via node.state)
        and returns a goal distance estimate"""
        return 0

    """Feel free to add your own functions
    (-2, -2, None) means there was a timeout"""


def create_onepiece_problem(game):
    return OnePieceProblem(game)

def main():
    test = {
        'map': [['S', 'S', 'S', 'S', 'I'],
                ['S', 'I', 'S', 'S', 'S'],
                ['S', 'S', 'S', 'S', 'S'],
                ['B', 'S', 'S', 'I', 'S']],
        'pirate_ships': {'pirate_ship_1': (3, 0), 'pirate_ship_2': (3, 0)},
        'treasures': {'treasure_1': (1, 1), 'treasure_2': (3, 3)},
        'marine_ships': {'marine_1': [(3, 2), (2, 2), (2, 3), (2, 4)]}
    }
    pr = OnePieceProblem(test)
    print(pr.actions(pr.initial))


if __name__ == '__main__':
    main()