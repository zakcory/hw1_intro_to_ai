import itertools
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

        for k, v in initial.items():
            if k == "map":
                self.map = v
            elif k == "pirate_ships":
                self.pirate_ships_names = set(v.keys())

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
        """ Returns all the actions that can be executed in the given state.
         The result should be a tuple (or other iterable) of actions as defined in the problem description file
            Examples of a Valid Action:
                If you have one ship: ((“wait”, “pirate_1”), )
                If you have 2 ships: ((“wait”, “pirate_1”),(“move”, “pirate_2”, (1, 2)))
            Must return a tuple
        """
        all_ships_actions_list = list()
        for ship_name, ship_loc in state.pirate_ships_loc_dict.items():
            ship_actions = []
            for action_command in self.all_actions_names: # check each command
                # each command type require different code
                if action_command == "collect_treasure":
                    # first check if ship can collect more treasures :
                    ship_treasure_num = len(state.treasures_on_ships_dict.get(ship_name))
                    if ship_treasure_num < 2 :
                        # then check if there is a nearby uncollected treasure and add action as much as there is:
                        for treasure,treasure_loc in state.uncollected_island_loc_dict.items():
                            if ((ship_loc[0]-1) <= treasure_loc[0] ) and ((ship_loc[1]-1) <= treasure_loc[1]
                                ) and ( treasure_loc[0] <= (ship_loc[0]+1)) and (treasure_loc[1]<=(ship_loc[1]+1)):
                                ship_actions.append(("collect_treasure", ship_name, treasure)) # add action

                elif action_command == "deposit_treasures":
                    # Check if the ship is at the base (deposit available)
                    if self.base_loc == ship_loc:
                        ship_treasures = state.treasures_on_ships_dict.get(ship_name)
                        if len(ship_treasures)>0:  # if there is this treasure on ship then deposit it
                            ship_actions.append(("deposit_treasures", ship_name)) # add action

                elif action_command == "sail":
                    all_sail_locations = self.sail_locations(ship_loc,ship_name)
                    ship_actions.extend(all_sail_locations) # add list of actions

                elif action_command == "wait":
                    ship_actions.append( ("wait", ship_name) ) # add action
            all_ships_actions_list.append(ship_actions)

        actions = tuple(itertools.product(*all_ships_actions_list))
        return actions

    def confiscate_treasure(self, treasures_on_ships_dict, uncollected_islands_loc_dict, ship_name):
        """ confiscate the treasure of ship and return it to uncollected islands"""
        treasure_in_ship = treasures_on_ships_dict.get(ship_name)
        # remove treasures from ship
        treasures_on_ships_dict.update({ship_name: set()})
        # return treasures to uncollected islands
        new_uncollected_islands = uncollected_islands_loc_dict.copy()
        for treasure in treasure_in_ship:
            treasure_loc = self.treasures_loc.get(treasure)
            new_uncollected_islands.update({treasure:treasure_loc})

        return treasures_on_ships_dict, new_uncollected_islands

    def result(self, state, action):
        """Return the state that results from executing the given
        action in the given state. The action must be one of
        self.actions(state)."""

        # if state.turn_num == 6 : # breakpoint for check purpose
        #     breakPoint = False

        new_turn = state.turn_num + 1

        new_marine_location_dict = state.marine_ships_loc_dict.copy() # will be updated to new marine loc at end turn
        marines_location_at_turn_end_set = set() # set of just the location of marines at turn end
        for marine_ship in state.marine_ships_loc_dict.keys(): # check marine encounter at end turn
            new_marine_ship_location = self.marine_ship_loc_at_t(marine_ship, new_turn)  # marine loc at end turn
            new_marine_location_dict.update({marine_ship: new_marine_ship_location})  # update marine loc
            marines_location_at_turn_end_set.add(new_marine_ship_location)

        new_pirate_ships_loc_dict = state.pirate_ships_loc_dict.copy()
        new_collected_treasures_in_base_names_set = state.collected_treasures_in_base_names_set.copy()
        new_uncollected_islands_loc_dict = state.uncollected_island_loc_dict.copy()
        new_treasures_on_ships_dict = state.treasures_on_ships_dict.copy()
        num_deposited = 0

        for single_action_syntax in action:
            action_ship_name = single_action_syntax[1] # the ship doing the action
            action_command  = single_action_syntax[0] # the action command
            pirate_ship_curr_location = state.pirate_ships_loc_dict.get(action_ship_name)
            # now check the which one is the action_command and return new state according
            if action_command == "collect_treasure": # (“collect_treasure”, pirate_ship, “treasure_name”).
                # if there is no marine encounter at the end of turn then we can collect it without confiscating
                if pirate_ship_curr_location not in marines_location_at_turn_end_set:
                    treasure_name = single_action_syntax[2]
                    ship_treasure_set = new_treasures_on_ships_dict.get(action_ship_name).copy() # list of ship's treasures
                    ship_treasure_set.add(treasure_name) # add treasure to the list
                    new_treasures_on_ships_dict.update({action_ship_name : ship_treasure_set }) # update ship's new list
                    # remove treasure from uncollected islands
                    new_uncollected_islands_loc_dict.pop(treasure_name, self.treasures_loc.get(treasure_name))

            # remember to confiscate treasures ship is still sailed to
            # if action_command is "sail" then update ship's loc and check encounter in new loc
            if action_command == "sail": # action = (“sail”, pirate_ship, (x, y))
                new_pirate_loc = single_action_syntax[2]
                new_pirate_ships_loc_dict.update({action_ship_name: new_pirate_loc})

            # TODO : check Question: can marine be at base? include case anyway
            if action_command == "deposit_treasures":  # action = (“deposit_treasures”, “pirate_ship”)
                # check if ship in base_loc
                base_loc = self.base_loc
                if (base_loc not in marines_location_at_turn_end_set) and (
                        new_pirate_ships_loc_dict.get(action_ship_name) == base_loc) :
                    ships_treasure_list = new_treasures_on_ships_dict.get(action_ship_name).copy()
                    for treasure_to_deposit in ships_treasure_list:
                        num_deposited += 1
                        # add all treasures in ship to collected_in_base
                        new_collected_treasures_in_base_names_set.add(treasure_to_deposit)

                    # remove the deposited treasure
                    new_treasures_on_ships_dict.update({action_ship_name : set() })
                    # no need to reduce num_not_deposited_treasures because we will return len(new_collected..._set)

            if new_pirate_ships_loc_dict.get(action_ship_name) in marines_location_at_turn_end_set:
                # remark confiscated treasures as uncollected and confiscate all treasures in ship encountered marine
                (new_treasures_on_ships_dict,
                 new_uncollected_islands_loc_dict) = self.confiscate_treasure(new_treasures_on_ships_dict,
                                                                              new_uncollected_islands_loc_dict,
                                                                              action_ship_name)
        # command wait doesn't change any of the other states.
        new_state = State(new_pirate_ships_loc_dict, new_treasures_on_ships_dict,
                          new_uncollected_islands_loc_dict,
                          new_collected_treasures_in_base_names_set,
                          new_marine_location_dict, state.num_not_deposited_treasures - num_deposited
                          , new_turn)

        return new_state


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
# print the names of all ships
# print the names of all treasures

    def h_2(self, node): # I almost finished this function, still doesnt work
        """ This is the heuristic. It gets a node (not a state, state can be accessed via node.state)
        Returns a Sum of the distances from the pirate base to the closest sea cell adjacent to a treasure -
         for each treasure, divided by the number of pirates. If there is a treasure which all the adjacent cells are
         islands – return infinity. """

        def distance(loc1, loc2):
            """Returns the Manhattan distance between two locations"""
            return abs(loc1[0] - loc2[0]) + abs(loc1[1] - loc2[1])

        def surrounded_by_islands(treasure_loc): # TODO - there is similar check in A* - we should delete it later
            """Returns True if the treasure is surrounded by islands, False otherwise"""
            row = treasure_loc[0]
            col = treasure_loc[1]
            for (i, j) in [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]:
                if self.legal_move((i, j)) and self.map[i][j] in ['S',"B"]:
                    return False
            return True

        state = node.state
        # Merge the uncollected treasures and the treasures on the ships (treasures that are not on the base)
        islands_treasures = list(state.uncollected_island_loc_dict.values())
        ships_treasures = [loc for loc in (treasure for treasure in state.treasures_on_ships_dict.values() if len(treasure) > 0)]
        treasures_not_on_base = islands_treasures + ships_treasures
        print(treasures_not_on_base)
        sum = 0
        # If a treasure is at base, it doesn't have an affect on the sum
        for treasure_loc in treasures_not_on_base:

            if surrounded_by_islands(treasure_loc):
                return math.inf
            else:
                min_distance = math.inf
                for (i, j) in [(treasure_loc[0] - 1, treasure_loc[1]), (treasure_loc[0] + 1, treasure_loc[1]),
                               (treasure_loc[0], treasure_loc[1] - 1), (treasure_loc[0], treasure_loc[1] + 1)]:
                    # Finding the sea cell that's closest to the base
                    if self.legal_move((i, j)) and self.map[i][j] == 'S':
                        min_distance = min(min_distance, distance(self.base_loc, (i, j)))
                sum += min_distance

        return sum / (len(treasures_not_on_base) + len(state.collected_treasures_in_base_names_set))

    """Feel free to add your own functions
    (-2, -2, None) means there was a timeout"""

    def get_map(self):
        return self.map
    def get_pirate_ships_names(self):
        return self.pirate_ships_names
    def get_treasures_loc(self):
        return self.treasures_loc

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
# check if in the end of turn there will be a marine in ship's location to confiscate the treasure.
# the actions are atomic