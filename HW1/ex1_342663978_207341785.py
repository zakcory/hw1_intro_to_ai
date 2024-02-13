from collections import namedtuple
import search
import random
import math
from itertools import product

ids = ["342663978", "207341785"]

State_tuple = namedtuple('State_tuple', ['pirate_ships_loc_dict', 'treasures_on_ships_dict',
                             'uncollected_island_loc_dict', 'collected_treasures_in_base_names_set',
                                         'marine_ships_loc_dict', "num_not_deposited_treasures", "turn_num"])

class State(State_tuple):  # state must be hashable - so we need to make it hashable
    def __eq__(self, other):
        if isinstance(other, State):
            # check if self.state == other.state
            if self.num_not_deposited_treasures != other.num_not_deposited_treasures: #6
                return False
            for k,v in self.pirate_ships_loc_dict.items(): # 1
                if other.pirate_ships_loc_dict.get(k) != v:
                    return False
            for k,v in self.treasures_on_ships_dict.items(): # 2
                other_v = other.treasures_on_ships_dict.get(k)
                if len(other_v) != len(v):
                    return False
                else:
                    for treasure in v:
                        if treasure not in other_v:
                            return False
            self_uncollected_islands_set = set(self.uncollected_island_loc_dict.keys())
            other_uncollected_islands_set = set(other.uncollected_island_loc_dict.keys())
            if len(self_uncollected_islands_set) != len(other_uncollected_islands_set): # 3
                return False
            else:
                for k in self_uncollected_islands_set:
                    if not (k in other_uncollected_islands_set):
                        return False
            if len(self.collected_treasures_in_base_names_set.copy().symmetric_difference(
                    other.collected_treasures_in_base_names_set) ) > 0:                                      #4
                return False
            for k,v in self.marine_ships_loc_dict.items(): #5
                other_v = other.marine_ships_loc_dict.get(k)
                if v != other_v:
                    return False
            return True
        else:
            return False

    def __hash__(self):  #
        String_state = str(self[0:6]) # do not include turn_num in hashing
        # print("in hash",self,"  ", hash(String_state))
        return hash(String_state)

def find_key_by_value(dictionary, value):
    """ Find key in the dictionary by its specific value and return it if exists else return None """
    for key, val in dictionary.items():
        if val == value:
            return key
    return None

