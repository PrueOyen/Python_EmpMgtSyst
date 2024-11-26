import tkinter as tk
from tkinter import messagebox, ttk
import json
from typing import Any, Dict
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
#import calendar
from datetime import datetime
import os
import random
import re
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as pdf_canvas
from tkcalendar import DateEntry


# Constants
DATA_FILE = 'management_data.json'

# Initialize data storage
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as file:
        json.dump({'employees': {}, 'clients': {}, 'tasks': {}}, file)


# Helper functions
def load_data() -> Dict[str, Any]:
    try:
        with open(DATA_FILE, 'r') as my_file:
            return json.load(my_file)
    except FileNotFoundError:
        return {}  # to handle the error


def save_data(data: Dict[str, Any]) -> None:
    try:
        with open(DATA_FILE, 'w') as my_file:
            json.dump(data, my_file)
    except IOError as e:
        print("An error occurred while writing to the file:", e)

def generate_id(prefix, data, length=6):
    existing_ids = set(data.keys())
    while True:
        # Generate a random number with the specified length
        random_number = ''.join([str(random.randint(0, 9)) for _ in range(length)])
        new_id = f"{prefix}{random_number}"
        # Check if the generated ID is unique
        if new_id not in existing_ids:
            return new_id

# Classes
class ManagementApp:
    def __init__(self, master):
        self.master = master
        self.master.title('Prudence Global Cleaning Limited - Employee Management System')

        self.tab_control = ttk.Notebook(master)
        self.employee_tab = ttk.Frame(self.tab_control)
        self.client_tab = ttk.Frame(self.tab_control)
        self.task_tab = ttk.Frame(self.tab_control)
        self.payroll_tab = ttk.Frame(self.tab_control)

        self.tab_control.add(self.employee_tab, text='Employees')
        self.tab_control.add(self.client_tab, text='Clients')
        self.tab_control.add(self.task_tab, text='Tasks')
        self.tab_control.add(self.payroll_tab, text='Payroll')
        self.tab_control.pack(expand=1, fill='both')

        self.setup_employee_tab()
        self.setup_client_tab()
        self.setup_task_tab()
        self.setup_payroll_tab()

        #hhm3
        self.task_manager = None
        self.payroll_manager = None
        self.employee_manager = None
        self.client_manager = None

    def setup_employee_tab(self):
        self.employee_manager = RecordManager(self.employee_tab, 'employees',
                                              fields=['name', 'phone_number', 'position', 'hourly_rate'],
                                              id_prefix='E')

    def setup_client_tab(self):
        self.client_manager = RecordManager(self.client_tab, 'clients',
                                            fields=['name', 'phone_number', 'location'],
                                            id_prefix='C')

    def setup_task_tab(self):
        self.task_manager = TaskManager(self.task_tab, 'tasks',
                                        fields=['task_name', 'employee_id', 'client_id', 'hours_worked'],
                                        id_prefix='T')

    def setup_payroll_tab(self):
        self.payroll_manager = PayrollManager(self.payroll_tab, 'payroll')


