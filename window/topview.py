"""Everything that has to do with the view from top of the ship.

   Includes the main TopView canvas and all the commands that are started from there.
"""
import tkinter as tk
from window.sideview import make_grid
from window.framework import Observable

_HFUNNELS_TO_HLENGTH = 0.028
_FUNNEL_OVAL = 1.38
_WIDTH = 701
_HEIGHT = 261


class TopView(tk.Canvas, Observable):
    """Everything having to do with the area displaying the top view of the ship

    The ship is displayed with bow at the left
    the ship is scaled to fit the length of the canvas

    Args:
        parent (tk.Frame): the parent of the canvas
        ship_data (shipdata.ShipData):
        struct_editors (list): all superstructure editors
            that can impact the drawings of the superstructures
        funnel_editors (list): as the struct editors but for funnels
        command_stack (ComandStack): the undo/redo command stack common to the whole program
        parameters (parameters_loader.Parameters): set of data to draw the ship.
    """

    def __init__(self, parent,
                 ship_data,
                 struct_editors,
                 funnel_editors,
                 command_stack,
                 parameters):
        tk.Canvas.__init__(self, parent,
                           width=_WIDTH,
                           height=_HEIGHT,
                           borderwidth=2,
                           relief="ridge", cursor="crosshair",
                           xscrollincrement=1,
                           yscrollincrement=1)
        Observable.__init__(self)

        self._parameters = parameters
        self.command_stack = command_stack
        self._half_length = ship_data.half_length

        self.xview(tk.SCROLL, round(parameters.topview_offset[0]), tk.UNITS)
        self.yview(tk.SCROLL, round(parameters.topview_offset[1]), tk.UNITS)

        self._funnel_to_canvas, self._canvas_to_funnel = self.make_converters(
            ship_data.half_length)

        self._display_hull(
            parameters.hulls_shapes[ship_data.ship_type], self._half_length)
        self._drawings_ids = []
        self._active_editor = None

        self._struct_editors = struct_editors
        for struct_editor in struct_editors:
            struct_editor.subscribe(self._on_notification)

        self._funnel_half_width = ship_data.half_length*_HFUNNELS_TO_HLENGTH
        self._funnel_editors = funnel_editors
        for funnel_editor in funnel_editors:
            funnel_editor.subscribe(self._on_notification)

        self._turrets = ship_data.turrets_torps

        self._grid = make_grid(self.winfo_reqwidth(),
                               self.winfo_reqheight(), horizontal=True)
        self._grid_on = False

        self.redraw()

        self._dragging = False
        self.bind("<Motion>", self._on_mouse_move)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<Enter>", self._on_mouse_move)
        self.bind("<Leave>", self._on_mouse_move)
        self.bind("<ButtonPress-1>", self._on_click)
        self.bind("<ButtonRelease-1>", self._on_left_release)
        self.bind("<MouseWheel>", self._on_mousewheel)

    def make_converters(self, half_length):
        """give converters from funnel to canvas coordinates and vice-versa

        scaled so that the full length of the ship fits exactly the width of the canvas
        Args:
            half_length (number): the half-length of the ship.
                The converters are set up so that if fits neatly in the canvas

        Returns:
            a tupple of two converter functions:
                funnel to canvas
                canvas ti funnel
        """
        coord_factor = (self.winfo_reqwidth()/2.1) / \
            half_length*self._parameters.topview_zoom
        xoffset = self.winfo_reqwidth()/2.0
        yoffset = self.winfo_reqheight()/2.0

        def funnel_to_canvas(point):
            """convert from funnel to canvas coordinates

            Args:
                point (number, number): point in funnel coordinates

            Returns:
                (int, int) in canvas coordinates
            """
            if not point:
                return []
            return (point[1]*coord_factor + xoffset, -point[0]*coord_factor + yoffset)

        def canvas_to_funnel(point):
            """convert from canvas to funnel coordinates

            Args:
                point (number, number): point in canvas coordinates

            Returns:
                (int, int) in funnel coordinates
            """
            if not point:
                return []
            return (-(point[1] - yoffset)/coord_factor, (point[0] - xoffset)/coord_factor)

        return (funnel_to_canvas, canvas_to_funnel)

    def _display_hull(self, hull_shape, half_length):
        """draw the hull outlines according to the ship type and half length

        Args:
            huls_shape (dict): list of list of (x,y) tuples
                that define the lines that make the hull's outline
                in relative coordinates
            half_length: the half-length of the ship to go from relative to funnel coordinates
        """
        for line in hull_shape:
            converted_points = [self._funnel_to_canvas(
                (point[0]*half_length,
                 point[1]*half_length))
                for point in line]
            self.create_line(*converted_points, smooth=True, width=2)

    def _draw_structure(self, points, fill, selected_index=-1, mouse_xy=(-1, -1)):
        """Draw one structure on the canvas

        If the structure is active, draws the potential new outline to the cursor position
        Args:
            points list of (x, y): all the points of the superstructure in funel coordinates
            fill bool: draw as a filled polygon or just a line
            selected_index int: if a point of the structure has been selected by the user,
                this is the index of the point in the points list
                -1 means "none selected"
            mouse_xy (x, y): position of the mouse in the canvas local coordinates.
                (-1, -1) means "do not care"
                If there is a mouse position and a selected index,
                the potential new outline to the pointer is drawn.
        """
        if selected_index != -1:
            color = "orange"
        else:
            color = "black"
        drawing_ids = []
        if len(points) >= 2:
            converted_points = [self._funnel_to_canvas(
                point) for point in points]
            if fill:
                drawing_ids.append(self.create_polygon(*converted_points,
                                                       fill="cyan", outline=color, width=2))
            else:
                drawing_ids.append(self.create_line(
                    *converted_points, fill=color, width=2))

        if mouse_xy != (-1, -1) and selected_index != -1:
            mouse_drawing_verteces = []
            if selected_index - 1 >= 0 and points:
                mouse_drawing_verteces.append(
                    self._funnel_to_canvas(points[selected_index - 1]))
            mouse_drawing_verteces.append(mouse_xy)
            if selected_index + 1 <= len(points) - 1:
                mouse_drawing_verteces.append(
                    self._funnel_to_canvas(points[selected_index + 1]))

            if len(mouse_drawing_verteces) >= 2:
                drawing_ids.append(self.create_line(
                    *mouse_drawing_verteces, fill="red", width=2))
        return drawing_ids

    def _draw_funnel(self, x, y, oval, mouse_x=-1, mouse_y=-1):
        """Draw one funnel on the canvas

        If the funnel is active, draws the potential new outline to the cursor position
        Args:
            position int:the funnel's coordinate in funnel system along the Y (length) axis
            oval bool: draw as an oval or a disk
            mouse_x int: position of the mouse in the canvas' coordinates' x axis (length of ship).
                -1 means "do not care"
                If there is a mouse position and a selected index,
                the potential new funnel is drawn
        """
        drawing_ids = []
        delta = self._funnel_half_width
        if oval:
            delta = delta*_FUNNEL_OVAL
        if x != 0 or y != 0:
            vertex1_canvas = self._funnel_to_canvas(
                (x-self._funnel_half_width, y-delta))
            vertex2_canvas = self._funnel_to_canvas(
                (x+self._funnel_half_width, y+delta))
            drawing_ids.append(self.create_oval(
                *vertex1_canvas, *vertex2_canvas, fill="black"))

        if mouse_x != -1 and mouse_y != -1:
            (mouse_funnel_x, mouse_funnel_y) = self._canvas_to_funnel(
                (mouse_x, mouse_y))
            vertex1_canvas = self._funnel_to_canvas(
                (mouse_funnel_x-self._funnel_half_width, mouse_funnel_y-delta))
            vertex2_canvas = self._funnel_to_canvas(
                (mouse_funnel_x+self._funnel_half_width, mouse_funnel_y+delta))
            drawing_ids.append(self.create_oval(*vertex1_canvas, *vertex2_canvas,
                                                fill="red", stipple="gray25"))
        return drawing_ids

    def _draw_turret(self, turret):
        canvas_outline = [self._funnel_to_canvas(
            point) for point in turret.outline]
        return [self.create_polygon(*canvas_outline, fill="green", outline="black")]

    def redraw(self, active_editor=None):
        """Redraw all the canvas elements, except the hul outline

        Args:
            active_editor: the struct or funnel editor that is currently active.
                this editor will get the mouse clicks to modify the funnel or structure.
        """

        mouse_x = self.winfo_pointerx() - self.winfo_rootx() + self.canvasx(0)
        mouse_y = self.winfo_pointery() - self.winfo_rooty() + self.canvasy(0)
        if (mouse_x >= 0 and mouse_y >= 0
                and mouse_x <= self.winfo_width() - 1 and mouse_y <= self.winfo_height() - 1):
            mouse_rel_pos = (mouse_x, mouse_y)
        else:
            mouse_rel_pos = (-1, -1)

        for drawing_id in self._drawings_ids:
            self.delete(drawing_id)
        self._drawings_ids = []

        for editor in self._struct_editors:
            if editor == active_editor:
                self._drawings_ids = (self._drawings_ids
                                      + self._draw_structure(editor.points,
                                                             editor.fill,
                                                             selected_index=editor.selected_index,
                                                             mouse_xy=mouse_rel_pos))
            else:
                self._drawings_ids = (self._drawings_ids
                                      + self._draw_structure(editor.points, editor.fill))

        for editor in self._funnel_editors:
            if editor == active_editor:
                self._drawings_ids = (self._drawings_ids
                                      + self._draw_funnel(editor.x, editor.y,
                                                          editor.oval,
                                                          mouse_rel_pos[0],
                                                          mouse_rel_pos[1]))
            else:
                if editor.y != 0:
                    self._drawings_ids = (self._drawings_ids
                                          + self._draw_funnel(editor.x, editor.y, editor.oval))

        for turret in self._turrets:
            self._drawings_ids = self._drawings_ids + self._draw_turret(turret)

        self.refresh_grid()

    def refresh_grid(self):
        """Update the grid according to grid_on
        Resize the grid if the previous grid was too small
        No resize if the grid is too big!
        """
        if self._grid_on:
            if (self._grid.height() < self.winfo_height() or
                    self._grid.width() < self.winfo_width()):
                self._grid = make_grid(
                    self.winfo_width(), self.winfo_height(), horizontal=True)
            self._drawings_ids.append(self.create_image((self.canvasx(0),
                                                         self.canvasy(0)),
                                                        image=self._grid, anchor=tk.NW))

    def _on_drag(self, event):
        self._dragging = True
        self.scan_dragto(event.x, event.y, gain=1)
        new_offset = (self.canvasx(0), self.canvasy(0))
        x_move = new_offset[0] - self._parameters.topview_offset[0]
        self._parameters.topview_offset = new_offset
        self._notify("Drag", {"x": x_move})

    def _on_mouse_move(self, _event):
        if not self._dragging:
            self.redraw(self._active_editor)

    def _on_mousewheel(self, event):
        """Mouse wheel changes the zoom"""
        if event.delta > 0:
            factor = 1.05
        else:
            factor = 0.95
        self.scale("all", self.winfo_reqwidth()/2.0,
                   self.winfo_reqheight()/2.0, factor, factor)
        self._parameters.topview_zoom = self._parameters.topview_zoom*factor
        self._notify("Apply_zoom", {"factor": factor})
        self._funnel_to_canvas, self._canvas_to_funnel = self.make_converters(
            self._half_length)

    def _on_notification(self, observable, _event_type, _event_info):
        """Notifications comming from funnel and structure editors"""
        self._active_editor = observable
        self.redraw(observable)

    def _on_click(self, event):
        self.scan_mark(event.x, event.y)

    def _on_left_release(self, event):
        """Send to the active editor the coordinates of a mouse click, in funnel coordinates"""
        if self._dragging:
            self._dragging = False
            return
        if self._active_editor is not None:
            self._active_editor.update_to_coord(self._canvas_to_funnel((event.x + self.canvasx(0),
                                                                        event.y + self.canvasy(0))))

    def switch_grid(self, grid_on):
        """Add or remove the grid according to the state of grid_on"""
        self._grid_on = grid_on
        self.redraw()
