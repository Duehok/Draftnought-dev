"""docstring"""
from window.framework import Observable, Command
from math import atan2, sin, cos, pi, sqrt

# superstructures and funnels have different coordinates system
# I decide to use the funnel
# might be a bad idea
STRUCTURE_TO_FUNNEL = 1.0/45.0

# To convert the angle's value in superstructure's points to radiants
ANGLE_TO_RADS = pi/972000000.0


class Funnel(Observable):
    """Container for the data needed to draw a funnel

    Contrary to the other ship parts, not generated from the file's data but from passed parameters
    Args:
        oval=False: round or oval funnel
        TODO
        position=0: funnel position on the vertical axis. 0 is the center of the ship.
    Attrs:
        oval: if the funnel should be displayed as an oval, or not
        TODO
        position: Position of the funnel along the length of the ship, in funnel coordinates
    """

    def __init__(self, oval=False, x_coord=0, y_coord=0):
        super().__init__()
        self._oval = oval
        self._x = x_coord
        self._y = y_coord

    @property
    def oval(self):
        """if the funnel should be displayed as an oval, or not"""
        return self._oval

    @oval.setter
    def oval(self, value):
        if value != self._oval:
            self._oval = value
            self._notify("set_oval", {"oval": value})

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        if value != self._x:
            self._x = value
            self._notify("set_position", {"position": [self._x, self._y]})

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        if value != self._y:
            self._y = value
            self._notify("set_position", {"position": [self._x, self._y]})


class MoveFunnel(Command):
    """Moves a funnel to a given position

    Args:
    TODO
        funnel: funnel that moves
        position: new position in funnel coordinates
    """

    def __init__(self, funnel, x=0, y=0):
        super().__init__()
        self._funnel = funnel
        self._x = x
        self._y = y
        self._old_x = funnel.x
        self._old_y = funnel.y

    def execute(self):
        """Moves the funnel"""
        if self._x != self._funnel.x or self._y != self._funnel.y:
            self._funnel.x = self._x
            self._funnel.y = self._y

    def undo(self):
        """Back to previous position
        """
        if self._old_x != self._funnel.x or self._old_y != self._funnel.y:
            self._funnel.x = self._old_x
            self._funnel.y = self._old_y


class OvalFunnel(Command):
    """Change the funnel from oval to circular and the opposite

    Args:
        funnel (Funnel): the funnel to be changed
        oval (bool): true if oval
    """

    def __init__(self, funnel, oval):
        super().__init__()
        self._funnel = funnel
        self._oval = oval
        self._old_oval = funnel.oval

    def execute(self):
        """Change the funnel's status"""
        if self._oval != self._funnel.oval:
            self._funnel.oval = self._oval

    def undo(self):
        """Back to original state"""
        if self._old_oval != self._funnel.oval:
            self._funnel.oval = self._old_oval


def funnels_as_ini_section(funnels, is_rtw2):
    """from a list of funnels, gives back a dict that can be exported to a
    file that RTW can understand
    """
    section_content = {}
    if (is_rtw2):
        for name, funnel in funnels.items():
            section_content[name+"Oval"] = 1 if funnel.oval else 0
        for name, funnel in funnels.items():
            if funnel.oval:
                section_content[name+"Oval"] = 1

    else:
        for name, funnel in funnels.items():
            section_content[name + "Pos"] = round(funnel.position)
        for name, funnel in funnels.items():
            if funnel.oval:
                section_content[name+"Oval"] = 1
            else:
                section_content[name+"Oval"] = 0
    return section_content


def parse_funnels(funnels_section, is_rtw2):
    """helper function to read the funnels data

    Args:
        funnels_section (dict): about the funnels straight from the parsed file
    returns:
        dict {"funnelname": Funnel}
    """
    funnels = {}

    funnels_indexes = {int(''.join(filter(str.isdigit, k)))
                       for k in funnels_section.keys()}
    if(is_rtw2):
        for i in funnels_indexes:
            funnel_name = f'Funnel{i}'
            is_oval = funnels_section.getboolean(f'Funnel{i}Oval')

            angle = funnels_section.getint(f'Funnel{i}Angle')
            distance = funnels_section.getint(f'Funnel{i}Distance')
            x = round(-distance*sin(angle*ANGLE_TO_RADS)*STRUCTURE_TO_FUNNEL)
            y = round(-distance*cos(angle*ANGLE_TO_RADS)*STRUCTURE_TO_FUNNEL)
            funnels[funnel_name] = Funnel(oval=is_oval, x_coord=x, y_coord=y)

    else:
        for i in funnels_indexes:
            funnel_name = f'Funnel{i}'
            is_oval = funnels_section.getboolean(f'Funnel{i}Oval')
            y_coord = funnels_section.getint(f'Funnel{i}Pos')
            funnels[funnel_name] = Funnel(oval=is_oval, y_coord=y_coord)

    return funnels
