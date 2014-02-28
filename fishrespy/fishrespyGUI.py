from fishrespy import RawFileParse, MO2Calculate
from displayData import DisplayData
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

class MO2GUI:
    """Class to implement GUI for RawFileParse and MO2Calc classes.
       Implemented in tkinter.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("MO2 Calculator")
        self.root.columnconfigure(0, weight = 1)
        self.root.rowconfigure(0, weight = 1)
        self.root.minsize(300, 425)
        self.root.maxsize(300, 425)

        #Configure Frame
        self.frame = ttk.Frame(self.root, padding = 3)
        self.frame.grid(column = 0, row = 0, sticky = (N,W,S,E))

        #Define variables
        self.file = StringVar()
        self.outfile = StringVar()
        self.volume = DoubleVar()
        self.custom = DoubleVar()
        self.mass = DoubleVar()
        self.time = StringVar()
        self.date = StringVar()
        self.cycle_time = StringVar()

        #initialize widgets
        self.createWidgets()

    def get_file(self):
        file = filedialog.askopenfilename(filetypes = [('Text Files', '*.txt')])
        self.file.set(file)

    def calculate(self):
        file = self.file.get()
        if file == '':
            messagebox.showerror('File Error', 'Incorrect File entry')
            return
        outfile = self.outfile.get()
        start_time = self.time.get()
        st_check = start_time.split(':')
        if start_time[2] != ':' or start_time[5] != ':':
            messagebox.showerror('Time Error', 'Incorrect Start Time format\nRequires HH:MM:SS')
            return
        if int(st_check[0]) > 23 or int(st_check[1]) > 59 or int(st_check[2]) > 59:
            messagebox.showerror('Time Error', 'Incorrect Start Time format\nRequires HH:MM:SS')
            return
        start_date = self.date.get()
        d_check = start_date.split('/')
        if start_date[2] != '/' or start_date[5] != '/':
            messagebox.showerror('Date Error', 'Incorrect Start Date format\nRequires dd/mm/yy')
            return
        if int(d_check[0]) > 31 or int(d_check[1]) > 12 or int(d_check[2]) > 99:
            messagebox.showerror('Date Error', 'Incorrect Start Date format\nRequires dd/mm/yy')
            return
        cycle_time = self.cycle_time.get()
        if ':' not in cycle_time:
            messagebox.showerror('Cycle Error', 'Incorrect separator in Cycle Time\nRequires min:sec')
            return
        cycle_time = cycle_time.split(':')
        cycle_time = (int(cycle_time[0]), int(cycle_time[1]))
        if cycle_time[1] > 59:
            messagebox.showerror('Cycle Error', 'Seconds must be less than 60')
            return
        mass = self.mass.get()
        volume = self.volume.get()

        if volume == 0:
            volume = self.custom.get()

        output = RawFileParse(file, start_time, start_date, cycle_time).get_data()
        res = MO2Calculate(output, mass, volume, cycle_time)

        MO2 = res.get_data()
        self.showData(MO2)

    def showData(self, data):
        self.popup = Toplevel(self.root)
        view = DisplayData(self.popup, data)
        view.createHeader()
        view.createRowLabels()
        view.createCells()

        self.popup.transient(self.root)
        self.popup.grab_set()
        self.root.wait_window(self.popup)

    def createWidgets(self):
        #use for all buttons, disable if non custom button selected
        def custom_enable():
            custom_entry.configure(state = 'enabled')

        def custom_disable():
            custom_entry.configure(state = 'disabled')

        #set font size for radiobuttons
        s = ttk.Style()
        s.configure('TRadiobutton', font = 12)

        file_input_label = ttk.Label(self.frame, text = "File Location", font = 12)
        file_input_label.grid(column = 0, row = 0, sticky = (W,E))
        #display file to load
        file_input_entry = ttk.Entry(self.frame, textvariable = self.file, font = 12)
        file_input_entry.grid(column = 0, row = 1, sticky = (W,E))
        #browse for file
        file_input_button = ttk.Button(self.frame, text = "Browse", command = self.get_file)
        file_input_button.grid(column = 1, row = 1, sticky = W)

        resp_size_label = ttk.Label(self.frame, text = 'Choose respirometer volume', font = 12)
        resp_size_label.grid(column = 0, row = 2, sticky = W)

        #radiobutton to choose respo volume ADD DEFAULT
        five_resp = ttk.Radiobutton(self.frame, text = '5L', variable = self.volume, value = 5, command = custom_disable)
        five_resp.grid(column = 0, row = 3, sticky = W)
        self.volume.set(5) #default value

        ten_resp = ttk.Radiobutton(self.frame, text = '10L', variable = self.volume, value = 10, command = custom_disable)
        ten_resp.grid(column = 0, row = 4, sticky = W)

        thirty_resp = ttk.Radiobutton(self.frame, text = '30L', variable = self.volume, value = 30, command = custom_disable)
        thirty_resp.grid(column = 0, row = 5, sticky = W)

        custom_resp = ttk.Radiobutton(self.frame, text = 'Custom', variable = self.volume, value = 0, command = custom_enable)
        custom_resp.grid(column = 0, row = 6, sticky = W)

        custom_entry = ttk.Entry(self.frame, textvariable = self.custom, font = 12, state = 'disabled')
        custom_entry.grid(column = 0, row = 7, sticky = W)

        #enter fish mass
        mass_label = ttk.Label(self.frame, text = 'Enter fish mass (kg)', font = 12)
        mass_label.grid(column = 0, row = 8, sticky = W)

        mass_entry = ttk.Entry(self.frame, textvariable = self.mass, font = 12)
        mass_entry.grid(column = 0, row = 9, sticky = W)

        #enter start time of first close
        start_label = ttk.Label(self.frame, text = 'Enter start time of first close', font = 12)
        start_label.grid(column = 0, row = 10, sticky = W)

        start_entry = ttk.Entry(self.frame, textvariable = self.time, font = 12)
        start_entry.grid(column = 0, row = 11, sticky = W)
        start_entry.insert(0, 'HH:MM:SS')

        #enter start date
        date_label = ttk.Label(self.frame, text = 'Enter start date', font = 12)
        date_label.grid(column = 0, row = 12, sticky = W)

        date_entry = ttk.Entry(self.frame, textvariable = self.date, font = 12)
        date_entry.grid(column = 0, row = 13, sticky = W)
        date_entry.insert(0, 'dd/mm/yy')

        #enter cycle time in min:sec text
        cycle_time_label = ttk.Label(self.frame, text = 'Enter cycle duration', font = 12)
        cycle_time_label.grid(column = 0, row = 14, sticky = W)

        cycle_time_entry = ttk.Entry(self.frame, textvariable = self.cycle_time, font = 12)
        cycle_time_entry.grid(column = 0, row = 15, sticky = W)
        cycle_time_entry.insert(0, 'min:sec')

        bottom_frame = ttk.Frame(self.root)
        bottom_frame.grid(column = 0, row = 1, sticky = (W,E))
        bottom_frame.columnconfigure(0, weight = 1)

        calc_button = ttk.Button(bottom_frame, text = 'Calculate', command = self.calculate)
        calc_button.grid(column = 0, row = 0)

def main():
    root = Tk()
    MO2 = MO2GUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