class OnePieceProblem(search.Problem):
    """This class implements a medical problem according to problem description file

        contain attributes: self.map, self.pirate_ships_names, self.treasures_loc, self.marine_ships_input_route,
         self.marine_route_cycle, self.base_loc, self.all_actions_names.

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
        self.turn_timestamp = 0
        for k, v in initial.items():
            if k == "map":
                self.map = v
            elif k == "pirate_ships":
                self.pirate_ships_names = set(v.keys())
                # self.pirates_need_action_bool = {}
                self.pirates_need_action_bool = self.pirate_ships_names.copy()

                init_state_params.append(v)  # 'pirate_ships_loc_dict'

                treasures_on_ships_dict = {}
                for ship_name in self.pirate_ships_names:
                    treasures_on_ships_dict.update({ship_name: set()})
                init_state_params.append(treasures_on_ships_dict)  # 'treasures_on_ships_dict'- dict{ ship_name :
                #                                                   set of treasures_names (at most two treasures) ...}

            elif k == "treasures":
                self.treasures_loc = v
                init_state_params.append(v)  # uncollected_island_loc_dict
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

        init_state_params.append(len(init_state_params[2])) # num_not_deposited_treasures
        init_state_params.append(0) # turn_num
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

    def sail_locations(self, loc, ship_name, just_check_reachability = False) :
        """ Returns legal tuple (as described in file)
        of all the near sail actions to locations within the map that this ship can sail to."""
        locations_array = []
        row = loc[0]
        col = loc[1]
        for (i,j) in [(row-1,col), (row+1,col), (row,col-1), (row,col+1)]:
            if self.legal_move((i,j)):
                if self.map[i][j] in ["B","S"]: # we can sail to just B-base and S-sea
                    if just_check_reachability:
                        return True
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
                # each command type require different code
                if action_command == "collect_treasure":
                    # first check if ship can collect more treasures :
                    ship_treasure_num = len(state.treasures_on_ships_dict.get(ship_name))
                    if ship_treasure_num < 2 :
                        # then check if there is a nearby uncollected treasure and add action as much as there is:
                        for treasure,treasure_loc in state.uncollected_island_loc_dict.items():
                            if ((ship_loc[0]-1) <= treasure_loc[0] ) and ((ship_loc[1]-1) <= treasure_loc[1]
                                ) and ( treasure_loc[0] <= (ship_loc[0]+1)) and (treasure_loc[1]<=(ship_loc[1]+1)):
                                actions.append(("collect_treasure", ship_name, treasure)) # add action

                elif action_command == "deposit_treasures":
                    # Check if the ship is at the base (deposit available)
                    if self.base_loc == ship_loc:
                        ship_treasures = state.treasures_on_ships_dict.get(ship_name)
                        if len(ship_treasures)>0:  # if there is this treasure on ship then deposit it
                            actions.append(("deposit_treasures", ship_name)) # add action

                elif action_command == "sail":
                    all_sail_locations = self.sail_locations(ship_loc,ship_name)
                    actions.extend(all_sail_locations) # add list of actions

                elif action_command == "wait":
                    actions.append( ("wait", ship_name) ) # add action

        return set(actions)

    def result(self, state, action):
        """Return the state that results from executing the given
        action in the given state. The action must be one of
        self.actions(state)."""

        new_marine_location_dict = dict()
        if len(self.pirates_need_action_bool) == 0:
            self.turn_timestamp += 1
            self.pirates_need_action_bool = self.pirate_ships_names.copy() # now a new turn so we need to check again
            for marine_ship in state.marine_ships_loc_dict.keys():
                new_marine_location = self.marine_ship_loc_at_t(marine_ship, self.turn_timestamp)  # marine loc at this turn
                new_marine_location_dict.update({marine_ship: new_marine_location})  # update it

        action_ship_name = action[1] # the ship doing the action
        self.pirates_need_action_bool.discard(action_ship_name)
        new_turn = self.turn_timestamp# new turn number just after all ships did action

        legal_actions_set = self.actions(state) # all legal actions the current state can do

        if (not (legal_actions_set is None)) and (action in legal_actions_set):
            action_command  = action[0]

            # check if in the end of turn there will be a marine in ship's location to confiscate the treasure.
            ships_encountered_marine_list = []
            new_pirate_ships_loc_dict = state.pirate_ships_loc_dict.copy()
            new_treasures_on_ships_dict = state.treasures_on_ships_dict.copy()
            new_uncollected_islands_loc_dict = state.uncollected_island_loc_dict.copy()
            new_collected_treasures_in_base_names_set = state.collected_treasures_in_base_names_set.copy()

            for marine in state.marine_ships_loc_dict.keys():
                new_marine_location = self.marine_ship_loc_at_t(marine, new_turn+1) # loc of marine at end of turn
                for ship_name, ship_loc in state.pirate_ships_loc_dict.items(): # check if any ship encountered marine
                    # if action_command is "sail" then update ship's loc and check encounter in new loc
                    if ship_name==action_ship_name and action_command == "sail": # action = (“sail”, pirate_ship, (x, y))
                        new_loc = action[2]
                        # check new_loc if legal
                        if self.legal_move(new_loc) and self.map[new_loc[0]][new_loc[1]] in ["B", "S"]:
                            ship_loc = new_loc
                            new_pirate_ships_loc_dict.update({ship_name: ship_loc})

                    if new_marine_location == ship_loc:
                        ships_encountered_marine_list.append(ship_name)
                        # remark the confiscated treasures as uncollected:
                        for treasure in new_treasures_on_ships_dict.get(ship_name):
                            treasure_loc = self.treasures_loc.get(treasure)
                            new_uncollected_islands_loc_dict.update({treasure: treasure_loc})
                        # confiscate all treasures in ship encountered marine:
                        new_treasures_on_ships_dict.update({ship_name: set()})


            num_deposited = 0
            # now check the which one is the action_command and return new state according
            if action_command == "collect_treasure": # (“collect_treasure”, pirate_ship, “treasure_name”).
                # if there is no marine encounter at the end of turn then we can collect it without confiscating
                if not (action_ship_name in ships_encountered_marine_list):
                    ship_treasure_set = state.treasures_on_ships_dict.get(action_ship_name).copy() # list of ship's treasures
                    ship_treasure_set.add(action[2]) # add treasure to the list
                    new_treasures_on_ships_dict.update({action_ship_name : ship_treasure_set }) # update ship's new list
                    # remove treasure from uncollected islands
                    new_uncollected_islands_loc_dict.pop(action[2], new_uncollected_islands_loc_dict.get(action[2]))

            elif action_command == "deposit_treasures":  # action = (“deposit_treasures”, “pirate_ship”)
                # check if ship in base_loc
                if new_pirate_ships_loc_dict.get(action_ship_name) == self.base_loc:
                    ships_treasure_list = new_treasures_on_ships_dict.get(action_ship_name).copy()
                    for treasure_to_deposit in ships_treasure_list:
                        num_deposited += 1
                        # add all treasures in ship to collected_in_base
                        new_collected_treasures_in_base_names_set.add(treasure_to_deposit)

                    # remove the deposited treasure
                    new_treasures_on_ships_dict.update({action_ship_name : set() })
                    # no need to reduce num_not_deposited_treasures because we will return len(new_collected..._set)


            # command wait doesn't change any of the other states. command sail already checked
            new_state = State(new_pirate_ships_loc_dict, new_treasures_on_ships_dict,
                                      new_uncollected_islands_loc_dict,
                                      new_collected_treasures_in_base_names_set,
                                      new_marine_location_dict, state.num_not_deposited_treasures - num_deposited,
                         new_turn)
            return new_state
            # return State(new_pirate_ships_loc_dict, new_treasures_on_ships_dict,
            #                           new_uncollected_islands_loc_dict,
            #                           new_collected_treasures_in_base_names_set,
            #                           new_marine_location_dict, state.num_not_deposited_treasures - num_deposited,
            #              new_turn)
        else:
            return state

    def goal_test(self, state):
        """Given a state, checks if this is the goal state.
         Returns True if it is, False otherwise."""
        test_flag = state.num_not_deposited_treasures == 0
        return test_flag

    def h(self, node):  # TODO
        """ This is the heuristic. It gets a node (not a state,
        state can be accessed via node.state)
        and returns a goal distance estimate"""
        return self.h_1(node)

    def h_1(self, node):
        """ This is the heuristic. It gets a node (not a state,
        state can be accessed via node.state)
        and returns a number of uncollected treasures divided by the number of pirates."""
        state = node.state
        uncollected_treasures_num = len(state.uncollected_island_loc_dict)
        pirates_num = len(state.pirate_ships_loc_dict)
        # print(node.state,"h_1 ", uncollected_treasures_num/pirates_num)

        return uncollected_treasures_num/pirates_num

    def h_2(self, node): # TODO
        """ This is the heuristic. It gets a node (not a state, state can be accessed via node.state)
        Returns a Sum of the distances from the pirate base to the closest sea cell adjacent to a treasure -
         for each treasure, divided by the number of pirates. If there is a treasure which all the adjacent cells are
         islands – return infinity. """
        state = node.state

        pirates_num = len(state.pirate_ships_loc_dict)

        return 0

    """Feel free to add your own functions
    (-2, -2, None) means there was a timeout"""

    def get_map(self):
        return self.map
    def get_pirate_ships_names(self):
        return self.pirate_ships_names
    def get_treasures_loc(self):
        return self.treasures_loc
    def get_marine_ships_input_route(self):
        return self.marine_ships_input_route
    def get_marine_route_cycle(self):
        return self.marine_route_cycle
    def get_base_loc(self):
        return self.base_loc

def create_onepiece_problem(game):
    return OnePieceProblem(game)


def main():
    test = {
        'map': [['S', 'S', 'S', 'S', 'I'],
                ['S', 'I', 'S', 'S', 'S'],
                ['S', 'S', 'S', 'S', 'S'],
                ['B', 'S', 'S', 'I', 'S']],
        'pirate_ships': {'pirate_ship_1': (2, 0), 'pirate_ship_2': (3, 0)},
        'treasures': {'treasure_1': (1, 1), 'treasure_2': (3, 3)},
        'marine_ships': {'marine_1': [(3, 2), (2, 2), (2, 3), (2, 4)]}
    }
    pr = OnePieceProblem(test)
    print(pr.actions(pr.initial))



if __name__ == '__main__':
    main()


# TODO recheck notes:
# - sometimes we can move to a loc even if there is marine if we have no treasure on ships.
# - when collecting a treasure on ship make sure to remove it from uncollected, and if it was forfeited to marines don't
# forget to add it to uncollected again.
# - there is node.depth attribute in node which can be used as timestamp
# - make sure check in node if cell contain marine in next turn
# TODO : the actions are atomic - relate to just one ship