from PySide6.QtCore import Qt, QEvent, QRect, QPoint
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QWidget,
    QGridLayout,
    QSizePolicy,
    QMenuBar,
    QMenu,
    QDialog,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHBoxLayout,
    QDialogButtonBox,
    QHeaderView,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtGui import QMouseEvent
import sys
import rtmidi
import json
from pathlib import Path


class MIDIDeviceDialog(QDialog):
    def __init__(self, parent=None, current_input=None, current_output=None):
        super().__init__(parent)
        self.setWindowTitle("MIDI Device Selection")
        layout = QVBoxLayout(self)

        # Input devices section
        input_layout = QHBoxLayout()
        self.input_label = QLabel("MIDI Input Device:")
        self.input_combo = QComboBox()
        self.input_refresh = QPushButton("⟳")
        self.input_refresh.setMaximumWidth(30)
        self.input_refresh.clicked.connect(self.refresh_input_devices)

        input_layout.addWidget(self.input_label)
        input_layout.addWidget(self.input_combo)
        input_layout.addWidget(self.input_refresh)

        # Output devices section
        output_layout = QHBoxLayout()
        self.output_label = QLabel("MIDI Output Device:")
        self.output_combo = QComboBox()
        self.output_refresh = QPushButton("⟳")
        self.output_refresh.setMaximumWidth(30)
        self.output_refresh.clicked.connect(self.refresh_output_devices)

        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.output_combo)
        output_layout.addWidget(self.output_refresh)

        # Add layouts to main layout
        layout.addLayout(input_layout)
        layout.addLayout(output_layout)

        # Add OK/Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Store current selections
        self.current_input = current_input
        self.current_output = current_output

        # Initial refresh
        self.refresh_input_devices()
        self.refresh_output_devices()

    def refresh_input_devices(self):
        midi_in = rtmidi.RtMidiIn()
        self.input_combo.clear()
        ports = midi_in.get_ports()
        self.input_combo.addItems(ports)

        # Restore previous selection if it exists
        if self.current_input in ports:
            self.input_combo.setCurrentText(self.current_input)

    def refresh_output_devices(self):
        midi_out = rtmidi.RtMidiOut()
        self.output_combo.clear()
        ports = midi_out.get_ports()
        self.output_combo.addItems(ports)

        # Restore previous selection if it exists
        if self.current_output in ports:
            self.output_combo.setCurrentText(self.current_output)


class MIDILearnDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MIDI Learn")
        self.setModal(True)
        layout = QVBoxLayout(self)

        self.label = QLabel("Waiting for MIDI input...\nPress any MIDI message")
        layout.addWidget(self.label)


