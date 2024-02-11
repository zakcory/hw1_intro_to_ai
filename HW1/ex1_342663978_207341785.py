from collections import namedtuple
import search
import random
import math
from itertools import product

ids = ["342663978", "207341785"]

State_tuple = namedtuple('State_tuple', ['pirate_ships_loc_dict', 'treasures_on_ships_dict',
                             'uncollected_treasures_loc_dict', 'collected_treasures_in_base_names_set',
                                         'marine_ships_loc_dict'])

def test(ships): # TODO : what is this for?
    all_actions = []
    for ship in ships:
        for k, v in ship.items():
            name = k
            loc = v
            print("ship name: ", name,", loc: ", (v[0] - 1, v[1]))

def find_key_by_value(dictionary, value):
    """ Find key in the dictionary by its specific value and return it if exists else return None """
    for key, val in dictionary.items():
        if val == value:
            return key
    return None

class State(State_tuple):  # state must be hashable - so we need to make it hashable
    def __hash__(self):  # TODO : check if implementation is good - the teacher said we can use str as hash
        String_state = str(self)
        return hash(String_state)





class OnePieceProblem(search.Problem):
    """This class implements a medical problem according to problem description file

        contain attributes: self.map, self.pirate_ships_names, self.treasures_loc, self.marine_ships_input_route,
         self.marine_route_cycle, self.base_loc, self.all_actions_names

        contain methods: marine_ship_loc_at_t,  actions(self, state: namedtuple), result(self, state, action),
        goal_test(self, state), h, h1, h2
    """

    def __init__(self, initial):
        """Don't forget to implement the goal test
        You should change the initial to your own representation.
        search.Problem.__init__(self, initial) creates the root node"""

        # Adding all the parameters to the list to then pass on the list to the constructor
        self.all_actions_names = ["collect_treasure", "deposit_treasures", "sail", "wait"]

        init_state_params = []
        self.map = None
        for k, v in initial.items():
            if k == "map":
                self.map = v
            elif k == "pirate_ships":
                self.pirate_ships_names = list(v.keys())
                init_state_params.append(v)  # 'pirate_ships_loc_dict'

                treasures_on_ships_dict = {}
                for ship_name in self.pirate_ships_names:
                    treasures_on_ships_dict.update({ship_name: list([])})
                init_state_params.append(treasures_on_ships_dict)  # 'treasures_on_ships_dict'- dict{ ship_name :
                #                                                   list of treasures_names (at most two treasures) ...}

            elif k == "treasures":
                self.treasures_loc = v
                init_state_params.append(v)  # uncollected_treasures_loc_dict
                init_state_params.append(set())  # 'collected_treasures_in_base_names_set'

            elif k == "marine_ships":
                self.marine_ships_input_route = v  # TODO not sure if we need this variable - maybe delete it later

                init_loc = dict()
                self.marine_route_cycle = dict()  # will use this to keep track of the marine locations at time t
                for key, value in v.items():
                    route = list(value)
                    route = route + route[len(route)-2:0:-1]
                    self.marine_route_cycle.update({key: route})
                    init_loc.update({key: route[0]})

                init_state_params.append(init_loc)  # 'marine_ships_loc_dict'

        self.base_loc = list(initial['pirate_ships'].values())[0]

        initial_state = State(*init_state_params)
        search.Problem.__init__(self, initial_state)

    def marine_ship_loc_at_t(self, marine_ship_name: str, timestamp: int):
        """ Returns the location of the marine_ship_name at given timestamp"""
        cycle_route = list(self.marine_route_cycle.get(marine_ship_name))
        return cycle_route[timestamp % len(cycle_route)]

    def legal_move(self, location):
        """
            Indicates if a given location is within the map.

            Parameters:
            location (tuple of integers): a tuple of two integers that defines the location on the map

            Returns:
            boolean: if the location is within the map, returns True. Returns False otherwise
        """
        rows_num = len(self.map)
        cols_num = len(self.map[0])
        return (0 <= location[0] < rows_num) and (0 <= location[1] < cols_num)

    def sail_locations(self, loc, ship_name) : # TODO - make sue check in node if cell contain marine in next timestamp
        """ Returns legal tuple (as described in file)
        of all the near sail actions to locations within the map that this ship can sail to."""
        locations_array = []
        for i in range(loc[0]-1, loc[0]+2):
            for j in range(loc[1]-1, loc[1]+2):
                if (i, j)!= (loc[0],loc[1]) and self.legal_move([i,j]):
                    if self.map[i][j] in ["B","S"]: # we can sail to just B-base and S-sea
                        locations_array.append( ("sail", ship_name, (i,j) ) )
        return locations_array


    def actions(self, state: namedtuple):
        """Returns all the actions that can be executed in the given state.
         The result should be a tuple (or other iterable) of actions as defined in the problem description file
            Examples of a Valid Action:
                If you have one ship: ((“wait”, “pirate_1”), )
                If you have 2 ships: ((“wait”, “pirate_1”),(“move”, “pirate_2”, (1, 2)))
            Must return a tuple
        """
        actions = []

        for action_command in self.all_actions_names: # check each command

            for ship_name, ship_loc in state.pirate_ships_loc_dict.items():

                if action_command == "collect_treasure":
                    # first check if ship can collect more treasures :
                    ship_treasure_num = len(state.treasures_on_ships_dict.get(ship_name))
                    if ship_treasure_num < 2 :
                        # then check if there is a nearby uncollected treasure and add action as much as there is:
                        for treasure,treasure_loc in state.uncollected_treasures_loc_dict.items():
                            if ((ship_loc[0]-1) <= treasure_loc[0] ) and ((ship_loc[1]-1) <= treasure_loc[1]
                                ) and ( treasure_loc[0] <= (ship_loc[0]+1)) and (treasure_loc[1]<=(ship_loc[1]+1)):
                                actions.append(("collect_treasure", ship_name, treasure)) # add action

                elif action_command == "deposit_treasures":
                    # Check if the ship is at the base (deposit available)
                    if self.base_loc == ship_loc:
                        ship_treasures = state.treasures_on_ships_dict.get(ship_name)
                        there_is_treasure_on_ship = False
                        for treasure in ship_treasures:
                            if treasure is not None:
                                there_is_treasure_on_ship = True
                        if there_is_treasure_on_ship:  # if there is treasure on ship then deposit it
                            actions.append(("deposit_treasures", ship_name)) # add action

                elif action_command == "sail":
                    all_sail_locations = self.sail_locations(ship_loc,ship_name)
                    actions.extend(all_sail_locations) # add list of actions

                elif action_command == "wait":
                    actions.append( ("wait", ship_name) ) # add action

        return tuple(actions)

    def result(self, state, action): # TODO
        """Return the state that results from executing the given
        action in the given state. The action must be one of
        self.actions(state)."""
        if action in self.actions(state):
            pass

    def goal_test(self, state):
        """Given a state, checks if this is the goal state.
         Returns True if it is, False otherwise."""
        return len(state.uncollected_treasures_loc_dict) == 0

    def h(self, node):  # TODO
        """ This is the heuristic. It gets a node (not a state,
        state can be accessed via node.state)
        and returns a goal distance estimate"""
        return 0

    def h_1(self, node):
        """ This is the heuristic. It gets a node (not a state,
        state can be accessed via node.state)
        and returns a number of uncollected treasures divided by the number of pirates."""
        state = node.state
        uncollected_treasures_num = len(state.uncollected_treasures_loc_dict)
        pirates_num = len(state.pirate_ships_loc_dict)
        return uncollected_treasures_num/pirates_num

    def h_2(self, node): # TODO
        """ This is the heuristic. It gets a node (not a state,
        state can be accessed via node.state)
        Returns a Sum of the distances from the pirate base to the closest sea cell adjacent to a treasure -
         for each treasure, divided by the number of pirates. If there is a treasure which all the adjacent cells are
         islands – return infinity. """
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


# TODO notes:
# - sometimes we can move to a loc even if there is marine if we have no treasure on ships.
# - when collecting a treasure on ship make sure to remove it from uncollected, and if it was forfeited to marines don't
# forget to add it to uncollected again.
# - there is node.depth attribute in node which can be used as timestamp