class RecordManager:
    def __init__(self, master, category, fields, id_prefix):
        self.master = master
        self.category = category
        self.fields = fields
        self.id_prefix = id_prefix
        self.data = load_data()
        self.selected_id = None
        self.entries = {}
        self.search_var = tk.StringVar()

        # me
        # Initialize all UI-related attributes in __init__
        self.form_frame = None
        self.entries = {}
        self.button_frame = None
        self.list_frame = None
        self.tree = None
        self.search_row = None
        # self.search_var = None

        # Call the unified UI setup
        self.setup_ui()
        self.refresh_list()
        

    '''def setup_ui(self):
        self.setup_form()
        self.setup_buttons()
        self.setup_search()
        self.setup_list()
        '''

    def setup_ui(self):
        # Set up form
        self.form_frame = ttk.LabelFrame(self.master, text=f"{self.category.capitalize()} Form")
        self.form_frame.pack(fill='x', expand=True, padx=10, pady=10)

        self.entries = {}
        for field in self.fields:
            row = ttk.Frame(self.form_frame)
            row.pack(fill='x', padx=5, pady=5)
            label = ttk.Label(row, text=field.capitalize() + ':')
            label.pack(side='left')
            entry = ttk.Entry(row)
            entry.pack(side='right', expand=True, fill='x')
            self.entries[field] = entry

        # Set up buttons
        self.setup_buttons()

        # search functionality under buttons
        self.setup_search()

        # Setting up list/tree view
        self.setup_list()

    def setup_buttons(self):
        self.button_frame = ttk.Frame(self.master)
        self.button_frame.pack(fill='x', expand=True, padx=10, pady=10)

        ttk.Button(self.button_frame, text='Add', command=self.add_record).pack(side='left')
        ttk.Button(self.button_frame, text='Update', command=self.update_record).pack(side='left')
        ttk.Button(self.button_frame, text='Delete', command=self.delete_record).pack(side='left')
        ttk.Button(self.button_frame, text='Clear', command=self.clear_form).pack(side='left')

    def setup_list(self):
        self.list_frame = ttk.LabelFrame(self.master, text=f"{self.category.capitalize()} List")
        self.list_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(self.list_frame, columns=['ID'] + self.fields, show='headings')
        for field in ['ID'] + self.fields:
            self.tree.heading(field, text=field.capitalize(),
                              command=lambda _col=field: self.treeview_sort_column(self.tree, _col, False))
        self.tree.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(self.list_frame, orient='vertical', command=self.tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.tree.config(yscrollcommand=scrollbar.set)
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)


    def setup_search(self):
        # Create and pack the search row after all buttons have been added
        self.search_var = tk.StringVar()
        self.search_row = ttk.Frame(self.master)  # Place search in the master frame, not in form frame
        self.search_row.pack(fill='x', padx=10, pady=10)
        ttk.Label(self.search_row, text='Search:').pack(side='left')
        search_entry = ttk.Entry(self.search_row, textvariable=self.search_var)
        search_entry.pack(side='left', expand=True, fill='x')
        ttk.Button(self.search_row, text='Search', command=self.search_records).pack(side='right')

    def add_record(self):
        # Use the helper to prepare and validate the data
        success, new_data = self._validate_and_prepare_data()
        if not success:
            return

        try:
            new_id = generate_id(self.id_prefix, self.data[self.category])
            self.data[self.category][new_id] = new_data
            save_data(self.data)
            self.refresh_list()
            self.clear_form()
            messagebox.showinfo("Success", "Record added successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add record: {str(e)}")

    def _validate_and_prepare_data(self):
        """
        Helper method to validate fields and prepare data for adding or updating a record.
        Returns a tuple (success: bool, new_data: dict).
        """
        new_data = {field: self.entries[field].get() for field in self.fields}

        # Check if all fields are filled
        if any(v == "" for v in new_data.values()):
            messagebox.showerror('Error', 'All fields must be filled.')
            return False, {}

        # Validate phone number if 'phone_number' is a field
        if 'phone_number' in new_data:
            phone_number = new_data['phone_number']
            # Check if the phone number contains only digits and has 10 digits
            if not re.fullmatch(r"\d{10}", phone_number):
                messagebox.showerror('Error', 'Phone number must contain exactly 10 digits.')
                return False, {}

        # Check for duplicate fields dynamically based on available fields
        for field in self.fields:
            # Check for duplicates only if the field should be unique
            if field == 'name':
                if any(record.get('name', '').lower() == new_data['name'].lower() for record in
                       self.data[self.category].values()):
                    messagebox.showerror('Error', f"A record with the same {field} already exists.")
                    return False, {}
            elif field == 'phone_number':
                if any(record.get('phone_number', '') == new_data['phone_number'] for record in
                       self.data[self.category].values()):
                    messagebox.showerror('Error', 'An item with the same phone number already exists.')
                    return False, {}

        return True, new_data

    def update_record(self):
        if not self.selected_id:
            messagebox.showerror('Error', 'No record selected for update.')
            return

        updated_data = {field: self.entries[field].get() for field in self.fields}
        if any(v == "" for v in updated_data.values()):
            messagebox.showerror('Error', 'All fields must be filled.')
            return

        # Validate phone number
        if 'phone_number' in updated_data and not self.is_valid_phone(updated_data['phone_number']):
            messagebox.showerror('Error', 'Invalid phone number format.')
            return

        try:
            self.data[self.category][self.selected_id] = updated_data
            save_data(self.data)  # Assuming save_data is correctly defined to not require parameters
            self.refresh_list()
            messagebox.showinfo("Success", "Record updated successfully.")  # Inform the user of success
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update Employee/Client: {str(e)}")

    def delete_record(self):
        if not self.selected_id:
            messagebox.showerror('Error', 'No record selected for deletion.')
            return

        try:
            # Deletes the selected record
            del self.data[self.category][self.selected_id]
            save_data(self.data)
            self.refresh_list()
            self.clear_form()
            messagebox.showinfo("Success", "Record deleted successfully.")  # Inform the user of success
        except KeyError:
            messagebox.showerror("Error", "Failed to delete Employee/Client: Record does not exist.")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")

    @staticmethod
    def is_valid_phone(phone):
        # Pattern to match US phone numbers that may include country code
        pattern = re.compile(r"^\+?1?\s?(\([0-9]{3}\)|[0-9]{3})[\s.-]?[0-9]{3}[\s.-]?[0-9]{4}$")
        return pattern.match(phone) is not None

    def treeview_sort_column(self, tv, col, reverse):
        l = [(tv.set(k, col), k) for k in tv.get_children('')]
        l.sort(reverse=reverse)

        # Rearrange items in sorted positions
        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)

        # Reverse sort next time
        tv.heading(col, command=lambda: self.treeview_sort_column(tv, col, not reverse))

    def search_records(self):
        query = self.search_var.get().lower()
        for child in self.tree.get_children():
            if query in self.tree.item(child, 'values')[1].lower():
                self.tree.selection_set(child)
                self.tree.see(child)
                return
        messagebox.showinfo("Search", "No matching record found!")

    def refresh_list(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        for record_id, info in self.data[self.category].items():
            values = [record_id]
            for field in self.fields:
                if field in info:
                    values.append(info[field])
                else:
                    values.append("N/A")  # Provide a default value if the field is missing
            self.tree.insert('', 'end', iid=record_id, values=values)

    def on_tree_select(self, _event):
        selection = self.tree.selection()
        if selection:  # Check if the selection is not empty
            self.selected_id = selection[0]
            selected_record = self.data[self.category][self.selected_id]
            for field in self.fields:
                self.entries[field].delete(0, 'end')
                self.entries[field].insert(0, selected_record[field])
        else:
            self.clear_form()  # Clear the form if nothing is selected


    def clear_form(self):
            for entry in self.entries.values():
                entry.delete(0, 'end')
            self.selected_id = None  # Reset selected record ID if applicable
            # Clear the search field
            self.search_var.set("")  # clear the value in the search entry field


class TaskManager(RecordManager):
    def __init__(self, master, category, fields, id_prefix):
        # Load data before calling the base class
        self.data = load_data()
        self.employees = {emp_id: emp['name'] for emp_id, emp in self.data['employees'].items()}
        self.clients = {client_id: client['name'] for client_id, client in self.data['clients'].items()}
        self.employee_name_to_id = {emp['name']: emp_id for emp_id, emp in self.data['employees'].items()}
        self.client_name_to_id = {client['name']: client_id for client_id, client in self.data['clients'].items()}

        # Add 'date' to fields to track when each task was completed
        fields.append('date')

        # Call the superclass constructor to properly initialize the base class
        super().__init__(master, category, fields, id_prefix)

        # Set up the custom UI for TaskManager
        self.setup_task_ui()

    def setup_task_ui(self):
        # Ensure that any existing widgets are destroyed to avoid duplicates
        if hasattr(self, 'form_frame') and self.form_frame:
            self.form_frame.destroy()

        # Set up the form specific to TaskManager
        self.form_frame = ttk.LabelFrame(self.master, text='Task Form')
        self.form_frame.pack(fill='x', expand=True, padx=10, pady=10)

        # Create entries for each field in the form
        self.entries = {}
        for field in self.fields:
            row = ttk.Frame(self.form_frame)
            row.pack(fill='x', padx=5, pady=5)
            label = ttk.Label(row, text=field.capitalize() + ':')
            label.pack(side='left')

            if field == 'employee_id':
                # Use employee names instead of IDs
                self.entries[field] = ttk.Combobox(row, values=list(self.employees.values()))
            elif field == 'client_id':
                # Use client names instead of IDs
                self.entries[field] = ttk.Combobox(row, values=list(self.clients.values()))
            elif field == 'date':
                # Use DateEntry widget for date input
                self.entries[field] = DateEntry(row, date_pattern='yyyy-mm-dd')
            else:
                # Regular Entry for other fields
                self.entries[field] = ttk.Entry(row)

            self.entries[field].pack(side='right', expand=True, fill='x')

        # Set up buttons and list to avoid duplicate creation
        if hasattr(self, 'button_frame') and self.button_frame:
            self.button_frame.destroy()
        self.setup_buttons()

        if hasattr(self, 'list_frame') and self.list_frame:
            self.list_frame.destroy()
        self.setup_list()

        # Avoid multiple calls to `setup_search()`
        if hasattr(self, 'search_row') and self.search_row:
            self.search_row.destroy()
        self.setup_search()
        self.refresh_list()

    #ends here
    def add_record(self):
        new_data = {field: self.entries[field].get() for field in self.fields}

        # Check if all fields are filled
        if any(v == "" for v in new_data.values()):
            messagebox.showerror('Error', 'All fields must be filled.')
            return

        # Convert employee and client names back to IDs for storage
        if new_data['employee_id'] in self.employee_name_to_id:
            new_data['employee_id'] = self.employee_name_to_id[new_data['employee_id']]
        else:
            messagebox.showerror('Error', 'Invalid employee selected.')
            return

        if new_data['client_id'] in self.client_name_to_id:
            new_data['client_id'] = self.client_name_to_id[new_data['client_id']]
        else:
            messagebox.showerror('Error', 'Invalid client selected.')
            return

        try:
            new_id = generate_id(self.id_prefix, self.data[self.category])
            self.data[self.category][new_id] = new_data
            save_data(self.data)
            self.refresh_list()
            self.clear_form()
            messagebox.showinfo("Success", "Task added successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add Task: {str(e)}")

#end of task and start of payroll

class PayrollManager:
    def __init__(self, master, category):
        self.master = master
        self.category = category
        self.data = load_data()  # Load data from JSON

        # Load employee data for payroll calculations
        self.employees = {emp_id: emp for emp_id, emp in self.data['employees'].items()}

        # Set up UI components
        self.form_frame = None
        self.start_date_entry = None
        self.end_date_entry = None
        self.calculate_button = None
        self.output_frame = None
        self.tree = None
        self.generate_pdf_button = None

        self.setup_ui()

    def setup_ui(self):
        # Label Frame for Payroll Form
        self.form_frame = ttk.LabelFrame(self.master, text='Payroll Calculation')
        self.form_frame.pack(fill='x', expand=True, padx=10, pady=10)

        # Start Date Row
        start_date_row = ttk.Frame(self.form_frame)
        start_date_row.pack(fill='x', padx=5, pady=5)
        ttk.Label(start_date_row, text='Start Date (YYYY-MM-DD):').pack(side='left')
        self.start_date_entry = ttk.Entry(start_date_row)
        self.start_date_entry.pack(side='left', expand=True, fill='x', padx=5)

        # End Date Row
        end_date_row = ttk.Frame(self.form_frame)
        end_date_row.pack(fill='x', padx=5, pady=5)
        ttk.Label(end_date_row, text='End Date (YYYY-MM-DD):').pack(side='left')
        self.end_date_entry = ttk.Entry(end_date_row)
        self.end_date_entry.pack(side='left', expand=True, fill='x', padx=5)

        # Buttons for calculating and generating payroll
        self.calculate_button = ttk.Button(self.master, text='Calculate Payroll', command=self.calculate_payroll)
        self.calculate_button.pack(pady=10)

        self.generate_pdf_button = ttk.Button(self.master, text='Generate Payroll PDF',
                                              command=self.generate_payroll_pdf)
        self.generate_pdf_button.pack(pady=10)

        # Output frame for displaying results like charts and payroll breakdown
        self.output_frame = ttk.Frame(self.master)
        self.output_frame.pack(fill='both', expand=True)

        # Treeview for displaying payroll details on the left side
        self.tree = ttk.Treeview(self.output_frame, columns=['Employee', 'Total Salary'], show='headings')
        self.tree.heading('Employee', text='Employee')
        self.tree.heading('Total Salary', text='Total Salary')
        self.tree.column('Employee', anchor='center', width=150)
        self.tree.column('Total Salary', anchor='center', width=100)
        self.tree.pack(side='left', fill='y', padx=10, pady=10)

    def calculate_payroll(self):
        start_date = self.start_date_entry.get()
        end_date = self.end_date_entry.get()
        if not start_date or not end_date:
            messagebox.showerror('Error', 'Please enter start and end dates.')
            return

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror('Error', 'Dates must be in YYYY-MM-DD format.')
            return

        if start_date > end_date:
            messagebox.showerror('Error', 'Start date must be before end date.')
            return

        # Calculating payroll
        payroll_data = {}
        for task_id, task in self.data['tasks'].items():
            employee_id = task['employee_id']
            task_date = datetime.strptime(task['date'], '%Y-%m-%d')

            if start_date <= task_date <= end_date:
                if employee_id not in payroll_data:
                    payroll_data[employee_id] = 0
                payroll_data[employee_id] += int(task['hours_worked']) * float(
                    self.employees[employee_id]['hourly_rate'])

        # Displaying payroll breakdown in the Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)  # Clearing the tree before updating

        for employee_id, total_salary in payroll_data.items():
            employee_name = self.employees[employee_id]['name']
            self.tree.insert('', 'end', values=(employee_name, f"${total_salary:.2f}"))

        # Displaying results in pie chart
        if payroll_data:
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.pie(
                list(payroll_data.values()),
                labels=[self.employees[emp_id]['name'] for emp_id in payroll_data.keys()],
                autopct='%1.1f%%'
            )
            ax.set_title('Payroll Distribution')

            # Clearing previous canvas if it exists
            for widget in self.output_frame.pack_slaves():
                if isinstance(widget, FigureCanvasTkAgg):
                    widget.get_tk_widget().destroy()

            # Displaying new pie chart
            canvas = FigureCanvasTkAgg(fig, master=self.output_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(side='right', fill='both', expand=True, padx=10, pady=10)
        else:
            messagebox.showinfo("Info", "No tasks found for the specified date range.")

    def display_payroll_summary(self, payroll_data):
        """
        here prudence is displaying the payroll summary in the Treeview.

        Args:
            payroll_data (dict): Dictionary where keys are employee IDs and values are total pay for each employee.
        """
        # Clearing existing entries in the Treeview
        for i in self.tree.get_children():
            self.tree.delete(i)

        # Adding updated payroll summary to the Treeview
        for employee_id, total_pay in payroll_data.items():
            try:
                # I Safely access employee name, handle missing employee case
                employee_name = self.data['employees'][employee_id]['name']
                self.tree.insert('', 'end', values=(employee_name, f"${total_pay:.2f}"))
            except KeyError:
                # Handling case where the employee ID doesn't exist in the data
                print(f"Warning: Employee ID {employee_id} not found in data.")

    def display_payroll_chart(self, payroll_data):
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.pie(list(payroll_data.values()), labels=[self.data['employees'][emp_id]['name'] for emp_id in payroll_data.keys()], autopct='%1.1f%%')
        ax.set_title('Prudence Global Cleaning Ltd Payroll Distribution')
        chart_canvas = FigureCanvasTkAgg(fig, master=self.output_frame)
        chart_canvas.draw()
        chart_canvas.get_tk_widget().pack()

    def generate_payroll_pdf(self):
        # Prompting the user to choose a location to save the PDF
        pdf_filename = 'Payroll_Report.pdf'
        pdf = pdf_canvas.Canvas(pdf_filename, pagesize=letter)
        width, height = letter

        # Add title to the PDF
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(100, height - 50, "Prudence Global Cleaning Limited Payroll Report")

        # Set the font for the rest of the PDF
        pdf.setFont("Helvetica", 12)
        y = height - 100

        start_date = self.start_date_entry.get()
        end_date = self.end_date_entry.get()

        pdf.drawString(100, y, f"Prudence Global Cleaning Limited Payroll Report from {start_date} to {end_date}")
        y -= 30

        payroll_data = {}
        for task_id, task in self.data['tasks'].items():
            employee_id = task['employee_id']
            if employee_id not in payroll_data:
                payroll_data[employee_id] = 0
            payroll_data[employee_id] += int(task['hours_worked']) * float(self.data['employees'][employee_id]['hourly_rate'])

        # Writing employee payroll information to the PDF
        for employee_id, total_pay in payroll_data.items():
            employee_name = self.data['employees'][employee_id]['name']
            pdf.drawString(100, y, f"Employee: {employee_name}, Total Pay: ${total_pay:.2f}")
            y -= 20

            # Checking if I need to start a new page
            if y < 50:
                pdf.showPage()
                y = height - 50

        # Saving my PDF file
        pdf.save()

        # I Notify the user here
        messagebox.showinfo("Success", f"Payroll report generated and saved as {pdf_filename}.")


# Main application setup
if __name__ == '__main__':
    root = tk.Tk()
    app = ManagementApp(root)
    root.mainloop()
