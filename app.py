import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkcalendar import DateEntry
import sqlite3
import datetime
import logging

# Configure logging
logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s:%(message)s'
)


class EntryFormLogic:
    def __init__(self):
        self.conn = sqlite3.connect('entries.db')
        self.cursor = self.conn.cursor()
        self.initialize_database()
        logging.info("Database initialized.")

    def initialize_database(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS entries (
                sr_no INTEGER PRIMARY KEY,
                associate_id TEXT UNIQUE NOT NULL,
                date TEXT NOT NULL,
                name TEXT NOT NULL,
                mobile TEXT NOT NULL,
                height TEXT,
                age INTEGER,
                email TEXT,
                adhaar TEXT,
                dob TEXT
            )
        ''')
        self.conn.commit()

    def get_next_sr_no(self):
        self.cursor.execute('SELECT MAX(sr_no) FROM entries')
        result = self.cursor.fetchone()[0]
        next_sr_no = 1 if result is None else result + 1
        logging.debug(f"Next Sr. No. fetched: {next_sr_no}")
        return next_sr_no

    def get_all_entries(self):
        self.cursor.execute('SELECT * FROM entries ORDER BY sr_no')
        return self.cursor.fetchall()

    def get_entry_by_sr_no(self, sr_no):
        self.cursor.execute('SELECT * FROM entries WHERE sr_no = ?', (sr_no,))
        return self.cursor.fetchone()

    def validate_form(self, data, updating=False):
        error_messages = []

        if not data['associate_id']:
            error_messages.append("Associate I.D. No. is required.")
        if not data['name']:
            error_messages.append("Name is required.")
        if not data['mobile']:
            error_messages.append("Mobile number is required.")
        elif len(data['mobile']) != 10 or not data['mobile'].isdigit():
            error_messages.append("Mobile number must be exactly 10 digits.")
        if data['age'] and (data['age'] < 0 or data['age'] > 120):
            error_messages.append("Please enter a valid age between 0 and 120.")
        if data['email'] and '@' not in data['email']:
            error_messages.append("Please enter a valid email address.")
        if data['adhaar'] and (len(data['adhaar']) != 12 or not data['adhaar'].isdigit()):
            error_messages.append("Adhaar Card No. must be exactly 12 digits.")

        # Check for duplicate Associate I.D. No.
        self.cursor.execute('SELECT * FROM entries WHERE associate_id = ?', (data['associate_id'],))
        existing_entry = self.cursor.fetchone()
        if existing_entry:
            if not updating or existing_entry[0] != data['sr_no']:
                error_messages.append("Duplicate Associate I.D. No. found.")

        # Check for duplicate Sr. No. when adding new entries
        if not updating:
            self.cursor.execute('SELECT * FROM entries WHERE sr_no = ?', (data['sr_no'],))
            if self.cursor.fetchone():
                error_messages.append("Duplicate Sr. No. found.")

        return error_messages

    def save_entry(self, data):
        try:
            self.cursor.execute('''
                INSERT INTO entries (
                    sr_no, associate_id, date, name, mobile, height, age, email, adhaar, dob
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (data['sr_no'], data['associate_id'], data['date'], data['name'], data['mobile'],
                  data['height'], data['age'], data['email'], data['adhaar'], data['dob']))
            self.conn.commit()
            logging.info(f"Entry saved: Sr. No. {data['sr_no']}, Associate I.D. No. {data['associate_id']}")
            return True
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            return False

    def update_entry(self, data):
        try:
            self.cursor.execute('''
                UPDATE entries SET
                    associate_id = ?,
                    date = ?,
                    name = ?,
                    mobile = ?,
                    height = ?,
                    age = ?,
                    email = ?,
                    adhaar = ?,
                    dob = ?
                WHERE sr_no = ?
            ''', (data['associate_id'], data['date'], data['name'], data['mobile'],
                  data['height'], data['age'], data['email'], data['adhaar'], data['dob'], data['sr_no']))
            self.conn.commit()
            logging.info(f"Entry updated: Sr. No. {data['sr_no']}, Associate I.D. No. {data['associate_id']}")
            return True
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            return False

    def delete_entry(self, sr_no):
        try:
            self.cursor.execute('DELETE FROM entries WHERE sr_no = ?', (sr_no,))
            self.conn.commit()
            logging.info(f"Entry deleted: Sr. No. {sr_no}")
            return True
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            return False

    def close_connection(self):
        self.conn.close()
        logging.info("Database connection closed.")


class EntryFormView(tk.Tk):
    def __init__(self, logic):
        super().__init__()
        self.logic = logic
        self.title("Entry Card Form")
        self.geometry("600x600")

        # Set the theme
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Choose a theme that works across platforms

        self.create_widgets()  # Initialize widgets first

        # Now that widgets are created, we can use variables like self.sr_no_var
        self.entries = self.logic.get_all_entries()
        if self.entries:
            self.current_entry_index = 0
            self.load_entry(self.entries[self.current_entry_index])
        else:
            self.current_entry_index = None
            self.reset_form()

        self.associate_id_entry.focus_set()
        self.set_navigation_buttons_state()
        logging.info("GUI initialized.")

    def create_widgets(self):
        # Main Frame
        main_frame = ttk.Frame(self, padding=(20, 10, 20, 10))
        main_frame.pack(fill='both', expand=True)

        # Title Label
        title_label = ttk.Label(main_frame, text="Entry Card Form", font=('Helvetica', 16, 'bold'))
        title_label.pack(pady=10)

        # Content Frame
        content_frame = ttk.Frame(main_frame, padding=(10, 10))
        content_frame.pack(fill='both', expand=True)

        # Configure grid weights for responsiveness
        for i in range(8):
            content_frame.grid_rowconfigure(i, weight=1)
        for i in range(4):
            content_frame.grid_columnconfigure(i, weight=1)

        # Sr. No.
        ttk.Label(content_frame, text="Sr. No.:").grid(row=0, column=0, pady=5, padx=5, sticky='e')
        self.sr_no_var = tk.IntVar()
        self.sr_no_entry = ttk.Entry(content_frame, textvariable=self.sr_no_var, state='readonly')
        self.sr_no_entry.grid(row=0, column=1, pady=5, padx=5, sticky='we')

        # Date
        ttk.Label(content_frame, text="Date:").grid(row=0, column=2, pady=5, padx=5, sticky='e')
        self.date_var = tk.StringVar()
        self.date_entry = ttk.Entry(content_frame, textvariable=self.date_var, state='readonly')
        self.date_entry.grid(row=0, column=3, pady=5, padx=5, sticky='we')

        # Associate I.D. No.
        ttk.Label(content_frame, text="Associate I.D. No.:").grid(row=1, column=0, pady=5, padx=5, sticky='e')
        self.associate_id_var = tk.StringVar()
        self.associate_id_entry = ttk.Entry(content_frame, textvariable=self.associate_id_var)
        self.associate_id_entry.grid(row=1, column=1, columnspan=3, pady=5, padx=5, sticky='we')

        # Name
        ttk.Label(content_frame, text="Name:").grid(row=2, column=0, pady=5, padx=5, sticky='e')
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(content_frame, textvariable=self.name_var)
        self.name_entry.grid(row=2, column=1, columnspan=3, pady=5, padx=5, sticky='we')

        # Mobile
        ttk.Label(content_frame, text="Mobile:").grid(row=3, column=0, pady=5, padx=5, sticky='e')
        self.mobile_var = tk.StringVar()
        self.mobile_entry = ttk.Entry(content_frame, textvariable=self.mobile_var)
        self.mobile_entry.grid(row=3, column=1, columnspan=3, pady=5, padx=5, sticky='we')

        # Height
        ttk.Label(content_frame, text="Height (cm):").grid(row=4, column=0, pady=5, padx=5, sticky='e')
        self.height_var = tk.StringVar()
        self.height_entry = ttk.Entry(content_frame, textvariable=self.height_var)
        self.height_entry.grid(row=4, column=1, pady=5, padx=5, sticky='we')

        # Age
        ttk.Label(content_frame, text="Age:").grid(row=4, column=2, pady=5, padx=5, sticky='e')
        self.age_var = tk.IntVar()
        self.age_entry = ttk.Entry(content_frame, textvariable=self.age_var)
        self.age_entry.grid(row=4, column=3, pady=5, padx=5, sticky='we')

        # E-Mail Id
        ttk.Label(content_frame, text="E-Mail Id:").grid(row=5, column=0, pady=5, padx=5, sticky='e')
        self.email_var = tk.StringVar()
        self.email_entry = ttk.Entry(content_frame, textvariable=self.email_var)
        self.email_entry.grid(row=5, column=1, columnspan=3, pady=5, padx=5, sticky='we')

        # Adhaar Card No.
        ttk.Label(content_frame, text="Adhaar Card No.:").grid(row=6, column=0, pady=5, padx=5, sticky='e')
        self.adhaar_var = tk.StringVar()
        self.adhaar_entry = ttk.Entry(content_frame, textvariable=self.adhaar_var)
        self.adhaar_entry.grid(row=6, column=1, columnspan=3, pady=5, padx=5, sticky='we')

        # DOB
        ttk.Label(content_frame, text="DOB:").grid(row=7, column=0, pady=5, padx=5, sticky='e')
        self.dob_var = tk.StringVar()
        self.dob_entry = DateEntry(content_frame, textvariable=self.dob_var, date_pattern='yyyy-mm-dd')
        self.dob_entry.grid(row=7, column=1, columnspan=3, pady=5, padx=5, sticky='we')

        # Submit Button Frame
        button_frame = ttk.Frame(main_frame, padding=(10, 10))
        button_frame.pack(fill='x', expand=False)

        # Submit Button
        self.submit_button = ttk.Button(button_frame, text="Submit", command=self.submit_form)
        self.submit_button.pack(pady=10, padx=5, fill='x')

        # Navigation Buttons Frame
        nav_frame = ttk.Frame(main_frame, padding=(10, 10))
        nav_frame.pack(fill='x', expand=False)

        # Previous Button
        self.prev_button = ttk.Button(nav_frame, text="Previous", command=self.prev_entry)
        self.prev_button.pack(side='left', pady=10, padx=5)

        # Next Button
        self.next_button = ttk.Button(nav_frame, text="Next", command=self.next_entry)
        self.next_button.pack(side='left', pady=10, padx=5)

        # Update Button
        self.update_button = ttk.Button(nav_frame, text="Update", command=self.update_entry)
        self.update_button.pack(side='left', pady=10, padx=5)

        # Delete Button
        self.delete_button = ttk.Button(nav_frame, text="Delete", command=self.delete_entry)
        self.delete_button.pack(side='left', pady=10, padx=5)

        # Add New Entry Button
        self.add_new_button = ttk.Button(nav_frame, text="Add New", command=self.add_new_entry)
        self.add_new_button.pack(side='left', pady=10, padx=5)

    def load_entry(self, entry):
        self.sr_no_var.set(entry[0])
        self.associate_id_var.set(entry[1])
        self.date_var.set(entry[2])
        self.name_var.set(entry[3])
        self.mobile_var.set(entry[4])
        self.height_var.set(entry[5] if entry[5] is not None else '')
        self.age_var.set(entry[6] if entry[6] is not None else 0)
        self.email_var.set(entry[7] if entry[7] is not None else '')
        self.adhaar_var.set(entry[8] if entry[8] is not None else '')
        self.dob_var.set(entry[9] if entry[9] is not None else '')

    def set_navigation_buttons_state(self):
        if self.current_entry_index is None:
            # We're in add new entry mode
            self.prev_button.config(state='disabled' if not self.entries else 'normal')
            self.next_button.config(state='disabled' if not self.entries else 'normal')
            self.update_button.config(state='disabled')
            self.delete_button.config(state='disabled')
            self.submit_button.config(state='normal')
        else:
            # We're viewing an existing entry
            if self.current_entry_index == 0:
                self.prev_button.config(state='disabled')
            else:
                self.prev_button.config(state='normal')

            if self.current_entry_index == len(self.entries) - 1:
                self.next_button.config(state='disabled')
            else:
                self.next_button.config(state='normal')

            self.update_button.config(state='normal')
            self.delete_button.config(state='normal')
            self.submit_button.config(state='disabled')

    def next_entry(self):
        if self.entries and self.current_entry_index is not None:
            if self.current_entry_index < len(self.entries) - 1:
                self.current_entry_index += 1
                self.load_entry(self.entries[self.current_entry_index])
                self.set_navigation_buttons_state()
            else:
                messagebox.showinfo("Information", "This is the last entry.")
        else:
            messagebox.showinfo("Information", "No entries available.")

    def prev_entry(self):
        if self.entries and self.current_entry_index is not None:
            if self.current_entry_index > 0:
                self.current_entry_index -= 1
                self.load_entry(self.entries[self.current_entry_index])
                self.set_navigation_buttons_state()
            else:
                messagebox.showinfo("Information", "This is the first entry.")
        else:
            messagebox.showinfo("Information", "No entries available.")

    def submit_form(self):
        logging.info("Form submission initiated.")
        data = {
            'sr_no': self.sr_no_var.get(),
            'associate_id': self.associate_id_var.get().strip(),
            'date': datetime.date.today().strftime("%Y-%m-%d"),
            'name': self.name_var.get().strip(),
            'mobile': self.mobile_var.get().strip(),
            'height': self.height_var.get().strip(),
            'age': self.age_var.get(),
            'email': self.email_var.get().strip(),
            'adhaar': self.adhaar_var.get().strip(),
            'dob': self.dob_var.get()
        }

        error_messages = self.logic.validate_form(data)

        if error_messages:
            error_text = "\n".join(error_messages)
            messagebox.showerror("Validation Error", error_text)
            logging.warning(f"Form submission failed with errors: {error_text}")
            return

        if self.logic.save_entry(data):
            messagebox.showinfo("Success", "Entry saved successfully.")
            self.reset_form()
        else:
            messagebox.showerror("Database Error", "An error occurred while saving the entry.")

    def update_entry(self):
        if self.current_entry_index is None:
            messagebox.showerror("Error", "No entry selected to update.")
            return

        logging.info("Entry update initiated.")

        data = {
            'sr_no': self.sr_no_var.get(),
            'associate_id': self.associate_id_var.get().strip(),
            'date': self.date_var.get(),
            'name': self.name_var.get().strip(),
            'mobile': self.mobile_var.get().strip(),
            'height': self.height_var.get().strip(),
            'age': self.age_var.get(),
            'email': self.email_var.get().strip(),
            'adhaar': self.adhaar_var.get().strip(),
            'dob': self.dob_var.get()
        }

        error_messages = self.logic.validate_form(data, updating=True)

        if error_messages:
            error_text = "\n".join(error_messages)
            messagebox.showerror("Validation Error", error_text)
            logging.warning(f"Entry update failed with errors: {error_text}")
            return

        if self.logic.update_entry(data):
            messagebox.showinfo("Success", "Entry updated successfully.")
            # Reload entries and refresh
            self.entries = self.logic.get_all_entries()
            # Find the index of the updated entry
            for index, entry in enumerate(self.entries):
                if entry[0] == data['sr_no']:
                    self.current_entry_index = index
                    break
            self.set_navigation_buttons_state()
        else:
            messagebox.showerror("Database Error", "An error occurred while updating the entry.")

    def delete_entry(self):
        if self.current_entry_index is None:
            messagebox.showerror("Error", "No entry selected to delete.")
            return

        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this entry?")
        if not confirm:
            return

        sr_no = self.sr_no_var.get()
        if self.logic.delete_entry(sr_no):
            messagebox.showinfo("Success", "Entry deleted successfully.")
            # Remove the entry from entries list
            del self.entries[self.current_entry_index]
            if self.entries:
                # Adjust current_entry_index
                if self.current_entry_index >= len(self.entries):
                    self.current_entry_index = len(self.entries) - 1
                self.load_entry(self.entries[self.current_entry_index])
            else:
                self.reset_form()
            self.set_navigation_buttons_state()
        else:
            messagebox.showerror("Database Error", "An error occurred while deleting the entry.")

    def add_new_entry(self):
        self.reset_form()
        self.set_navigation_buttons_state()

    def reset_form(self):
        self.sr_no_var.set(self.logic.get_next_sr_no())
        self.date_var.set(datetime.date.today().strftime("%Y-%m-%d"))
        self.associate_id_var.set('')
        self.name_var.set('')
        self.mobile_var.set('')
        self.height_var.set('')
        self.age_var.set(0)
        self.email_var.set('')
        self.adhaar_var.set('')
        self.dob_var.set('')
        self.associate_id_entry.focus_set()
        # Update entries list
        self.entries = self.logic.get_all_entries()
        self.current_entry_index = None  # Since we're in add new entry mode
        self.set_navigation_buttons_state()
        logging.debug("Form reset for next entry.")


if __name__ == "__main__":
    try:
        logic = EntryFormLogic()
        app = EntryFormView(logic)
        app.mainloop()
    except Exception as e:
        logging.critical(f"Unhandled exception: {e}")
    finally:
        logic.close_connection()
        logging.info("Application closed.")