class NoteMappingDialog(QDialog):
    def __init__(self, button_mappings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MIDI Mappings")
        self.setModal(False)
        self.resize(800, 600)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Store button mappings and parent
        self.button_mappings = button_mappings
        self.main_window = parent

        # Create table with columns for all MIDI parameters
        self.table = QTableWidget(8, 6)  # Always 8 rows
        self.table.setHorizontalHeaderLabels(
            ["Button", "Input Type", "Input #", "Output Type", "Output #", "Value"]
        )

        # Set font size for header and cells
        font = self.table.font()
        font.setPointSize(14)
        self.table.setFont(font)
        header = self.table.horizontalHeader()
        header.setFont(font)

        # Set row height
        self.table.verticalHeader().setDefaultSectionSize(40)

        # Stretch columns to fill width
        for i in range(self.table.columnCount()):
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)

        # MIDI type options
        self.midi_types = ["note", "cc", "pc"]

        # Fill table with current mappings
        self.row_to_button = {}  # Map table rows to button objects
        buttons = list(button_mappings.values())
        for i in range(8):  # Always process 8 rows
            button = buttons[i]

            # Editable button name
            button_name_item = QTableWidgetItem(button.text())
            button_name_item.setFlags(button_name_item.flags() | Qt.ItemIsEditable)
            self.table.setItem(i, 0, button_name_item)

            # Input type combo
            input_type_combo = QComboBox()
            input_type_combo.setFont(font)
            input_type_combo.addItems(self.midi_types)
            input_type_combo.setCurrentText(button.input_type)
            self.table.setCellWidget(i, 1, input_type_combo)

            # Input number
            input_number_item = QTableWidgetItem(str(button.input_number or ""))
            self.table.setItem(i, 2, input_number_item)

            # Output type combo
            output_type_combo = QComboBox()
            output_type_combo.setFont(font)
            output_type_combo.addItems(self.midi_types)
            output_type_combo.setCurrentText(button.output_type)
            self.table.setCellWidget(i, 3, output_type_combo)

            # Output number
            output_number_item = QTableWidgetItem(str(button.output_number or ""))
            self.table.setItem(i, 4, output_number_item)

            # Value (for CC)
            value_item = QTableWidgetItem(str(button.output_value))
            self.table.setItem(i, 5, value_item)

            # Map row to button
            self.row_to_button[i] = button

            # Connect change handlers
            def make_handler(btn):
                def handler():
                    self.update_button_config(btn)

                return handler

            input_type_combo.currentTextChanged.connect(make_handler(button))
            output_type_combo.currentTextChanged.connect(make_handler(button))

        # Connect itemChanged signal for direct cell edits
        self.table.itemChanged.connect(self.on_cell_changed)

        layout.addWidget(self.table)

    def on_cell_changed(self, item):
        row = item.row()
        col = item.column()
        button = self.row_to_button[row]

        try:
            value = item.text()
            if col == 0:  # Button name
                old_name = button.text()
                new_name = value.strip()
                if new_name and new_name != old_name:
                    # Update button text
                    button.setText(new_name)
                    
                    # Update mappings in main window
                    if self.main_window:
                        if old_name in self.main_window.buttons:
                            self.main_window.buttons[new_name] = self.main_window.buttons.pop(old_name)
                            # Update button_order
                            if old_name in self.main_window.button_order:
                                index = self.main_window.button_order.index(old_name)
                                self.main_window.button_order[index] = new_name
                
            elif col == 2:  # Input number
                button.input_number = int(value) if value else None
            elif col == 4:  # Output number
                button.output_number = int(value) if value else None
            elif col == 5:  # Value
                button.output_value = int(value) if value else 127

            # Save after each change
            if self.main_window:
                self.main_window.save_config()
            
        except ValueError:
            # Restore previous value if invalid input
            if col == 2:
                item.setText(str(button.input_number or ""))
            elif col == 4:
                item.setText(str(button.output_number or ""))
            elif col == 5:
                item.setText(str(button.output_value))

    def update_button_config(self, button):
        try:
            # Find the row for this button
            row = None
            for i, btn in enumerate(self.button_mappings.values()):
                if btn == button:
                    row = i
                    break

            if row is not None:
                # Update input configuration
                button.input_type = self.table.cellWidget(row, 1).currentText()
                input_number = self.table.item(row, 2).text()
                button.input_number = int(input_number) if input_number else None

                # Update output configuration
                button.output_type = self.table.cellWidget(row, 3).currentText()
                output_number = self.table.item(row, 4).text()
                button.output_number = int(output_number) if output_number else None

                value = self.table.item(row, 5).text()
                button.output_value = int(value) if value else 127

                # Save configuration after each change
                if self.main_window:
                    self.main_window.save_config()
        except ValueError:
            pass  # Handle invalid number inputs


