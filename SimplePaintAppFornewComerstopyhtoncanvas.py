import tkinter as tk
from tkinter import colorchooser # Imports the color chooser dialog

class PaintApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Paint App for Code in Place Final Project") # Sets the title of the application window
        self.root.geometry("1100x750") # Defines the initial size of the application window

        # Drawing configuration settings
        self.drawing_color = "black"  # Stores the currently selected drawing color
        self.brush_size = 3           # Stores the current brush thickness
        self.old_x = None             # Stores the previous X coordinate for continuous drawing
        self.old_y = None             # Stores the previous Y coordinate for continuous drawing
        # Defines the current drawing mode: 'draw', 'erase', 'rectangle', 'circle', or 'line'
        self.drawing_mode = "draw"    # Sets the default drawing mode to free draw

        # History management for Undo/Redo functionality
        self.history = []            # A list to store item IDs for each completed drawing stroke or shape
        self.history_idx = -1        # An index indicating the current position in the history list
        self.current_stroke_items = [] # A temporary list to collect item IDs during a single drawing stroke
        self.eraser_indicator_id = None # Stores the ID of the visual indicator for the eraser size
        self.temp_shape_id = None    # Stores the ID of the temporary shape drawn for preview during dragging
        self.shape_popup = None      # Stores a reference to the shape selection pop-up window

        # Main frame acts as a container for the canvas and control panel
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill="both", expand=True) # Makes the main frame fill the entire root window

        # Canvas widget: The primary drawing area
        self.canvas = tk.Canvas(self.main_frame, bg="white", bd=2, relief="groove")
        # Positions the canvas to the left within the main frame, allowing it to expand
        self.canvas.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        # Binds mouse events to the canvas for interactive drawing
        self.canvas.bind("<Button-1>", self.start_action)       # Triggers when the left mouse button is pressed
        self.canvas.bind("<B1-Motion>", self.perform_action)    # Triggers when the mouse is dragged with left button pressed
        self.canvas.bind("<ButtonRelease-1>", self.stop_action) # Triggers when the left mouse button is released
        self.canvas.bind("<Motion>", self.update_indicator) # Triggers on any mouse movement over the canvas

        # Control Frame: Contains all the tool buttons and sliders
        self.control_frame = tk.Frame(self.main_frame, bd=2, relief="ridge", padx=10, pady=10)
        # Positions the control frame to the right within the main frame, allowing vertical expansion
        self.control_frame.pack(side="right", fill="y", padx=10, pady=20)

        # Brush Size Slider: Allows users to adjust the drawing thickness
        tk.Label(self.control_frame, text="Brush Size:", font=("Arial", 10)).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.brush_size_slider = tk.Scale(self.control_frame, from_=1, to=15, orient="horizontal",
                                          command=self.change_brush_size, length=150, sliderrelief="raised")
        self.brush_size_slider.set(self.brush_size) # Sets the slider to the default brush size
        self.brush_size_slider.grid(row=1, column=0, padx=5, pady=5) # Positions the slider

        # Color Selection Button: Opens a color picker dialog
        self.color_button = tk.Button(self.control_frame, text="Select Color", command=self.choose_color,
                                       bg="black", fg="white", width=15, height=2, relief="raised")
        self.color_button.grid(row=2, column=0, padx=5, pady=10) # Positions the color button

        # Free Draw Tool Button: Activates freehand drawing mode
        self.draw_button = tk.Button(self.control_frame, text="Free Draw", command=self.set_draw_mode,
                                      bg="lightblue", width=15, height=2, relief="sunken") # Default active state
        self.draw_button.grid(row=3, column=0, padx=5, pady=5) # Positions the free draw button

        # Eraser Tool Button: Activates erase mode
        self.eraser_button = tk.Button(self.control_frame, text="Eraser", command=self.set_erase_mode,
                                        bg="lightgray", width=15, height=2, relief="raised")
        self.eraser_button.grid(row=4, column=0, padx=5, pady=5) # Positions the eraser button

        # Shapes Tool Button: Opens a popup for selecting specific shapes
        self.shape_tool_button = tk.Button(self.control_frame, text="Shapes", command=self.open_shape_selection_popup,
                                            bg="lightgray", width=15, height=2, relief="raised")
        self.shape_tool_button.grid(row=5, column=0, padx=5, pady=10) # Positions the shapes button

        # Undo Button: Reverts the last drawing action
        self.undo_button = tk.Button(self.control_frame, text="Undo", command=self.undo_action,
                                      width=15, height=2, relief="raised", state="disabled") # Disabled by default
        self.undo_button.grid(row=6, column=0, padx=5, pady=10) # Positions the undo button

        # Redo Button: Reapplies a previously undone drawing action
        self.redo_button = tk.Button(self.control_frame, text="Redo", command=self.redo_action,
                                      width=15, height=2, relief="raised", state="disabled") # Disabled by default
        self.redo_button.grid(row=7, column=0, padx=5, pady=5) # Positions the redo button

        # Clear Canvas Button: Removes all drawings from the canvas
        self.clear_button = tk.Button(self.control_frame, text="Clear Canvas", command=self.clear_canvas,
                                       bg="red", fg="white", width=15, height=2, relief="raised")
        self.clear_button.grid(row=8, column=0, padx=5, pady=10) # Positions the clear canvas button

        # Signature Label: Displays author information
        self.signature_label = tk.Label(self.control_frame, text="by Yusuf Mert Tuna", font=("Arial", 8, "italic"), fg="gray")
        self.signature_label.grid(row=9, column=0, padx=5, pady=(20, 5), sticky="s") # Positions the signature at the bottom

        self.update_undo_redo_buttons() # Initializes the states of the Undo/Redo buttons

    # Mouse Event Handlers: Functions that respond to specific mouse interactions on the canvas
    def start_action(self, event):
        """Records the starting coordinates of a drawing stroke or shape when the mouse button is pressed."""
        # If the user is in an 'undone' state and starts drawing, future undone actions are discarded
        if self.history_idx < len(self.history) - 1:
            # Deletes items that would be overwritten by new history
            for i in range(self.history_idx + 1, len(self.history)):
                for item_id in self.history[i]:
                    self.canvas.delete(item_id)
            self.history = self.history[:self.history_idx + 1]

        self.current_stroke_items = [] # Clears the list for items in the new stroke/shape
        self.old_x = event.x # Stores the starting X coordinate
        self.old_y = event.y # Stores the starting Y coordinate
        self.clear_indicator() # Hides any active eraser indicator

    def perform_action(self, event):
        """Draws continuously or previews shapes as the mouse is dragged."""
        if self.old_x is not None and self.old_y is not None: # Ensures a valid starting point exists
            # Clears any previous temporary shape preview
            if self.temp_shape_id:
                self.canvas.delete(self.temp_shape_id)
                self.temp_shape_id = None

            current_color = self.drawing_color
            # Handles free drawing or erasing logic
            if self.drawing_mode == "draw" or self.drawing_mode == "erase":
                if self.drawing_mode == "erase":
                    current_color = self.canvas["bg"] # Eraser draws with the canvas's background color

                # Creates a line segment from the previous point to the current mouse position
                item_id = self.canvas.create_line(self.old_x, self.old_y, event.x, event.y,
                                        width=self.brush_size,
                                        fill=current_color,
                                        capstyle=tk.ROUND,  # Renders line ends with a round cap
                                        smooth=tk.TRUE,     # Attempts to smooth out the drawn line
                                        splinesteps=12      # Defines the degree of smoothing
                                       )
                self.current_stroke_items.append(item_id) # Adds the created line segment ID to the current stroke list

                # Updates the 'old' coordinates to the current mouse position for the next segment
                self.old_x = event.x
                self.old_y = event.y
            
            # Handles shape preview logic for rectangles, circles, and lines
            elif self.drawing_mode == "rectangle":
                self.temp_shape_id = self.canvas.create_rectangle(self.old_x, self.old_y, event.x, event.y,
                                                                   outline=current_color, width=self.brush_size)
            elif self.drawing_mode == "circle":
                self.temp_shape_id = self.canvas.create_oval(self.old_x, self.old_y, event.x, event.y,
                                                              outline=current_color, width=self.brush_size)
            elif self.drawing_mode == "line":
                self.temp_shape_id = self.canvas.create_line(self.old_x, self.old_y, event.x, event.y,
                                                              fill=current_color, width=self.brush_size,
                                                              capstyle=tk.ROUND, smooth=tk.TRUE)

    def stop_action(self, event):
        """Finalizes the drawing stroke or shape when the mouse button is released."""
        # Finalizes the shape if currently in a shape drawing mode
        if self.temp_shape_id:
            self.canvas.delete(self.temp_shape_id) # Deletes the temporary preview shape
            self.temp_shape_id = None # Clears the reference to the temporary shape

            final_item_id = None
            # Creates the permanent shape based on the drawing mode
            if self.drawing_mode == "rectangle":
                final_item_id = self.canvas.create_rectangle(self.old_x, self.old_y, event.x, event.y,
                                                              outline=self.drawing_color, width=self.brush_size)
            elif self.drawing_mode == "circle":
                final_item_id = self.canvas.create_oval(self.old_x, self.old_y, event.x, event.y,
                                                         outline=self.drawing_color, width=self.brush_size)
            elif self.drawing_mode == "line":
                final_item_id = self.canvas.create_line(self.old_x, self.old_y, event.x, event.y,
                                                         fill=self.drawing_color, width=self.brush_size,
                                                         capstyle=tk.ROUND, smooth=tk.TRUE)
            
            if final_item_id:
                self.current_stroke_items.append(final_item_id) # Adds the final shape's ID to the current stroke

        if self.current_stroke_items: # Adds the completed stroke/shape to the history if items were drawn
            self.history.append(self.current_stroke_items)
            self.history_idx = len(self.history) - 1
        
        self.old_x = None # Resets the starting coordinates for the next action
        self.old_y = None
        self.update_undo_redo_buttons() # Updates the state of Undo/Redo buttons
        self.update_indicator(event) # Shows the eraser indicator if still in eraser mode

    def update_indicator(self, event):
        """Draws or updates a visual indicator (circle) for the eraser size on mouse motion."""
        # The indicator is only shown if the current mode is 'erase' and the mouse is over the canvas
        if self.drawing_mode == "erase" and \
           0 <= event.x <= self.canvas.winfo_width() and \
           0 <= event.y <= self.canvas.winfo_height():

            self.clear_indicator() # Removes any previously drawn indicator

            # Calculates coordinates for drawing a circle based on brush size
            x1 = event.x - self.brush_size
            y1 = event.y - self.brush_size
            x2 = event.x + self.brush_size
            y2 = event.y + self.brush_size
            # Creates the oval indicator and stores its ID
            self.eraser_indicator_id = self.canvas.create_oval(x1, y1, x2, y2,
                                                                outline="gray", width=1)
        else: # Hides the indicator if not in eraser mode or mouse leaves the canvas
            self.clear_indicator()

    def clear_indicator(self):
        """Removes the current eraser size indicator from the canvas."""
        if self.eraser_indicator_id:
            self.canvas.delete(self.eraser_indicator_id) # Deletes the oval object
            self.eraser_indicator_id = None # Clears the ID reference

    # Control Functions: Methods associated with buttons and sliders in the control panel
    def choose_color(self):
        """Opens a color selection dialog and updates the drawing color based on user's choice."""
        color_code = colorchooser.askcolor(title="Choose Color") # Opens the system color picker
        if color_code[1]: # Checks if a color was selected (not canceled)
            self.drawing_color = color_code[1] # Sets the new drawing color
            self.color_button.config(bg=self.drawing_color) # Updates the color button's background
            self.set_draw_mode() # Automatically switches to free draw mode

    def change_brush_size(self, size):
        """Updates the brush size based on the value from the brush size slider."""
        self.brush_size = int(size)

    def open_shape_selection_popup(self):
        """Creates and displays a small pop-up window for selecting shape tools."""
        # Destroys any existing popup to ensure only one is open at a time
        if self.shape_popup:
            self.shape_popup.destroy()
            self.shape_popup = None
            return # If clicked again, it closes the popup

        self.shape_popup = tk.Toplevel(self.root) # Creates a new top-level window
        self.shape_popup.title("Select Shape") # Sets the title of the popup
        self.shape_popup.transient(self.root) # Makes the popup transient to the main window
        self.shape_popup.grab_set() # Forces user interaction with the popup
        self.shape_popup.resizable(False, False) # Prevents resizing of the popup

        # Calculates the position for the popup to appear below the "Shapes" button
        btn_x = self.shape_tool_button.winfo_rootx()
        btn_y = self.shape_tool_button.winfo_rooty()
        btn_height = self.shape_tool_button.winfo_height()
        self.shape_popup.geometry(f"+{btn_x}+{btn_y + btn_height + 5}") # Positions the popup below the button

        # Creates and packs buttons for Rectangle, Circle/Oval, and Straight Line inside the popup
        tk.Button(self.shape_popup, text="Rectangle", command=lambda: self.set_rectangle_mode(self.shape_popup),
                  width=15, height=2).pack(pady=2, padx=5)
        tk.Button(self.shape_popup, text="Circle/Oval", command=lambda: self.set_oval_mode(self.shape_popup),
                  width=15, height=2).pack(pady=2, padx=5)
        tk.Button(self.shape_popup, text="Straight Line", command=lambda: self.set_line_mode(self.shape_popup),
                  width=15, height=2).pack(pady=2, padx=5)
        
        # Binds the close button of the popup to a custom close function
        self.shape_popup.protocol("WM_DELETE_WINDOW", self.close_shape_popup)

    def close_shape_popup(self):
        """Closes the shape selection pop-up window."""
        if self.shape_popup:
            self.shape_popup.grab_release() # Releases focus from the popup
            self.shape_popup.destroy() # Destroys the popup window
            self.shape_popup = None # Clears the reference

    def set_draw_mode(self):
        """Activates the free drawing mode and updates tool button states."""
        self.drawing_mode = "draw"
        self.update_tool_button_states(self.draw_button) # Sets the 'Free Draw' button as active
        self.clear_indicator() # Hides any eraser indicator
        self.close_shape_popup() # Closes the shape selection popup if open

    def set_erase_mode(self):
        """Activates the eraser mode and updates tool button states."""
        self.drawing_mode = "erase"
        self.update_tool_button_states(self.eraser_button) # Sets the 'Eraser' button as active
        self.close_shape_popup() # Closes the shape selection popup if open

    def set_rectangle_mode(self, popup_window=None):
        """Activates the rectangle drawing mode and updates tool button states."""
        self.drawing_mode = "rectangle"
        self.update_tool_button_states(self.shape_tool_button) # Sets the 'Shapes' button as active
        self.clear_indicator()
        if popup_window:
            popup_window.destroy() # Destroys the popup window that called this function
            self.shape_popup = None # Clears the reference to the popup

    def set_oval_mode(self, popup_window=None):
        """Activates the circle/oval drawing mode and updates tool button states."""
        self.drawing_mode = "circle"
        self.update_tool_button_states(self.shape_tool_button) # Sets the 'Shapes' button as active
        self.clear_indicator()
        if popup_window:
            popup_window.destroy() # Destroys the popup window that called this function
            self.shape_popup = None # Clears the reference to the popup

    def set_line_mode(self, popup_window=None):
        """Activates the straight line drawing mode and updates tool button states."""
        self.drawing_mode = "line"
        self.update_tool_button_states(self.shape_tool_button) # Sets the 'Shapes' button as active
        self.clear_indicator()
        if popup_window:
            popup_window.destroy() # Destroys the popup window that called this function
            self.shape_popup = None # Clears the reference to the popup

    def update_tool_button_states(self, active_button):
        """Helper function to visually update the state of all tool buttons (active/inactive)."""
        # Resets all main tool buttons to a normal (raised) state
        for button in [self.draw_button, self.eraser_button, self.shape_tool_button]:
            button.config(relief="raised", bg="lightgray")
        # Sets the currently active tool button to a sunken (pressed) state
        active_button.config(relief="sunken", bg="lightblue")

    def clear_canvas(self):
        """Deletes all drawn items from the canvas and resets the history."""
        self.canvas.delete("all") # Removes all drawing objects from the canvas
        self.history = [] # Clears the history list
        self.history_idx = -1 # Resets the history index
        self.update_undo_redo_buttons() # Updates the state of Undo/Redo buttons
        self.clear_indicator() # Hides any eraser indicator
        self.close_shape_popup() # Closes the shape selection popup if open

    def undo_action(self):
        """Hides the last drawn stroke or shape, moving back in the history."""
        if self.history_idx >= 0:
            stroke_items = self.history[self.history_idx] # Gets the items from the last stroke
            for item_id in stroke_items:
                self.canvas.itemconfigure(item_id, state='hidden') # Sets the items to be hidden
            self.history_idx -= 1 # Moves the history index back
            self.update_undo_redo_buttons() # Updates the state of Undo/Redo buttons
        self.close_shape_popup() # Closes the shape selection popup if open

    def redo_action(self):
        """Reveals the next stroke or shape in the history, moving forward."""
        if self.history_idx < len(self.history) - 1:
            self.history_idx += 1 # Moves the history index forward
            stroke_items = self.history[self.history_idx] # Gets the items from the next stroke
            for item_id in stroke_items:
                self.canvas.itemconfigure(item_id, state='normal') # Sets the items to be visible
            self.update_undo_redo_buttons() # Updates the state of Undo/Redo buttons
        self.close_shape_popup() # Closes the shape selection popup if open

    def update_undo_redo_buttons(self):
        """Enables or disables Undo/Redo buttons based on the current state of the history."""
        # Enables Undo button if there are actions to undo, otherwise disables it
        if self.history_idx >= 0:
            self.undo_button.config(state="normal")
        else:
            self.undo_button.config(state="disabled")

        # Enables Redo button if there are actions to redo, otherwise disables it
        if self.history_idx < len(self.history) - 1:
            self.redo_button.config(state="normal")
        else:
            self.redo_button.config(state="disabled")

# Application Entry Point: This block runs when the script is executed
if __name__ == "__main__":
    root = tk.Tk() # Creates the main Tkinter window (the application's root window)
    app = PaintApp(root) # Instantiates the PaintApp class, creating the application interface
    root.mainloop() # Starts the Tkinter event loop, which processes events and keeps the window open
