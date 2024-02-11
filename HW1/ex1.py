from collections import namedtuple
import search
import random
import math
from itertools import product

ids = ["342663978", "207341785"]


def test(ships): # TODO : what is this for?
    all_actions = []
    for ship in ships:
        for k, v in ship.items():
            name = k
            loc = v
            print("ship name: ", name,", loc: ", (v[0] - 1, v[1]))


State_tuple = namedtuple('State_tuple', ['pirate_ships_loc', 'treasures_on_ships',
                             'not_collected_treasures_loc', 'collected_treasures_in_base_num',
                             'marine_ships_loc'])
# TODO i think about adding to State: a timestamp and the place of each marine_ship in the specific timestamp ,
#  or maybe we add them in node instead?


class State(State_tuple):  # state must be hashable - so we need to make it hashable
    def __hash__(self):  # TODO : needs implementation
        return self.collected_treasures_in_base_num


class OnePieceProblem(search.Problem):
    """This class implements a medical problem according to problem description file
        contain attributes: self.map, self.pirate_ships_names, self.treasures_loc, self.marine_ships_input_route,
         self.marine_route_cycle, self.base_loc
        contain methods:__init__, marine_ship_loc_at_t,
    """

    def __init__(self, initial):
        """Don't forget to implement the goal test
        You should change the initial to your own representation.
        search.Problem.__init__(self, initial) creates the root node"""
        # Adding all the parameters to the list to then pass on the list to the constructor
        init_state_params = []
        self.map = None
        for k, v in initial.items():
            if k == "map":
                self.map = v
            elif k == "pirate_ships":
                self.pirate_ships_names = list(v.keys())
                init_state_params.append(v)  # 'pirate_ships_loc'
                init_state_params.append(dict())  # 'treasures_on_ships' : dict{ ship_name : treasures_names (at
                #                                                                              most two treasures) ...}

            elif k == "treasures":
                self.treasures_loc = v
                init_state_params.append(v)  # not_collected_treasures_loc
                init_state_params.append(0)  # 'collected_treasures_in_base_num'

            elif k == "marine_ships":
                self.marine_ships_input_route = v  # TODO not sure if we need this variable

                init_loc = dict()
                self.marine_route_cycle = dict()  # will use this to keep track of the marine locations at time t
                for key, value in v.items():
                    route = list(value)
                    route = route + route[len(route)-2:0:-1]
                    self.marine_route_cycle.update({key: route})
                    init_loc.update({key: route[0]})

                init_state_params.append(init_loc)  # 'marine_ships_loc'

        self.base_loc = list(initial['pirate_ships'].values())[0]

        initial_state = State(*init_state_params)
        search.Problem.__init__(self, initial_state)  # TODO check note bellow:
        # shouldn't we also define goal state/s? it should  be all possible states were all treasures are collected.
        # I know that there is a goal test,but we should keep this note in case we needed it

    def marine_ship_loc_at_t(self, marine_ship_name, timestamp):
        """ Returns the location of the marine_ship_name at given timestamp"""
        cycle_route = list(self.marine_route_cycle.get(marine_ship_name))
        return cycle_route[timestamp % len(cycle_route)]

    def actions(self, state: namedtuple):
        """Returns all the actions that can be executed in the given
                state. The result should be a tuple (or other iterable) of actions
                as defined in the problem description file"""

        def legal_move(location):
            """
                   Indicates if a given location is within the map.

                   Parameters:
                   location (tuple of integers): a tuple of two integers that defines the location on the map

                   Returns:
                   boolean: if the location is within the map, returns True. Returns False otherwise
            """
            rows_num = len(state.map)
            cols_num = len(state.map[0])
            return (0 <= location[0] < rows_num) and (0 <= location[1] < cols_num)

        def find_key_by_value(dictionary, value):  # TODO what is this for?
            for key, val in dictionary.items():
                if val == value:
                    return key
            return None

        # TODO can you explain the code here?
        actions = []
        offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        actions_per_ship = []   # list of all possible actions per ship
        

        for k, (name, loc) in enumerate(state.pirate_ships.items()):
            combo = []  # list of actions possible for a certain ship (atomic)
            # Wait action is always available
            combo.append(('wait', name))

            # Check if the ship is at the base (deposit available)
            if state.base_location == loc and state.treasures_num > 0:
                combo.append(('deposit_treasures', name))

            # Going over each possible cell to move (horizontally and vertically)
            for m, (i, j) in enumerate(offsets):
                if abs(i) != abs(j):    # diagonal is an illegal move (-1,1). (when exploring 'sail' options, staying in the same cell is not an option)
                    # Iterating through possible 'sail' and 'collect' actions
                    next_location = (loc[0] + i, loc[1] + j)
                    print(next_location)
                    if legal_move(next_location):
                        print("got in")
                        print(state.map[next_location[0]][next_location[1]])
                        if state.map[next_location[0]][next_location[1]] == 'S':
                            combo.append(("sail", name, next_location))
                        elif state.map[next_location[0]][next_location[1]] == 'I':
                            combo.append(("collect_treasure", name, find_key_by_value(state.treasures, next_location)))
            actions_per_ship.append(combo)
            product = list(product(*(aps for aps in actions_per_ship)))
        return product

    def result(self, state, action):
        """Return the state that results from executing the given
        action in the given state. The action must be one of
        self.actions(state)."""
        if action in self.actions(state):
            pass

    def goal_test(self, state):
        """ Given a state, checks if this is the goal state.
         Returns True if it is, False otherwise."""
        return len(state.not_collected_treasures_loc) == 0

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