class CustomButton(QPushButton):
    def __init__(self, name):
        super().__init__(name)
        self.input_type = "note"
        self.input_number = None
        self.output_type = "note"
        self.output_number = None
        self.output_value = 127
        self.midi_message = None

        # Learn mode UI elements
        self.learn_label = None
        self.button_container = None
        self.ok_button = None
        self.cancel_button = None

    def hideLearnMode(self):
        """Hide MIDI learn UI elements"""
        if self.learn_label:
            self.learn_label.hide()
        if self.button_container:
            self.button_container.hide()

    def showLearnMode(self, pos=None):  # Add pos parameter with default None
        """Show MIDI learn UI elements"""
        if self.learn_label is None:
            # Create label if it doesn't exist
            self.learn_label = QLabel("Waiting for MIDI message...", self)
            self.learn_label.setStyleSheet(
                """
                QLabel {
                    background-color: rgba(0, 0, 0, 0.8);
                    color: white;
                    padding: 10px;
                    border-radius: 5px;
                    font-size: 16px;
                }
            """
            )
            self.learn_label.setAlignment(Qt.AlignCenter)

            # Create buttons container
            self.button_container = QWidget(self)
            button_layout = QHBoxLayout(self.button_container)

            # Create OK and Cancel buttons
            self.ok_button = QPushButton("OK", self.button_container)
            self.cancel_button = QPushButton("Cancel", self.button_container)

            # Style buttons
            button_style = """
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    padding: 5px 15px;
                    border-radius: 3px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """
            self.ok_button.setStyleSheet(button_style)
            self.cancel_button.setStyleSheet(
                button_style.replace("#2196F3", "#F44336").replace("#1976D2", "#D32F2F")
            )

            # Add buttons to layout
            button_layout.addWidget(self.ok_button)
            button_layout.addWidget(self.cancel_button)

            # Connect button signals
            self.ok_button.clicked.connect(
                lambda: self.window().finish_midi_learn(self)
            )
            self.cancel_button.clicked.connect(
                lambda: self.window().cancel_midi_learn()
            )

        # Position the learn UI elements
        if pos:
            # Position relative to the clicked position
            self.learn_label.move(pos.x(), pos.y() - self.learn_label.height())
            self.button_container.move(pos.x(), pos.y())
        else:
            # Center in the button
            self.learn_label.move(
                (self.width() - self.learn_label.width()) // 2,
                (self.height() - self.learn_label.height()) // 2 - 20,
            )
            self.button_container.move(
                (self.width() - self.button_container.width()) // 2,
                (self.height() - self.button_container.height()) // 2 + 20,
            )

        # Show the UI elements
        self.learn_label.show()
        self.button_container.show()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Touch-Friendly MIDI Controller")
        self.showFullScreen()

        # Initialize state variables
        self.buttons = {}
        self.button_order = []
        self.current_learning_button = None
        self.is_learn_mode = False
        self.changes_made = False  # Track changes

        # Initialize MIDI devices
        self.midi_in = rtmidi.RtMidiIn()
        self.midi_out = rtmidi.RtMidiOut()
        self.current_input_port = None
        self.current_output_port = None

        # Set config file paths
        self.config_dir = Path.cwd() / "configs"
        self.config_dir.mkdir(exist_ok=True)
        self.default_config = self.config_dir / "default_config.json"
        self.temp_config = self.config_dir / "temp_config.json"
        self.current_config = None

        # Setup UI first (this will create default buttons)
        self.setup_ui()

        # Load configuration
        if self.temp_config.exists():
            self.load_config(self.temp_config)
        elif self.default_config.exists():
            self.load_config(self.default_config)
        else:
            self.create_default_config()

        # Setup menu
        self.setup_menu()

    def create_default_config(self):
        """Create a default configuration"""
        default_config = {
            "buttons": {
                f"Button {i+1}": {
                    "input_type": "note",
                    "input_number": None,
                    "output_type": "note",
                    "output_number": None,
                    "output_value": 127,
                    "midi_message": None,
                }
                for i in range(8)
            },
            "midi_ports": {"input": None, "output": None},
        }

        # Save default config
        with open(self.default_config, "w") as f:
            json.dump(default_config, f, indent=4)

        # Load the default config
        self.load_config(self.default_config)

    def save_config(self, config_file=None):
        """Save configuration to file"""
        if config_file is None:
            config_file = self.temp_config

        config = {
            "buttons": {
                btn.text(): {
                    "input_type": btn.input_type,
                    "input_number": btn.input_number,
                    "output_type": btn.output_type,
                    "output_number": btn.output_number,
                    "output_value": btn.output_value,
                    "midi_message": getattr(btn, "midi_message", None),
                }
                for btn in self.buttons.values()
            },
            "midi_ports": {
                "input": self.current_input_port,
                "output": self.current_output_port,
            },
        }

        try:
            with open(config_file, "w") as f:
                json.dump(config, f, indent=4)
            print(f"Configuration saved to: {config_file}")
        except Exception as e:
            print(f"Error saving configuration: {e}")

    def save_config_as(self):
        """Save configuration with a new name"""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Configuration File",
            str(self.config_dir),
            "JSON Files (*.json);;All Files (*)",
        )
        if file_name:
            self.save_config(Path(file_name))
            self.current_config = Path(file_name)

    def closeEvent(self, event):
        """Handle application closing"""
        if self.changes_made and self.current_config != self.default_config:
            reply = QMessageBox.question(
                self,
                "Save Changes",
                "Do you want to save your changes?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )

            if reply == QMessageBox.Save:
                if self.current_config and self.current_config != self.temp_config:
                    self.save_config(self.current_config)
                else:
                    self.save_config_as()
                if self.temp_config.exists():
                    self.temp_config.unlink()
                event.accept()
            elif reply == QMessageBox.Discard:
                if self.temp_config.exists():
                    self.temp_config.unlink()
                event.accept()
            else:
                event.ignore()
        else:
            # If no changes or using default config, just exit
            if self.temp_config.exists():
                self.temp_config.unlink()
            event.accept()

    def on_cell_changed(self, item):
        row = item.row()
        col = item.column()
        button = self.row_to_button[row]

        try:
            value = item.text()
            if col == 0:  # Button name
                old_name = button.text()
                new_name = value.strip()
                if new_name and new_name != old_name:
                    # Update button text
                    button.setText(new_name)
                    
                    # Update mappings in main window
                    if self.main_window:
                        if old_name in self.main_window.buttons:
                            self.main_window.buttons[new_name] = self.main_window.buttons.pop(old_name)
                            # Update button_order
                            if old_name in self.main_window.button_order:
                                index = self.main_window.button_order.index(old_name)
                                self.main_window.button_order[index] = new_name
                
            elif col == 2:  # Input number
                button.input_number = int(value) if value else None
            elif col == 4:  # Output number
                button.output_number = int(value) if value else None
            elif col == 5:  # Value
                button.output_value = int(value) if value else 127

            # Save after each change
            if self.main_window:
                self.main_window.save_config()
            
        except ValueError:
            # Restore previous value if invalid input
            if col == 2:
                item.setText(str(button.input_number or ""))
            elif col == 4:
                item.setText(str(button.output_number or ""))
            elif col == 5:
                item.setText(str(button.output_value))

        # Save to temp file after each change
        self.save_config(self.temp_config)
        self.changes_made = True  # Mark changes made

    def update_button_config(self, button):
        try:
            # Find the row for this button
            row = None
            for i, btn in enumerate(self.button_mappings.values()):
                if btn == button:
                    row = i
                    break

            if row is not None:
                # Update input configuration
                button.input_type = self.table.cellWidget(row, 1).currentText()
                input_number = self.table.item(row, 2).text()
                button.input_number = int(input_number) if input_number else None

                # Update output configuration
                button.output_type = self.table.cellWidget(row, 3).currentText()
                output_number = self.table.item(row, 4).text()
                button.output_number = int(output_number) if output_number else None

                value = self.table.item(row, 5).text()
                button.output_value = int(value) if value else 127

                # Save configuration after each change
                if self.main_window:
                    self.main_window.save_config()
        except ValueError:
            pass  # Handle invalid number inputs

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Add MIDI Learn button at the top
        learn_button = QPushButton("MIDI Learn Mode")
        learn_button.setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 15px;
                border-radius: 5px;
                font-size: 18px;
                min-height: 50px;
            }
            QPushButton:checked {
                background-color: #F44336;
            }
        """
        )
        learn_button.setCheckable(True)
        learn_button.clicked.connect(self.toggle_learn_mode)
        main_layout.addWidget(learn_button)
        self.learn_button = learn_button

        # Create grid layout for buttons
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(20)
        grid_layout.setContentsMargins(20, 20, 20, 20)

        # Define button colors
        button_colors = [
            "#FF5252",
            "#FF4081",
            "#7C4DFF",
            "#448AFF",
            "#64FFDA",
            "#69F0AE",
            "#FFEB3B",
            "#FF9800",
        ]

        # Initialize ordered storage
        self.buttons = {}
        self.button_order = []

        # Create buttons in a specific order
        for i in range(8):
            name = f"Button {i+1}"
            row = i // 4  # 0 for first row (0-3), 1 for second row (4-7)
            col = i % 4  # 0,1,2,3 for each row

            button = CustomButton(name)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            button.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {button_colors[i]};
                    color: white;
                    border: none;
                    border-radius: 15px;
                    font-size: 24px;
                    font-weight: bold;
                }}
                QPushButton:pressed {{
                    background-color: {button_colors[i]}99;
                }}
            """
            )

            button.clicked.connect(
                lambda checked, btn=button: self.handle_button_click(btn)
            )

            # Store button in both dictionaries and order list
            self.buttons[name] = button
            self.button_order.append(name)

            # Add to grid
            grid_layout.addWidget(button, row, col)

        # Make grid cells expand evenly
        for i in range(2):
            grid_layout.setRowStretch(i, 1)
        for i in range(4):
            grid_layout.setColumnStretch(i, 1)

        main_layout.addWidget(grid_widget)

        # Add status label at the bottom
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(
            """
            QLabel {
                color: white;
                background-color: rgba(0, 0, 0, 0.7);
                padding: 10px;
                border-radius: 5px;
                font-size: 16px;
            }
        """
        )
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.hide()
        main_layout.addWidget(self.status_label)

    def toggle_learn_mode(self, checked):
        if checked:
            self.is_learn_mode = True
            self.status_label.setText("Select a button to assign MIDI message")
            self.status_label.show()
        else:
            # Allow unchecking and cancel learn mode
            self.cancel_midi_learn()
            self.is_learn_mode = False
            self.status_label.hide()
        return True

    def handle_button_click(self, button):
        if self.is_learn_mode:
            # Enter MIDI learn mode for this button
            if self.current_learning_button:
                return  # Don't allow switching buttons while in learn mode
            self.current_learning_button = button
            button.showLearnMode()
            self.status_label.setText("Waiting for MIDI message...")
        else:
            # Normal button press handling
            self.handle_button_press(button)

    def setup_menu(self):
        # Create main menu bar
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #333;
                color: white;
                padding: 5px;
            }
            QMenuBar::item {
                padding: 5px 10px;
                background: transparent;
            }
            QMenuBar::item:selected {
                background: #555;
            }
        """)

        # Create a container widget for the entire top bar
        top_container = QWidget()
        top_layout = QHBoxLayout(top_container)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)

        # MIDI menu (left)
        midi_menu = menubar.addMenu("MIDI")
        devices_action = midi_menu.addAction("Select Devices")
        devices_action.triggered.connect(self.show_midi_dialog)
        mappings_action = midi_menu.addAction("View Note Mappings")
        mappings_action.triggered.connect(self.show_mappings_dialog)

        # Config menu (left)
        self.config_menu = menubar.addMenu("Config")
        save_action = self.config_menu.addAction("Save Configuration")
        save_action.triggered.connect(self.save_config)
        save_as_action = self.config_menu.addAction("Save Configuration As...")
        save_as_action.triggered.connect(self.save_config_as)
        load_action = self.config_menu.addAction("Load Configuration")
        load_action.triggered.connect(self.load_config_dialog)

        # Add menubar to layout
        top_layout.addWidget(menubar)

        # Create and add config label
        self.config_label = QLabel()
        self.config_label.setStyleSheet("""
            QLabel {
                color: white;
                padding: 0 10px;
                font-size: 14px;
                font-weight: bold;
                background-color: #333;
            }
        """)
        self.config_label.setAlignment(Qt.AlignCenter)
        top_layout.addWidget(self.config_label)

        # Add stretch to keep everything aligned
        top_layout.addStretch()

        # Set the top container as the menu widget
        self.setMenuWidget(top_container)

    def update_config_label(self):
        """Update the config label in the menu bar"""
        if self.current_config:
            config_name = self.current_config.name
            if self.current_config == self.temp_config:
                config_name += " (Unsaved)"
            elif self.current_config == self.default_config:
                config_name += " (Default)"
            self.config_label.setText(f"Current Config: {config_name}")

    def load_config_dialog(self):
        try:
            file_name, _ = QFileDialog.getOpenFileName(
                self,
                "Load Configuration File",
                str(self.config_dir),
                "JSON Files (*.json);;All Files (*)",
            )
            if file_name:
                print(f"Selected config file: {file_name}")  # Debug print
                self.load_config(Path(file_name))
        except Exception as e:
            print(f"Error in load_config_dialog: {e}")
            import traceback

            traceback.print_exc()  # Print full error traceback

    def update_ui_from_config(self):
        try:
            print("Updating UI from config")  # Debug print

            # Update button names and properties
            for button in self.buttons.values():
                button_name = button.text()
                print(f"Updated button name to: {button_name}")  # Debug print

                # Update button_order to match current button names
                if button_name not in self.button_order:
                    index = list(self.buttons.values()).index(button)
                    if index < len(self.button_order):
                        self.button_order[index] = button_name

            print("UI update completed")  # Debug print
        except Exception as e:
            print(f"Error updating UI: {e}")
            import traceback

            traceback.print_exc()  # Print full error traceback

    def load_config(self, config_file=None):
        if config_file is None:
            config_file = self.config_file

        try:
            print(f"Loading configuration from: {config_file}")
            if isinstance(config_file, str):
                config_file = Path(config_file)

            if config_file.exists():
                with open(config_file, "r") as f:
                    config = json.load(f)
                print(f"Loaded config: {config}")

                # Set current config file
                self.current_config = config_file

                # Load button configurations
                if "buttons" in config:
                    # Get the list of button configurations in order
                    button_configs = list(config["buttons"].items())

                    # Update each button with its corresponding configuration
                    for i, (button_name, button_config) in enumerate(button_configs):
                        if i < len(self.button_order):
                            old_name = self.button_order[i]
                            button = self.buttons[old_name]

                            # Update button properties
                            button.setText(button_name)  # Update the visible text
                            button.input_type = button_config.get("input_type", "note")
                            button.input_number = button_config.get("input_number")
                            button.output_type = button_config.get("output_type", "note")
                            button.output_number = button_config.get("output_number")
                            button.output_value = button_config.get("output_value", 127)
                            if "midi_message" in button_config:
                                button.midi_message = button_config["midi_message"]

                            # Update mappings
                            if old_name != button_name:
                                self.buttons[button_name] = self.buttons.pop(old_name)
                                self.button_order[i] = button_name

                            print(f"Updated button {button_name} (was {old_name})")

                # Load MIDI port configurations
                if "midi_ports" in config:
                    self.current_input_port = config["midi_ports"].get("input")
                    self.current_output_port = config["midi_ports"].get("output")
                    if self.current_input_port or self.current_output_port:
                        self.connect_midi_devices(
                            self.current_input_port, self.current_output_port
                        )

                # Update config label
                self.update_config_label()
                
                print("Configuration loaded successfully")
            else:
                print(f"Configuration file not found: {config_file}")
        except Exception as e:
            print(f"Error loading configuration: {e}")
            import traceback
            traceback.print_exc()

    def show_midi_dialog(self):
        dialog = MIDIDeviceDialog(
            self,
            current_input=self.current_input_port,
            current_output=self.current_output_port,
        )
        if dialog.exec():
            # Connect to selected devices
            self.connect_midi_devices(
                dialog.input_combo.currentText(), dialog.output_combo.currentText()
            )
            # Store current selections
            self.current_input_port = dialog.input_combo.currentText()
            self.current_output_port = dialog.output_combo.currentText()

    def connect_midi_devices(self, input_port, output_port):
        # Close existing connections
        if self.midi_in.is_port_open():
            self.midi_in.close_port()
        if self.midi_out.is_port_open():
            self.midi_out.close_port()

        # Open new connections
        if input_port:
            input_ports = self.midi_in.get_ports()
            if input_port in input_ports:
                self.midi_in.open_port(input_ports.index(input_port))
                self.midi_in.set_callback(self.handle_midi_input)
                self.current_input_port = input_port

        if output_port:
            output_ports = self.midi_out.get_ports()
            if output_port in output_ports:
                self.midi_out.open_port(output_ports.index(output_port))
                self.current_output_port = output_port

    def handle_midi_input(self, midi_message, time_stamp):
        message, delta_time = midi_message
        if len(message) >= 2:  # All MIDI messages have at least 2 bytes
            status = message[0]

            if self.current_learning_button:
                # Store the complete MIDI message
                self.current_learning_button.midi_message = message

                # MIDI Learn mode
                if status >= 0x90 and status <= 0x9F:  # Note On
                    self.current_learning_button.input_type = "note"
                    self.current_learning_button.input_number = message[1]
                elif status >= 0xB0 and status <= 0xBF:  # CC
                    self.current_learning_button.input_type = "cc"
                    self.current_learning_button.input_number = message[1]
                elif status >= 0xC0 and status <= 0xCF:  # Program Change
                    self.current_learning_button.input_type = "pc"
                    self.current_learning_button.input_number = message[1]

                # Update learn label with received message
                msg_type = self.current_learning_button.input_type.upper()
                msg_num = self.current_learning_button.input_number
                self.current_learning_button.learn_label.setText(
                    f"Received: {msg_type} {msg_num}\nClick OK to confirm"
                )
            else:
                # Normal mode - find and trigger button with matching input
                for button in self.buttons.values():
                    if (
                        button.input_type == "note"
                        and status >= 0x90
                        and status <= 0x9F
                    ):
                        if button.input_number == message[1]:
                            self.handle_button_press(button)
                    elif (
                        button.input_type == "cc" and status >= 0xB0 and status <= 0xBF
                    ):
                        if button.input_number == message[1]:
                            self.handle_button_press(button)
                    elif (
                        button.input_type == "pc" and status >= 0xC0 and status <= 0xCF
                    ):
                        if button.input_number == message[1]:
                            self.handle_button_press(button)

    def handle_button_press(self, button):
        # Don't handle button press if we're in MIDI learn mode
        if self.current_learning_button:
            return

        if not self.midi_out.isPortOpen() or button.output_number is None:
            return

        if button.output_type == "note":
            # Note On
            self.midi_out.send_message([0x90, button.output_number, 127])
            # Note Off
            self.midi_out.send_message([0x80, button.output_number, 0])
        elif button.output_type == "cc":
            # Control Change
            self.midi_out.send_message(
                [0xB0, button.output_number, button.output_value]
            )
        elif button.output_type == "pc":
            # Program Change
            self.midi_out.send_message([0xC0, button.output_number])

    def keyPressEvent(self, event):
        # Handle Escape key to exit fullscreen
        if event.key() == Qt.Key_Escape:
            self.close()

    def show_mappings_dialog(self):
        try:
            # Create an ordered dictionary based on button_order
            ordered_mappings = {}
            buttons_list = list(self.buttons.values())

            # Always process 8 buttons
            for i in range(8):
                if i < len(buttons_list):
                    button = buttons_list[i]
                    ordered_mappings[button.text()] = button
                else:
                    # Create a default button for empty slots
                    default_button = CustomButton(f"Button {i+1}")
                    ordered_mappings[default_button.text()] = default_button
                print(
                    f"Adding button to mappings: {ordered_mappings[list(ordered_mappings.keys())[i]].text()}"
                )  # Debug print

            dialog = NoteMappingDialog(ordered_mappings, self)
            dialog.exec()
        except Exception as e:
            print(f"Error showing mappings dialog: {e}")
            import traceback

            traceback.print_exc()

    def show_midi_learn(self, button, pos):
        if self.current_learning_button:
            self.current_learning_button.hideLearnMode()

        self.current_learning_button = button
        button.showLearnMode(pos)

    def eventFilter(self, obj, event):
        if isinstance(event, QMouseEvent):
            if (
                event.type() == QEvent.Type.MouseButtonPress
                and self.current_learning_button
            ):
                # Check if click is outside the MIDI learn UI
                if not self.is_click_inside_learn_ui(event.globalPosition().toPoint()):
                    self.cancel_midi_learn(self.current_learning_button)
                return True  # Consume the click event while in MIDI learn mode
        return super().eventFilter(obj, event)

    def finish_midi_learn(self, button):
        if button == self.current_learning_button:
            # Save the MIDI mapping here
            self.save_config()  # Save the new configuration

            # Clean up the UI
            button.hideLearnMode()
            self.current_learning_button = None
            self.is_learn_mode = False
            self.learn_button.setChecked(False)
            self.status_label.hide()

    def cancel_midi_learn(self):
        if self.current_learning_button:
            self.current_learning_button.hideLearnMode()
            self.current_learning_button = None
        self.is_learn_mode = False
        self.learn_button.setChecked(False)
        self.status_label.hide()

    def is_click_inside_learn_ui(self, global_pos):
        if not self.current_learning_button:
            return False

        button = self.current_learning_button

        # Check if click is inside label or button
        label_geo = button.learn_label.geometry()
        buttons_geo = button.button_container.geometry()
        label_global = button.mapToGlobal(label_geo.topLeft())
        buttons_global = button.mapToGlobal(buttons_geo.topLeft())

        label_rect = QRect(label_global, label_geo.size())
        buttons_rect = QRect(buttons_global, buttons_geo.size())

        return label_rect.contains(global_pos) or buttons_rect.contains(global_pos)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
